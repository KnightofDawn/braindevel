import numpy as np
import theano
import theano.tensor as T
from braindecode.analysis.heatmap import (relevance_pool,
    create_back_conv_z_b_fn, create_back_conv_w_sqr_fn, create_back_dense_fn,
    create_back_conv_z_plus_fn, relevance_conv_stable_sign, relevance_conv_a_b)
    
def test_conv_w_sqr_theano():
    conv_w_sqr_fun = create_back_conv_w_sqr_fn()
    out_relevances = np.array([[[[1,0,0]]]], dtype=np.float32)
    conv_weights = np.array([[[[1,0]]]],dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_w_sqr_fun(out_relevances, conv_weights)
    assert np.array_equal([[[[ 1.,  0.,  0.,  0.]]]], in_relevances)
    
    out_relevances = np.array([[[[1,0,0]]]], dtype=np.float32)
    conv_weights = np.array([[[[1,1]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_w_sqr_fun(out_relevances, conv_weights)
    assert np.array_equal([[[[ 0.5,  0.5,  0.,  0.]]]], in_relevances)
    
    out_relevances = np.array([[[[1,0,0]]]], dtype=np.float32)
    conv_weights = np.array([[[[1,2]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_w_sqr_fun(out_relevances, conv_weights)
    assert np.allclose([[[[ 0.2,  0.8,  0.,  0.]]]], in_relevances)
    
    out_relevances = np.array([[[[1,0,0]]]], dtype=np.float32)
    conv_weights = np.array([[[[0,0]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_w_sqr_fun(out_relevances, conv_weights)
    assert np.array_equal([[[[ 0.,  0.,  0.,  0.]]]], in_relevances)
    
    # 2 trials
    out_relevances = np.array([[[[1,0,0]]],[[[0,0,1]]]], dtype=np.float32)
    conv_weights = np.array([[[[1,1]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_w_sqr_fun(out_relevances, conv_weights)
    assert np.array_equal([[[[ 0.5,  0.5,  0.,  0.]]],[[[ 0,  0,  0.5,  0.5]]]],
        in_relevances)
    
    
def test_conv_z_plus_theano():
    conv_z_plus_fn = create_back_conv_z_plus_fn()

    out_relevances = np.array([[[[1,0,0]]]]).astype(np.float32)
    conv_weights = np.array([[[[1,2]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_z_plus_fn(out_relevances,
                                   np.ones((1,1,1,4), dtype=np.float32), conv_weights)
    assert np.allclose([[[[ 1/3.0,  2/3.0,  0.,  0.]]]], in_relevances)
    
    # 0-weights lead to equal distribution
    out_relevances = np.array([[[[1,0,0]]]]).astype(np.float32)
    conv_weights = np.array([[[[1,2]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_z_plus_fn(out_relevances, np.zeros((1,1,1,4), dtype=np.float32), conv_weights)
    assert np.array_equal([[[[ 0.5,  0.5,  0.,  0.]]]], in_relevances)
    
    # negative weights ignored
    out_relevances = np.array([[[[1,0,0]]]]).astype(np.float32)
    conv_weights = np.array([[[[1,-2]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_z_plus_fn(out_relevances, np.ones((1,1,1,4), dtype=np.float32), conv_weights)
    assert np.allclose([[[[ 1,0,  0.,  0.]]]], in_relevances)
    in_activations = np.array([[[[1,2,6]]]], dtype=np.float32)
    out_relevances = np.array([[[[3,4]]]], dtype=np.float32)
    weights = np.array([[[[2,3]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_z_plus_fn(out_relevances, in_activations,weights)
    assert np.allclose([[[[3/4.0, 131/44.0, 36/11.0]]]], in_relevances)
    
def test_conv_z_b_theano():
    conv_z_b_fn = create_back_conv_z_b_fn(-2,4)
    out_rel = np.array([[[[3,4]]]], dtype=np.float32)
    in_act = np.array([[[[1,-2,3]]]], dtype=np.float32)
    weights = np.array([[[[-2,3]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_z_b_fn(out_rel,in_act,weights)
    assert np.allclose([[[[3,48/27.0,60/27.0]]]], in_relevances)
    
    out_rel = np.array([[[[3,4],[-2,3]]]], dtype=np.float32)
    in_act = np.array([[[[1,-2,3], [-1,2,-1.5]]]], dtype=np.float32)
    weights = np.array([[[[-2,3]]]], dtype=np.float32)[:,:,::-1,::-1]
    in_relevances = conv_z_b_fn(out_rel,in_act,weights)
    assert np.allclose([[[[3,48/27.0,60/27.0],
                         [-10/11.0, (-12+24)/11.0, 9/11.0]]]], 
                         in_relevances)

def test_conv_stable_sign():
    inputs = T.ftensor4()
    weights = T.ftensor4()
    relevances = T.ftensor4()
    bias = T.fvector()
    in_rel = relevance_conv_stable_sign(inputs, weights, 
        relevances, bias)
    in_rel_fn = theano.function([inputs, weights, relevances, bias], in_rel)
    # without overlap negative/positive (each relevance completely 
    # redistributed to only positive or only negative)
    in_relevance = in_rel_fn(np.array([[[[-1,2,-3]]]], dtype=np.float32), 
               np.array([[[[1,-1]]]], dtype=np.float32)[:,:,::-1,::-1],
               np.array([[[[4,2]]]], dtype=np.float32),
               np.array([0], dtype=np.float32))
    assert np.allclose([[[[-4/3.0, -8/3.0 + 4/5.0, 6/5.0]]]], in_relevance)
    # with overlap negatve/positive
    in_relevance = in_rel_fn(np.array([[[[-1,-2,3]]]], dtype=np.float32), 
               np.array([[[[1,-1]]]], dtype=np.float32)[:,:,::-1,::-1],
               np.array([[[[4,2]]]], dtype=np.float32),
               np.array([0], dtype=np.float32))
    assert np.allclose([[[[-4/3.0, 16/3.0 - 4/5.0, -6/5.0]]]], in_relevance)

    ### with bias
    in_relevance = in_rel_fn(np.array([[[[-1,2,-3]]]], dtype=np.float32), 
               np.array([[[[1,-1]]]], dtype=np.float32)[:,:,::-1,::-1],
               np.array([[[[4,2]]]], dtype=np.float32),
               np.array([2], dtype=np.float32))
    
    assert np.allclose([[[[16/5.0- 4/5.0, 16/5.0 + 6/7.0 -8/5.0, 8/7.0]]]], in_relevance)

    ### with negative bias
    in_relevance = in_rel_fn(np.array([[[[-1,-2,3]]]], dtype=np.float32), 
               np.array([[[[1,-1]]]], dtype=np.float32)[:,:,::-1,::-1],
               np.array([[[[4,2]]]], dtype=np.float32),
               np.array([-2], dtype=np.float32))
    
    assert np.allclose([[[[-8/5.0, 32/5.0 - 4/5.0 - 6/7.0, -8/7.0]]]], in_relevance)

def test_conv_a_b():
    inputs = T.ftensor4()
    weights = T.ftensor4()
    relevances = T.ftensor4()
    bias = T.fvector()
    in_rel = relevance_conv_a_b(inputs, weights, 
        relevances, a=2, b=1, bias=bias)
    in_rel_fn = theano.function([inputs, weights, relevances, bias], 
        in_rel)
    in_relevance = in_rel_fn(np.array([[[[-1,-2,3]]]], dtype=np.float32), 
               np.array([[[[1,-1]]]], dtype=np.float32)[:,:,::-1,::-1],
               np.array([[[[4,2]]]], dtype=np.float32),
               np.array([0], dtype=np.float32))
    assert np.allclose([[[[-4, 2*4 - 4/5.0,-6/5.0]]]], in_relevance)


def test_dense_w_sqr_theano():
    back_dense_fn = create_back_dense_fn('w_sqr')
    assert np.allclose([[ 1.57243109,  4.92130327,  0.50626564]],
                       back_dense_fn(np.array([[2,1,0,3,1]], dtype=np.float32),
                   np.array([[0,1,2,3,4], [9,3,4,-5,1],[0,0,5,-2,2]],
                       dtype=np.float32)))
    
    assert np.allclose([[1.65684497,  4.97152281,  1.37163186]],
                       back_dense_fn(np.array([[2,1,1,3,1]], dtype=np.float32),
                   np.array([[1,1,2,3,4], [9,3,4,-5,1],[1,2,5,-2,2]],
                       dtype=np.float32)))
    
    # only regression test, not handcalculated, result could be false(!)
    assert np.allclose([[ 1.57243109,  4.92130327,  0.50626564],
                        [ 1.66131997,  5.27685881,  1.06182122]],
                       back_dense_fn(np.array([[2,1,0,3,1], [2,1,1,3,1]], dtype=np.float32),
                   np.array([[0,1,2,3,4], [9,3,4,-5,1],[0,0,5,-2,2]],
                       dtype=np.float32)))

def test_dense_z_plus_theano():
    back_dense_fn = create_back_dense_fn('z_plus')
    out_relevances = np.array([[0,2,1]], dtype=np.float32)
    weights = np.array([[1,1,1], [2,2.25,0]], dtype=np.float32)
    in_activations = np.array([[1,4]], dtype=np.float32)
    in_relevances = back_dense_fn(out_relevances,in_activations,weights)
    assert np.allclose([1.2,1.8], in_relevances)
    
    assert np.allclose([ 3.44895196,  3.20214176,  1.3489064 ],
                   back_dense_fn(np.array([[2,1,1,3,1]], dtype=np.float32),
                           np.array([[1,4,3]], dtype=np.float32),
                           np.array([[1,1,2,3,4], [9,3,4,-5,1],[1,2,5,-2,2]],
                               dtype=np.float32))) 
    # different from numpy due to NaNs being replaced by zeros instead of
    # being replaced by 1 / #input units
    assert np.allclose([[ 4.4000001 ,  0.        ,  0.60000002]], 
                       back_dense_fn(np.array([[2,1,0,3,1]], dtype=np.float32),
                           np.array([[1,0,3]], dtype=np.float32),
                           np.array([[0,1,2,3,4], [9,3,4,-5,1],[0,0,5,-2,2]],
                               dtype=np.float32)))
    
    # Only regression test, values are computed by hand,
    # so could be incorrect
    assert np.allclose([[ 3.44895196,  3.202142  ,  1.34890628],
                   [ 4.04285717,  0.        ,  2.95714283]],
        back_dense_fn(np.array([[2,1,1,3,1], [2,1,0,3,1]], dtype=np.float32),
                       np.array([[1,4,3], [1,0,3]], dtype=np.float32),
                       np.array([[1,1,2,3,4], [9,3,4,-5,1],[1,2,5,-2,2]],
                           dtype=np.float32)))

def test_dense_z_b_theano():
    back_dense_fn = create_back_dense_fn('z_b',min_in=-2, max_in=4)
    out_relevances = np.array([[5,4,1]], dtype=np.float32)
    weights = np.array([[1,-2,4], [0,1,2]], dtype=np.float32)
    in_activations = np.array([[3,2]], dtype=np.float32)
    in_relevances = back_dense_fn(out_relevances,in_activations,weights)
    assert np.allclose([5 + 4/3.0 + 5/7.0,8/3.0 + 2/7.0], in_relevances)
    
def test_pool_theano():
    inputs_var = T.ftensor4()
    out_rel_var = T.ftensor4()
    pool_size =(1,2)
    pool_stride = (1,2)
    
    in_relevances_var = relevance_pool(out_rel_var, inputs_var,
        pool_size, pool_stride)
    pool_relevance_fn = theano.function([out_rel_var,inputs_var],
        in_relevances_var)
    
    out_rel = [[[[1,3,2]]]]
    in_act = [[[[1, 4, 3, 0.3, 4, 6]]]]
    in_relevance = pool_relevance_fn(np.array(out_rel, dtype=np.float32), np.array(in_act, dtype=np.float32))
    assert np.allclose(in_relevance, [[[0.2,0.8, 3*3/3.3, 3*0.3/3.3, 0.8,1.2]]])
    
    inputs_var = T.ftensor4()
    out_rel_var = T.ftensor4()
    pool_size =(1,3)
    pool_stride = (1,2)
    
    in_relevances_var = relevance_pool(out_rel_var, inputs_var,
        pool_size, pool_stride)
    pool_relevance_fn = theano.function([out_rel_var,inputs_var],
        in_relevances_var)
    out_rel = [[[[1,4]]]]
    in_act = [[[[1, 2, 6, 4, 5]]]]
    in_relevance = pool_relevance_fn(out_rel, in_act)
    assert np.allclose(in_relevance,
        [[[[1/9.0,2/9.0, 204/90.0, 16/15.0, 20/15.0]]]])
    
    # Regression test, several chans did not work correctly before
    inputs_var = T.ftensor4()
    out_rel_var = T.ftensor4()
    pool_size =(1,2)
    pool_stride = (1,2)
    
    in_relevances_var = relevance_pool(out_rel_var, inputs_var, pool_size, pool_stride)
    pool_relevance_fn = theano.function([out_rel_var,inputs_var], in_relevances_var)
    out_rel = [[[[1,3,2]], [[1,3,2]]]]
    in_act = [[[[1, 4, 3, 0.3, 4, 6]], [[1, 4, 3, 0.3, 4, 7]]]]
    in_relevance = pool_relevance_fn(np.array(out_rel, dtype=np.float32),
                                     np.array(in_act, dtype=np.float32))
    assert np.allclose(in_relevance, [[[[0.2,0.8, 3*3/3.3, 3*0.3/3.3, 0.8,1.2]],
                                     [[0.2,0.8, 3*3/3.3, 3*0.3/3.3, 0.72727275,
                                        1.27272725]]]])
    
    # Two trials and two channels
    inputs_var = T.ftensor4()
    out_rel_var = T.ftensor4()
    pool_size =(1,2)
    pool_stride = (1,2)
    
    in_relevances_var = relevance_pool(out_rel_var, inputs_var, pool_size, pool_stride)
    pool_relevance_fn = theano.function([out_rel_var,inputs_var], in_relevances_var)
    out_rel = [[[[1,3,2]], [[1,3,2]]], [[[-1,-3,-2]], [[-1,-3,-2]]]]
    in_act = [[[[1, 4, 3, 0.3, 4, 6]], [[1, 4, 3, 0.3, 4, 7]]],
             [[[1, 4, 3, 0.3, 4, 6]], [[1, 4, 3, 0.3, 4, 7]]]]
    in_relevance = pool_relevance_fn(np.array(out_rel, dtype=np.float32),
                                     np.array(in_act, dtype=np.float32))
    assert np.allclose(in_relevance, [[[[0.2,0.8, 3*3/3.3, 3*0.3/3.3, 0.8,1.2]],
                                     [[0.2,0.8, 3*3/3.3, 3*0.3/3.3, 0.72727275,
                                        1.27272725]]],
                                     [[[-0.2,-0.8, -3*3/3.3, -3*0.3/3.3, -0.8,-1.2]],
                                     [[-0.2,-0.8, -3*3/3.3, -3*0.3/3.3, -0.72727275,
                                        -1.27272725]]]])
        