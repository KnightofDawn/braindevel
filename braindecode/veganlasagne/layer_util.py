import lasagne
import numpy as np
from braindecode.analysis.kaggle import (transform_to_time_activations,
    transform_to_cnt_activations)

def get_receptive_field_size(layer):
    """Receptive field size of a single output of the given layer.
    
    Parameters
    ----------
    layer: Lasagne layer
        Layer to compute receptive field size of the outputs from.
        
    Returns
    -------
    receptive_field_size:
        How many samples one output has "seen"/is influenced by.
    """

    all_layers = lasagne.layers.get_all_layers(layer)

    in_layer = all_layers[0]


    receptive_field_end = np.arange(in_layer.shape[2])
    for layer in all_layers:
        if hasattr(layer, 'filter_size'):
            receptive_field_end = receptive_field_end[layer.filter_size[0]-1:]
        if hasattr(layer, 'pool_size'):
            receptive_field_end = receptive_field_end[layer.pool_size[0]-1:]
        if hasattr(layer,'stride'):
            receptive_field_end = receptive_field_end[::layer.stride[0]]
        if hasattr(layer,'n_stride'):
            receptive_field_end = receptive_field_end[::layer.n_stride]

    return receptive_field_end[0] + 1

def get_trial_acts(all_outs_per_batch, batch_sizes, n_trials, n_inputs_per_trial,
                   n_trial_len, n_sample_preds):
    """Compute trial activations from activations of a specific layer.
    
    Parameters
    ----------
    all_outs_per_batch: list of 1darray
        All activations of a specific layer for all batches from the iterator.
    batch_sizes: list
        All batch sizes of all batches.
    n_trials: int
    n_inputs_per_trial: int
        How many inputs/rows are used to predict all samples of one trial. 
        Depends on trial length, number of predictions per input window.
    n_trial_len: int
        Number of samples per trial
    n_sample_preds: int
        Number of predictions per input window.
    
    Returns
    --------
    trial_acts: 3darray (final empty dim removed)
        Activations of this layer for all trials.
    
    """
    time_acts = transform_to_time_activations(all_outs_per_batch,batch_sizes)
    trial_batch_acts = np.concatenate(time_acts, axis=0).reshape(n_trials,n_inputs_per_trial,
        time_acts[0].shape[1], time_acts[0].shape[2], 1)
    trial_acts = [transform_to_cnt_activations(t[np.newaxis], n_sample_preds, 
                                                   n_samples = n_trial_len)
                      for t in trial_batch_acts]
    trial_acts = np.array(trial_acts)
    return trial_acts