'''
Created on Sep 17, 2012

@author: georgianadinu
'''

import numpy as np
from warnings import warn
from scipy.sparse import issparse
from scipy.sparse import vstack
from scipy.sparse import csr_matrix
from scipy.sparse.sputils import isintlike
from composes.utils.num_utils import is_numeric
from composes.matrix.matrix import Matrix
from composes.utils.matrix_utils import array_to_csr_diagonal
from scipy.sparse import identity

class SparseMatrix(Matrix):
    '''
    classdocs
    '''


    def __init__(self, data, *args, **kwargs):
        '''
        Constructor, creates a SparseMatrix from a numpy matrix-like
        object.
        
        Matrix-like objects (np.ndarray, np.matrix, scipy.sparse.matrix,
         DenseMatrix) are converted into scipy.csr_matrix.
        
        Params:
            data: numpy matrix-like object or Matrix type
            
        Raises:
            TypeError
        '''
        if issparse(data):
            self.mat = data.tocsr()
        elif isinstance(data, np.matrix):
            if data.shape[0] == 0 or data.shape[1] == 0:
                raise ValueError("cannot initialize empty matrix")
            warn("Convert numpy dense array to scipy sparse matrix")
            self.mat = csr_matrix(data)
            
        elif isinstance(data, np.ndarray):
            if len(data) == 0:
                raise ValueError("cannot initialize empty matrix")
            warn("Convert numpy dense array to scipy sparse matrix")
            self.mat = csr_matrix(data)
            
        elif isinstance(data, Matrix):
            warn("Convert DenseMatrix to SparseMatrix")
            self.mat = data.to_sparse_matrix().mat
        else:
            raise TypeError("expected scipy sparse matrix, received %s" 
                            % (type(data)))

     
    def __getitem__(self, key):
         
        def __get_row(row):
            start = self.mat.indptr[row]
            end = self.mat.indptr[row + 1]
            return SparseMatrix(csr_matrix((self.mat.data[start:end], 
                                            self.mat.indices[start:end], 
                                            [0, end - start]), 
                                           shape=(1, self.mat.shape[1]),
                                           copy=True))
                     
        if isinstance(key, tuple):
            row = key[0]
            col = key[1]
            if isintlike(row) and isinstance(col, slice):
                if col == slice(None, None, None):
                    return __get_row(row)
        
        if isintlike(key):        
            return __get_row(key)

        result = self.mat[key]
        if is_numeric(result):
            return result
        else:
            return SparseMatrix(result)
    

    @staticmethod
    def identity(size):
        # TODO: should do system-wise
        return SparseMatrix(identity(size, dtype = np.double, format = "csr"))
    
    def multiply(self, matrix_):
        '''
        Component-wise multiplication
        '''
        self._assert_same_type(matrix_)
        return SparseMatrix(self.mat.multiply(matrix_.mat))
        
    def vstack(self, matrix_):
        self._assert_same_type(matrix_)
        return SparseMatrix(vstack([self.mat, matrix_.mat], format = "csr"))
       
    def get_non_negative(self):
        mat_ = self.mat.copy()
        #TODO time against : mat_.data[mat_.data < 0] = 0
        mat_.data = np.where(mat_.data > 0, mat_.data, 0)
        mat_.eliminate_zeros()
        return SparseMatrix(mat_)
            
    def to_non_negative(self):
        self.mat.data = np.where(self.mat.data > 0, self.mat.data, 0)
        self.mat.eliminate_zeros()

    def to_ones(self):
        self.mat.data = np.where(self.mat.data > 0, 1, 0)
        self.mat.eliminate_zeros()
                    
    def assert_positive(self):
        if not np.all(self.mat.data >= 0):
            raise ValueError("expected non-negative matrix")
        
    def is_mostly_positive(self):
        return self.mat.data[self.mat.data > 0].size > self.mat.data.size/2 

    def all_close(self, matrix_):
        diff = self.mat - matrix_.mat
        return np.allclose(diff.data, np.zeros(len(diff.data)))

    def norm(self, axis = None):
        if axis is None:
            return np.linalg.norm(self.mat.data)
        else:
            return np.sqrt(self.multiply(self).sum(axis))
    
    def scale_rows(self, array_):
        
        self._assert_array(array_)
        
        diag_matrix = array_to_csr_diagonal(array_)
        return SparseMatrix(diag_matrix * self.mat)
        
    def scale_columns(self, array_):
        
        self._assert_array(array_)
        
        diag_matrix = array_to_csr_diagonal(array_)
        return SparseMatrix(self.mat * diag_matrix)
        
    def plog(self):
        '''
        Applies positive log to the matrix elements.
        
        Elements smaller than 1 (leading to not defined log or negative log)
        are set to 0. Log is applied on all other elements.
        '''
        
        self.mat.data[self.mat.data <= 1] = 1
        self.mat.data = np.log(self.mat.data)
        self.mat.eliminate_zeros()
            
    def to_dense_matrix(self):
        '''
        Convert to DenseMatrix.
        '''
        from composes.matrix.dense_matrix import DenseMatrix
        return DenseMatrix(self.mat)
    
    def to_sparse_matrix(self, copy = False):
        if (copy):
            return self.copy()
        else:
            return self    
    
    

     
     