from abc import ABCMeta, abstractmethod
import time
import numpy as np
import theano
from sklearn.metrics import roc_auc_score
from copy import deepcopy

class Monitor(object):
    __metaclass__ = ABCMeta
    @abstractmethod
    def setup(self, monitor_chans, datasets):
        raise NotImplementedError("Subclass needs to implement this")

    @abstractmethod
    def monitor_epoch(self, monitor_chans):
        raise NotImplementedError("Subclass needs to implement this")
    @abstractmethod
    def monitor_set(self, monitor_chans, setname, preds, losses, 
            all_batch_sizes, targets, dataset):
        raise NotImplementedError("Subclass needs to implement this")

class MonitorManager(object):
    def __init__(self, monitors):
        self.monitors = monitors
        
    def create_theano_functions(self, input_var, target_var, predictions_var, 
            loss_var):
        self.pred_loss_func = theano.function([input_var, target_var], 
            [predictions_var, loss_var])
        
    def setup(self, monitor_chans, datasets):
        for monitor in self.monitors:
            monitor.setup(monitor_chans, datasets)
        
    def monitor_epoch(self, monitor_chans, datasets, iterator):
        # first call monitor epoch of all monitors, 
        # then monitor set with losses and preds
        # maybe change this method entirely if it turns out to be too
        # inflexible
        for m in self.monitors:
            m.monitor_epoch(monitor_chans)
        
        for setname in datasets:
            assert setname in ['train', 'valid', 'test']
            dataset = datasets[setname]
            all_preds = []
            all_losses = []
            batch_sizes = []
            targets = []
            for batch in iterator.get_batches(dataset, shuffle=False):
                preds, loss = self.pred_loss_func(batch[0], batch[1])
                all_preds.append(preds)
                all_losses.append(loss)
                batch_sizes.append(len(batch[0]))
                targets.append(batch[1])

            for m in self.monitors:
                m.monitor_set(monitor_chans, setname, all_preds, all_losses,
                    batch_sizes, targets, dataset)

class LossMonitor(Monitor):
    def setup(self, monitor_chans, datasets):
        for setname in datasets:
            assert setname in ['train', 'valid', 'test']
            monitor_key = "{:s}_loss".format(setname)
            monitor_chans[monitor_key] = []

    def monitor_epoch(self, monitor_chans):
        return

    def monitor_set(self, monitor_chans, setname, preds, losses, 
            all_batch_sizes, targets, dataset):
        total_loss = 0.0
        num_trials = 0
        for i_batch in range(len(all_batch_sizes)):
            batch_size = all_batch_sizes[i_batch]
            batch_loss = losses[i_batch]
            # at the end we want the mean over whole dataset
            # so weigh this mean (loss func arleady computes mean for batch)
            # by the size of the batch... this works also if batches
            # not all the same size
            num_trials += batch_size
            total_loss += (batch_loss * batch_size)
            
        mean_loss = total_loss / num_trials
        monitor_key = "{:s}_loss".format(setname)
        monitor_chans[monitor_key].append(float(mean_loss))
        
class MisclassMonitor(Monitor):
    def setup(self, monitor_chans, datasets):
        for setname in datasets:
            assert setname in ['train', 'valid', 'test']
            monitor_key = "{:s}_misclass".format(setname)
            monitor_chans[monitor_key] = []

    def monitor_epoch(self, monitor_chans):
        return

    def monitor_set(self, monitor_chans, setname, all_preds, losses, 
            all_batch_sizes, targets, dataset):
        all_pred_labels = []
        all_target_labels = []
        for i_batch in range(len(all_batch_sizes)):
            preds = all_preds[i_batch]
            pred_labels = np.argmax(preds, axis=1)
            all_pred_labels.extend(pred_labels)
            all_target_labels.extend(targets[i_batch])
        all_pred_labels = np.array(all_pred_labels)
        all_target_labels = np.array(all_target_labels)
        
        # in case of one hot encoding convert back to scalar class numbers
        if all_target_labels.ndim == 2:
            all_target_labels = np.argmax(all_target_labels, axis=1)
        misclass = 1 - (np.sum(all_pred_labels == all_target_labels) / 
            float(len(all_target_labels)))
        monitor_key = "{:s}_misclass".format(setname)
        monitor_chans[monitor_key].append(float(misclass))

class WindowMisclassMonitor(Monitor):
    def setup(self, monitor_chans, datasets):
        for setname in datasets:
            assert setname in ['train', 'valid', 'test']
            monitor_key = "{:s}_misclass".format(setname)
            monitor_chans[monitor_key] = []

    def monitor_epoch(self, monitor_chans):
        return

    def monitor_set(self, monitor_chans, setname, all_batch_preds, losses, 
            all_batch_sizes, targets, dataset):
        all_preds = []
        for i_batch in range(len(all_batch_sizes)):
            batch_preds = all_batch_preds[i_batch]
            all_preds.extend(batch_preds)
        
        n_trials = len(dataset.y)
        preds_by_trial = np.reshape(all_preds, (n_trials, -1 , len(all_preds[0])))
        preds_by_trial = np.sum(preds_by_trial, axis=1)
        pred_labels = np.argmax(preds_by_trial, axis=1)
        accuracy = np.sum(pred_labels == dataset.y) / float(len(dataset.y))
        misclass = 1 - accuracy
        monitor_key = "{:s}_misclass".format(setname)
        monitor_chans[monitor_key].append(float(misclass))

