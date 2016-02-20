from pylearn2.datasets.dense_design_matrix import DenseDesignMatrix
from wyrm.processing import select_channels
from braindecode.datasets.sensor_positions import sort_topologically
import numpy as np
import logging
from braindecode.mywyrm.processing import select_marker_classes,\
    get_event_samples_and_classes
from braindecode.datasets import signal_processor
log = logging.getLogger(__name__)

class CntSignalMatrix(DenseDesignMatrix):
    reloadable=False # otherwise have to deal with sensor name issue on reload
    def __init__(self, signal_processor,
        sensor_names='all',
        axes=('b', 'c', 0, 1),
        sort_topological=True):
        # sort sensors topologically to allow networks to exploit topology
        if (sensor_names is not None) and (sensor_names  != 'all') and sort_topological:
            sensor_names = sort_topologically(sensor_names)
        self.__dict__.update(locals())
        del self.self       

    def ensure_is_loaded(self):
        if not hasattr(self, 'X'):
            self.load()

    def load(self):
        self.load_cnt()
        self.load_from_cnt()
    
    def load_from_cnt(self):
        """ This function is split off to allow cleaner to go 
        between loading of cnt, clean markers, and then resume loading"""
        log.info("Preprocess continuous signal...")
        self.signal_processor.preprocess_continuous_signal()
        self.select_sensors()
        self.create_cnt_y()
        self.create_dense_design_matrix()
        self.remove_cnt()

    def load_cnt(self):
        log.info("Load continuous signal...")
        self.signal_processor.load_signal_and_markers()

    def select_sensors(self):
        if (self.sensor_names is not None) and (self.sensor_names is not 'all'):
            self.signal_processor.cnt = select_channels(
                self.signal_processor.cnt, 
                self.sensor_names)
        self.sensor_names = self.signal_processor.cnt.axes[-1]

    def create_cnt_y(self):
        """Create continuous target signal"""
        n_classes = len(self.signal_processor.marker_def)
        assert np.all([len(labels) == 1 for labels in 
            self.signal_processor.marker_def.values()]), (
            "Expect only one label per class, otherwise rewrite...")
        
        classes = sorted([labels[0] for labels in self.signal_processor.marker_def.values()])
        assert classes == range(1,n_classes+1), ("Expect class labels to be "
            "from 1 to n_classes (due to matlab 0-based indexing)")
        # Select relevant markers
        reduced_cnt = select_marker_classes(self.signal_processor.cnt,
            classes)
        
        event_samples_and_classes = get_event_samples_and_classes(reduced_cnt)
        i_samples, labels = zip(*event_samples_and_classes)
        
        
        # Create y "signal", first zero everywhere, in loop assign 
        #  1 to where a trial for the respective class happened
        # (respect segmentation interval for this)
        y = np.zeros((len(self.signal_processor.cnt.data), n_classes),
            dtype=np.int32)
        trial_start_offset = int(self.signal_processor.segment_ival[0] * 
                         self.signal_processor.cnt.fs / 1000.0)
        trial_stop_offset = int(self.signal_processor.segment_ival[1] * 
                                 self.signal_processor.cnt.fs / 1000.0)

        unique_labels = sorted(np.unique(labels))
        assert np.array_equal(unique_labels, range(1, len(unique_labels)+1)), (
            "Expect labels to be from 1 to n_classes...")
        
        for i_trial in xrange(len(labels)):
            i_start_sample = i_samples[i_trial]
            i_class = labels[i_trial]-1 # -1 due to 1-based matlab indexing
            # make sure trial is within bounds
            if ((i_start_sample + trial_start_offset >= 0) and
                (i_start_sample + trial_stop_offset <= len(y))):
                y[i_start_sample+trial_start_offset:i_start_sample+trial_stop_offset, 
                    i_class] = 1
        self.y = y

    def create_dense_design_matrix(self):
        # add empty 01 (from bc01) axes ...
        topo_view = self.signal_processor.cnt.data[:,:,
            np.newaxis,np.newaxis].astype(np.float32)
        topo_view = np.ascontiguousarray(np.copy(topo_view))
        super(CntSignalMatrix, self).__init__(topo_view=topo_view, y=self.y, 
                                              axes=self.axes)

        log.info("Loaded dataset with shape: {:s}".format(
            str(self.get_topological_view().shape)))

    def remove_cnt(self):
        del self.signal_processor.cnt

    def free_memory(self):
        del self.X