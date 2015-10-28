from braindecode.datasets.pylearn import DenseDesignMatrixWrapper
from braindecode.datahandling.batch_iteration import WindowsIterator
from braindecode.veganlasagne.monitors import WindowMisclassMonitor,\
    MonitorManager
import numpy as np
import theano.tensor as T

def test_flat_sample_window_misclass_monitor():
    inputs = T.ftensor4()
    targets = T.vector()
    
    preds = T.stack((-(T.mean(inputs, axis=(1,2,3)) - 3),
        T.mean(inputs, axis=(1,2,3)) - 3,
        0.0 * T.mean(inputs, axis=(1,2,3)))).T
    loss = T.mean(targets) # some dummy stuff
    # should lead to predictions 0,1,1 which should lead to misclass 1/3.0

    topo_data = [range(i_trial,i_trial+6) for i_trial in range(3)]
    topo_data = np.array(topo_data)[:,np.newaxis,:,np.newaxis]
    
    y = np.int32(range(topo_data.shape[0]))
    dataset = DenseDesignMatrixWrapper(topo_view=topo_data, y=y, 
        axes=('b','c',0,1))
    
    iterator = WindowsIterator(batch_size=7, 
        trial_window_fraction=1/3.0, sample_axes_name=0, stride=1)
    
    monitor = WindowMisclassMonitor()
    monitor_manager = MonitorManager([monitor])
    monitor_manager.create_theano_functions(inputs, targets, preds, loss)
    monitor_chans = {'train_misclass': []}
    monitor_manager.monitor_epoch(monitor_chans, {'train': dataset}, iterator)
    assert np.allclose([1/3.0], monitor_chans['train_misclass'])