class RuntimeMonitor(Monitor):
    def setup(self, monitor_chans, datasets):
        self.last_call_time = None
        monitor_chans['runtime'] = []

    def monitor_epoch(self, monitor_chans):
        cur_time = time.time()
        if self.last_call_time is None:
            # just in case of first call
            self.last_call_time = cur_time
        monitor_chans['runtime'].append(cur_time - self.last_call_time)
        self.last_call_time = cur_time

    def monitor_set(self, monitor_chans, setname, all_preds, losses, 
            all_batch_sizes, targets, dataset):
        return

class DummyMisclassMonitor(Monitor):
    """ For Profiling tests...."""
    def setup(self, monitor_chans, datasets):
        for setname in datasets:
            assert setname in ['train', 'valid', 'test']
            monitor_key = "{:s}_misclass".format(setname)
            monitor_chans[monitor_key] = []

    def monitor_set(self, monitor_chans, setname, all_preds, losses, 
            all_batch_sizes, targets, dataset):
        misclass = 0.5
        monitor_key = "{:s}_misclass".format(setname)
        monitor_chans[monitor_key].append(float(misclass))

    def monitor_epoch(self, monitor_chans):
        return

def safe_roc_auc_score(y_true, y_score):
    """Returns nan if targets only contain one class"""
    if len(np.unique(y_true)) == 1:
        return np.nan
    else:
        return roc_auc_score(y_true, y_score)
    
def auc_classes_mean(y, preds):
    # nanmean to ignore classes that are not present
    return np.nanmean([safe_roc_auc_score(
            np.int32(y[:,i] == 1), preds[:,i]) 
            for i in range(y.shape[1])])

class AUCMeanMisclassMonitor(Monitor):
    def __init__(self, input_time_length=None, n_sample_preds=None):
        self.input_time_length = input_time_length
        self.n_sample_preds = n_sample_preds
    
    def setup(self, monitor_chans, datasets):
        for setname in datasets:
            assert setname in ['train', 'valid', 'test']
            monitor_key = "{:s}_misclass".format(setname)
            monitor_chans[monitor_key] = []

    def monitor_epoch(self, monitor_chans):
        return

    def monitor_set(self, monitor_chans, setname, all_preds, losses, 
            all_batch_sizes, targets, dataset):
        # remove last preds that were duplicates due to overlap of final windows
        n_samples = len(dataset.y)
        if self.input_time_length is not None:
            all_preds_arr = get_reshaped_cnt_preds(all_preds, n_samples, 
                self.input_time_length, self.n_sample_preds)
        else:
            all_preds_arr = np.concatenate(all_preds)
        
        auc_mean = auc_classes_mean(dataset.y, all_preds_arr)
        misclass = 1 - auc_mean
        monitor_key = "{:s}_misclass".format(setname)
        monitor_chans[monitor_key].append(float(misclass))
        
def get_reshaped_cnt_preds(all_preds, n_samples, input_time_length,
        n_sample_preds):
    """Taking predictions from a multiple prediction/parallel net
    and removing the last predictions (from last batch) which are duplicated.
    """
    all_preds = deepcopy(all_preds)
    # fix the last predictions, they are partly duplications since the last window
    # is made to fit into the timesignal 
    # sample preds
    # might not exactly fit into number of samples)
    legitimate_last_preds = n_samples % n_sample_preds
    if legitimate_last_preds != 0: # in case = 0 there was no overlap, no need to do anything!
        fixed_last_preds = all_preds[-1][-legitimate_last_preds:]
        final_batch_size = all_preds[-1].shape[0] / n_sample_preds
        if final_batch_size > 1:
            # need to take valid sample preds from batches before
            samples_from_legit_batches = n_sample_preds * (final_batch_size - 1)
            fixed_last_preds = np.append(all_preds[-1][:samples_from_legit_batches], 
                 fixed_last_preds, axis=0)
        all_preds[-1] = fixed_last_preds
    
    all_preds_arr = np.concatenate(all_preds)
    
    return all_preds_arr


class CntTrialMisclassMonitor(Monitor):
    def setup(self, monitor_chans, datasets):
        for setname in datasets:
            assert setname in ['train', 'valid', 'test']
            monitor_key = "{:s}_misclass".format(setname)
            monitor_chans[monitor_key] = []

    def monitor_epoch(self, monitor_chans):
        return

    def monitor_set(self, monitor_chans, setname, all_preds, losses, 
            all_batch_sizes, all_targets, dataset):
        """Assuming one hot encoding for now"""
        all_pred_labels = []
        all_target_labels = []
        for i_batch in range(len(all_batch_sizes)):
            trial_preds = all_preds[i_batch]
            trial_pred_label = np.argmax(np.sum(trial_preds, axis=0))
            targets = all_targets[i_batch]
            
            assert np.sum(np.max(targets, axis=0)) == 1, ("Trial should only "
                 "have one class")
            assert np.sum(targets) == len(targets), ("Every sample should have "
                                                    "one positive marker")
            target_label = np.argmax(np.max(targets, axis=0))
            all_pred_labels.append(trial_pred_label)
            all_target_labels.append(target_label)
        all_pred_labels = np.array(all_pred_labels)
        all_target_labels = np.array(all_target_labels)
        
        misclass = 1 - (np.sum(all_pred_labels == all_target_labels) / 
            float(len(all_target_labels)))
        monitor_key = "{:s}_misclass".format(setname)
        monitor_chans[monitor_key].append(float(misclass))