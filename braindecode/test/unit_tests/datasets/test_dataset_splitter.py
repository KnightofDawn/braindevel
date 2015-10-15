from braindecode.datasets.dataset_splitters import (
    DatasetSingleFoldSplitter, PreprocessedSplitter)
from pylearn2.datasets.dense_design_matrix import DenseDesignMatrix
import numpy as np

def to_4d_array(arr):
    arr = np.array(arr)
    assert arr.ndim == 1
    return arr[:, np.newaxis, np.newaxis, np.newaxis]

def test_last_fold():
    data = np.arange(10)
    dataset = DenseDesignMatrix(topo_view=to_4d_array(data), y=np.zeros(10))
    splitter = DatasetSingleFoldSplitter(dataset, num_folds=10, 
        i_test_fold=9)
    datasets= splitter.split_into_train_valid_test()
    
    assert np.array_equal(to_4d_array(np.arange(8)), 
                   datasets['train'].get_topological_view() )
    assert np.array_equal(to_4d_array([8]),
         datasets['valid'].get_topological_view() )
    assert np.array_equal(to_4d_array([9]), 
                   datasets['test'].get_topological_view() )

def test_first_fold():
    data = np.arange(10)
    dataset = DenseDesignMatrix(topo_view=to_4d_array(data), y=np.zeros(10))
    splitter = DatasetSingleFoldSplitter(dataset, num_folds=10, 
        i_test_fold=0)
    datasets= splitter.split_into_train_valid_test()
    
    assert np.array_equal(to_4d_array(np.arange(1,9)), 
                   datasets['train'].get_topological_view() )
    assert np.array_equal(to_4d_array([9]), 
                   datasets['valid'].get_topological_view() )
    assert np.array_equal(to_4d_array([0]), 
                   datasets['test'].get_topological_view() )

def test_preprocessed_splitter():
    class DemeanPreproc():
        """Just for tests :)"""
        def apply(self, dataset, can_fit=False):
            topo_view = dataset.get_topological_view()
            if can_fit:
                self.mean = np.mean(topo_view)
            dataset.set_topological_view(topo_view - self.mean)


    data = np.arange(10)
    dataset = DenseDesignMatrix(topo_view=to_4d_array(data), y=np.zeros(10))
    splitter = DatasetSingleFoldSplitter(dataset, num_folds=10, i_test_fold=9)
    preproc_splitter = PreprocessedSplitter(dataset_splitter=splitter,
        preprocessor=DemeanPreproc())

    first_round_sets = preproc_splitter.get_train_valid_test()
    
    train_topo = first_round_sets['train'].get_topological_view()
    valid_topo = first_round_sets['valid'].get_topological_view()
    test_topo = first_round_sets['test'].get_topological_view()
    assert np.array_equal(train_topo, 
                          to_4d_array([-3.5, -2.5,-1.5,-0.5,0.5,1.5,2.5,3.5]))
    assert np.array_equal(valid_topo, to_4d_array([4.5]))
    assert np.array_equal(test_topo, to_4d_array([5.5]))
    
    second_round_set = preproc_splitter.get_train_merged_valid_test()
    
    train_topo = second_round_set['train'].get_topological_view()
    valid_topo = second_round_set['valid'].get_topological_view()
    test_topo = second_round_set['test'].get_topological_view()
    assert np.array_equal(train_topo, to_4d_array([-4,-3,-2,-1,0,1,2,3,4]))
    assert np.array_equal(valid_topo, to_4d_array([4]))
    assert np.array_equal(test_topo, to_4d_array([5]))