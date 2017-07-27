from lasagne.layers.input import InputLayer
from lasagne.layers.shape import DimshuffleLayer
from lasagne.layers.noise import DropoutLayer
from lasagne.layers.conv import Conv2DLayer
from lasagne.nonlinearities import identity, softmax, elu
from braindevel.veganlasagne.layers import Conv2DAllColsLayer,\
    StrideReshapeLayer, FinalReshapeLayer
from braindevel.veganlasagne.batch_norm import BatchNormLayer
from lasagne.layers.pool import Pool2DLayer
from lasagne.layers.special import NonlinearityLayer
import lasagne

class Deep5Net(object):
    def __init__(self, in_chans, input_time_length, 
            num_filters_time, filter_time_length, num_filters_spat,
             pool_time_length, pool_time_stride,
            num_filters_2, filter_length_2, 
            num_filters_3,
            filter_length_3, num_filters_4, filter_length_4,
            final_dense_length, n_classes, final_nonlin=softmax,
            first_nonlin=elu,
            first_pool_mode='max',
            first_pool_nonlin=identity,
            later_nonlin=elu,
            later_pool_mode='max', 
            later_pool_nonlin=identity, 
            drop_in_prob=0.,
            drop_prob=0.5, 
            batch_norm_alpha=0.1,
            double_time_convs=False,
            split_first_layer=True,
            batch_norm=True):
        self.__dict__.update(locals())
        del self.self
        
    def get_layers(self):
        l = InputLayer([None, self.in_chans, self.input_time_length, 1])
        if self.split_first_layer:
            l = DimshuffleLayer(l, pattern=[0,3,2,1])
            l = DropoutLayer(l, p=self.drop_in_prob)
            l = Conv2DLayer(l,
                num_filters=self.num_filters_time,
                filter_size=[self.filter_time_length, 1], 
                nonlinearity=identity,
                name='time_conv')
            if self.double_time_convs:
                l = Conv2DLayer(l,
                    num_filters=self.num_filters_time,
                    filter_size=[self.filter_time_length, 1], 
                    nonlinearity=identity,
                    name='time_conv')
            l = Conv2DAllColsLayer(l, 
                num_filters=self.num_filters_spat,
                filter_size=[1,-1],
                nonlinearity=identity,
                name='spat_conv')
        else: #keep channel dim in first dim, so it will also be convolved over
            l = DropoutLayer(l, p=self.drop_in_prob)
            l = Conv2DLayer(l,
                num_filters=self.num_filters_time,
                filter_size=[self.filter_time_length, 1], 
                nonlinearity=identity,
                name='time_conv')
            if self.double_time_convs:
                l = Conv2DLayer(l,
                    num_filters=self.num_filters_time,
                    filter_size=[self.filter_time_length, 1], 
                    nonlinearity=identity,
                    name='time_conv')
        if self.batch_norm:
            l = BatchNormLayer(l, epsilon=1e-4, alpha=self.batch_norm_alpha,
                nonlinearity=self.first_nonlin)
        else:
            l = NonlinearityLayer(l, nonlinearity=self.first_nonlin)
        l = Pool2DLayer(l, 
            pool_size=[self.pool_time_length,1],
            stride=[1,1],
            mode=self.first_pool_mode)
        l = StrideReshapeLayer(l, n_stride=self.pool_time_stride)
        l = NonlinearityLayer(l, self.first_pool_nonlin)
        
        def conv_pool_block(l, num_filters, filter_length, i_block):
            l = DropoutLayer(l, p=self.drop_prob)
            l = Conv2DLayer(l,
                num_filters=num_filters, 
                filter_size=[filter_length, 1],
                nonlinearity=identity,
                name='combined_conv_{:d}'.format(i_block))
            if self.double_time_convs:
                l = Conv2DLayer(l,
                    num_filters=num_filters, 
                    filter_size=[filter_length, 1],
                    nonlinearity=identity,
                    name='combined_conv_{:d}'.format(i_block))
            if self.batch_norm:
                l = BatchNormLayer(l, epsilon=1e-4, alpha=self.batch_norm_alpha,
                    nonlinearity=self.later_nonlin)
            else:
                l = NonlinearityLayer(l, nonlinearity=self.later_nonlin)
            l = Pool2DLayer(l, 
                pool_size=[self.pool_time_length, 1],
                stride=[1,1],
                mode=self.later_pool_mode)
            l = StrideReshapeLayer(l, n_stride=self.pool_time_stride)
            l = NonlinearityLayer(l, self.later_pool_nonlin)
            return l
        
        l = conv_pool_block(l, self.num_filters_2, self.filter_length_2, 2)
        l = conv_pool_block(l, self.num_filters_3, self.filter_length_3, 3)
        l = conv_pool_block(l, self.num_filters_4, self.filter_length_4, 4)
        # Final part, transformed dense layer
        l = DropoutLayer(l, p=self.drop_prob)
        l = Conv2DLayer(l, num_filters=self.n_classes,
            filter_size=[self.final_dense_length, 1], nonlinearity=identity,
            name='final_dense')
        l = FinalReshapeLayer(l)
        l = NonlinearityLayer(l, self.final_nonlin)
        return lasagne.layers.get_all_layers(l)