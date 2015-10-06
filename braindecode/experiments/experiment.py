import lasagn
from numpy.random import RandomState
import theano
import theano.tensor as T
from braindecode.veganlasagne.update_modifiers import norm_constraint
from collections import OrderedDict

class Experiment(object):
    def setup(self, final_layer, dataset_splitter, loss_var_func,
            updates_var_func, batch_iter_func, monitors,
            target_var=None):
        lasagne.random.set_rng(RandomState(9859295))
        self.final_layer = final_layer
        self.dataset_splitter = dataset_splitter
        self.batch_iter_func = batch_iter_func
        self.monitors = monitors
        self.create_theano_functions(final_layer, loss_var_func,
            updates_var_func, target_var)

    def create_theano_functions(self, final_layer, loss_var_func,
            updates_var_func, target_var):
        if target_var is None:
            target_var = T.ivector('targets')
        prediction = lasagne.layers.get_output(final_layer)
        loss = loss_var_func(prediction, target_var).mean()

        # create parameter update expressions
        params = lasagne.layers.get_all_params(final_layer, trainable=True)
        updates = updates_var_func(loss, params)
        # put norm constraints on all layer, for now fixed to max kernel norm
        # 2 and max col norm 0.5
        updates = norm_constraint(updates, final_layer)
        input_var = lasagne.layers.get_all_layers(final_layer)[0].input_var
        self.loss_func = theano.function([input_var, target_var], loss)

        self.train_func = theano.function([input_var, target_var], updates=updates)
        self.pred_func = theano.function([input_var], prediction)
        
    def run(self):
        datasets = self.dataset_splitter.split_into_train_valid_test()
        self.create_monitors(datasets)
        train_set = datasets['train']
        self.monitor_epoch(datasets)
        self.print_epoch()
        batch_rng = RandomState(328774)
        for _ in range(10):
            #print self.stop_criterion.should_stop()
            all_batch_inds = self.batch_iter_func(len(train_set.y),
                batch_size=60, rng=batch_rng)
            for batch_inds in all_batch_inds:
                self.train_func(train_set.get_topological_view()[batch_inds], 
                    train_set.y[batch_inds])
            self.monitor_epoch(datasets)
            self.print_epoch()

    def create_monitors(self, datasets):
        self.monitor_chans = OrderedDict()
        self.last_epoch_time = None
        for monitor in self.monitors:
            monitor.setup(self.monitor_chans, datasets)
            
    def monitor_epoch(self, all_datasets):
        for monitor in self.monitors:
            monitor.monitor_epoch(self.monitor_chans, self.pred_func,
                self.loss_func, all_datasets)

    def print_epoch(self):
        # -1 due to doing one monitor at start of training
        i_epoch = len(self.monitor_chans.values()[0]) - 1 
        print("Epoch {:d}".format(i_epoch))
        for chan_name in self.monitor_chans:
            print("{:20s} {:.5f}".format(chan_name,
                self.monitor_chans[chan_name][-1]))
        print("")
