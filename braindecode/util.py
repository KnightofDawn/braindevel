from lasagne.init import Initializer
import theano

class FuncAndArgs(object):
    """Container for a function and its arguments. 
    Useful in case you want to pass a function and its arguments 
    to another function without creating a new class.
    You can call the new instance either with the apply method or 
    the ()-call operator:
    
    >>> FuncAndArgs(max, 2,3).apply(4)
    4
    >>> FuncAndArgs(max, 2,3)(4)
    4
    >>> FuncAndArgs(sum, [3,4])(8)
    15
    
    """
    def __init__(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    
    def apply(self, *other_args, **other_kwargs):
        all_args = self.args + other_args
        all_kwargs = self.kwargs.copy()
        all_kwargs.update(other_kwargs)
        return self.func(*all_args, **all_kwargs)
        
    def __call__(self, *other_args, **other_kwargs):
        return self.apply(*other_args, **other_kwargs)
    
    
class GetAttr(object):
    """ Hacky class for yaml to return attr of something.
    Uses new to actually return completely different object... """
    def __new__(cls, obj, attr):
        return getattr(obj, attr) 

def add_message_to_exception(exc, additional_message):
    #  give some more info...
    # see http://www.ianbicking.org/blog/2007/09/re-raising-exceptions.html
    args = exc.args
    if not args:
        arg0 = ''
    else:
        arg0 = args[0]
    arg0 += additional_message
    exc.args = (arg0, ) + args[1:]
    
def unzip(list):
    return zip(*list)

def dict_compare(d1, d2):
    """From http://stackoverflow.com/a/18860653/1469195"""
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    added = d1_keys - d2_keys
    removed = d2_keys - d1_keys
    modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    same = set(o for o in intersect_keys if d1[o] == d2[o])
    return added, removed, modified, same

def dict_equal(d1,d2):
    d1_keys = set(d1.keys())
    d2_keys = set(d2.keys())
    intersect_keys = d1_keys.intersection(d2_keys)
    modified = {o : (d1[o], d2[o]) for o in intersect_keys if d1[o] != d2[o]}
    return (intersect_keys == d2_keys and intersect_keys == d1_keys and
        len(modified) == 0)
    
