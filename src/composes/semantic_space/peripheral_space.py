'''
Created on Sep 26, 2012

@author: georgianadinu
'''

from space import Space
from numpy import array
from composes.utils.space_utils import list2dict
from composes.utils.space_utils import assert_dict_match_list
from composes.utils.space_utils import assert_shape_consistent
from composes.utils.space_utils import add_items_to_dict
from composes.semantic_space.operation import FeatureSelectionOperation
from composes.semantic_space.operation import DimensionalityReductionOperation
from composes.utils.space_utils import read_words
from composes.utils.space_utils import read_rows_and_columns
from composes.utils.space_utils import read_sparse_space_data
from composes.utils.space_utils import read_dense_space_data

class PeripheralSpace(Space):
    '''
    classdocs
    '''


    def __init__(self, core_space, matrix_, id2row, row2id=None):
        '''
        Constructor
        '''
        if row2id is None:
            row2id = list2dict(id2row)
        else:
            assert_dict_match_list(row2id, id2row)    
            
        column2id = core_space.column2id
        id2column = core_space.id2column
        
        self._operations = list(core_space.operations)    
        self._row2id = row2id
        self._id2row = id2row
        self._column2id = column2id
        self._id2column = id2column
        
        self._cooccurrence_matrix = self._project_core_operations(matrix_)
        assert_shape_consistent(self.cooccurrence_matrix, self._id2row,
                                 self._id2column, self._row2id, self._column2id)
        
        self._element_shape = (self._cooccurrence_matrix.shape[1],)
        
                
    def _project_core_operations(self, matrix_):
       
        for operation in self._operations:
            if isinstance(operation, DimensionalityReductionOperation):
                self._id2column, self._column2id = [], {}
            
            if isinstance(operation, FeatureSelectionOperation):
                self._id2column = list(array(operation.original_columns)[operation.selected_columns])
                self._column2id = list2dict(self._id2column)
            
            matrix_ = operation.project(matrix_)
        return matrix_
        
         
    def add_rows(self, matrix_, id2row):
        
        try:
            self._row2id = add_items_to_dict(self.row2id, id2row)
        except ValueError:
            raise ValueError("Found duplicate keys when appending rows to\
                            peripheral space.")
        
        if matrix_.mat.shape[0] != len(id2row):
            raise ValueError("Matrix shape inconsistent with no. of rows:%s %s"
                              % (matrix_.mat.shape, len(id2row)))
       
        self._id2row = self.id2row + id2row
        matrix_ = self._project_core_operations(matrix_)

        self._cooccurrence_matrix = self._cooccurrence_matrix.vstack(matrix_)
        assert_shape_consistent(self.cooccurrence_matrix, self.id2row,
                                 self.id2column, self.row2id, self.column2id)        
    
    @classmethod            
    def build(self, core_space, **kwargs):
        # TODO: check arguments
        
        if "data" in kwargs:
            data_file = kwargs["data"]
        else:
            raise ValueError("Space data file needs to be specified")
            
        if "format" in kwargs:
            format_ = kwargs["format"]
            if format_ != "dm" or format != "sm":
                raise ValueError("Unrecognized format: %s" %format_)
        else:
            raise ValueError("Format of input files needs to be specified")
        
        if "rows" in kwargs:
            id2row, row2id = read_words(kwargs["rows"])
        if "cols" in kwargs:
            id2column, column2id = read_words(kwargs["cols"])
        elif format_ == "sp":
            raise ValueError("the list of columns must be specified")
        
        if format_ == "sp":
            if id2row is None or id2column is None:    
                tmp_id2row, tmp_row2id, tmp_id2column, tmp_column2id = read_rows_and_columns(data_file)
            if id2row is None:
                id2row = tmp_id2row
                row2id = tmp_row2id
            mat = read_sparse_space_data(data_file, row2id, column2id)
        else:   
            mat = read_dense_space_data(data_file, row2id)
        
        return PeripheralSpace(core_space, mat)
        
        
        
        