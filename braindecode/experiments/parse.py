import itertools
from copy import deepcopy, copy
import yaml 
from string import Template


def transform_vals_to_string_constructor(loader, node):
    return dict([(v[0].value, yaml.serialize(v[1])) for v in node.value])

def create_experiment_yaml_strings(config_str, main_template_str):
    
    yaml.add_constructor(u'!TransformValsToString', transform_vals_to_string_constructor)
    
    config_obj = yaml.load(config_str.replace("templates:", "templates: !TransformValsToString"))
    
    params =  create_variants_recursively(config_obj['variants'])
    # possibly remove equal params?
    templates = config_obj['templates']
    final_params = merge_parameters_and_templates(params, templates)
    
    train_strings = []
    for i_config in range(len(final_params)):
        final_params[i_config]['original_params'] = yaml.dump(params[i_config])
        train_str = Template(main_template_str).substitute(final_params[i_config])
        train_strings.append(train_str)
    return train_strings

def create_variants_recursively(variants):
        """
        Create Variants, variants are like structured like trees of ranges basically...
        >>> variant_dict_list = [[{'batches': [1, 2]}]]
        >>> ExperimentsRunner.create_variants_recursively(variant_dict_list)
        [{'batches': 1}, {'batches': 2}]
        >>> variant_dict_list = [[{'batches': [1, 2], 'algorithm': ['bgd', 'sgd']}]]
        >>> ExperimentsRunner.create_variants_recursively(variant_dict_list)
        [{'batches': 1, 'algorithm': 'bgd'}, {'batches': 1, 'algorithm': 'sgd'}, {'batches': 2, 'algorithm': 'bgd'}, {'batches': 2, 'algorithm': 'sgd'}]
        
        >>> variant_dict_list = [[{'batches': [1,2]}, {'algorithm': ['bgd', 'sgd']}]]
        >>> ExperimentsRunner.create_variants_recursively(variant_dict_list)
        [{'batches': 1}, {'batches': 2}, {'algorithm': 'bgd'}, {'algorithm': 'sgd'}]

        >>> variant_dict_list = [[{'algorithm': ['bgd'], 'variants': [[{'batches': [1, 2]}]]}]]
        >>> ExperimentsRunner.create_variants_recursively(variant_dict_list)
        [{'batches': 1, 'algorithm': 'bgd'}, {'batches': 2, 'algorithm': 'bgd'}]
        
        >>> variant_dict_list = [[{'batches': [1, 2]}], [{'algorithm': ['bgd', 'sgd']}]]
        >>> ExperimentsRunner.create_variants_recursively(variant_dict_list)
        [{'batches': 1, 'algorithm': 'bgd'}, {'batches': 1, 'algorithm': 'sgd'}, {'batches': 2, 'algorithm': 'bgd'}, {'batches': 2, 'algorithm': 'sgd'}]


        """
        list_of_lists_of_all_dicts = []
        for dict_list in variants:
            list_of_lists_of_dicts = []
            for param_dict in dict_list:
                param_dict = deepcopy(param_dict)
                variants = param_dict.pop('variants', None) # pop in case it exists
                param_dicts = cartesian_dict_of_lists_product(param_dict)
                if (variants is not None):
                    list_of_variant_param_dicts =  create_variants_recursively(variants)
                    param_dicts = product_of_lists_of_dicts(param_dicts, list_of_variant_param_dicts)
                list_of_lists_of_dicts.append(param_dicts)
            list_of_dicts =  merge_lists(list_of_lists_of_dicts)
            list_of_lists_of_all_dicts.append(list_of_dicts)
        return product_of_list_of_lists_of_dicts(list_of_lists_of_all_dicts)
        

def cartesian_dict_of_lists_product(params):
    # from stackoverflow somewhere (with different func name) :)
    value_product = [x for x in apply(itertools.product, params.values())]
    return [dict(zip(params.keys(), values)) for values in value_product]

def merge_dicts(a, b):
    return dict(a.items() + b.items())

def merge_lists(list_of_lists):
    return list(itertools.chain(*list_of_lists))

def merge_pairs_of_dicts_in_list(l):
    return [dict(a[0].items() + a[1].items()) for a in l]

def product_of_lists_of_dicts(a, b):
    ''' For two lists of dicts, first compute the product as list of dicts.
    First compute the cartesian product of both lists.
    Then merge the pairs of dicts into one list.
    If one of the lists is empty, return the other list.
    Examples:
    >>> a = [{'color':'red', 'number': 2}, {'color':'blue', 'number': 3}]
    >>> b = [{'name':'Jackie'}, {'name':'Hong'}]
    >>> product = product_of_lists_of_dicts(a,b)
    >>> from pprint import pprint
    >>> pprint(product)
    [{'color': 'red', 'name': 'Jackie', 'number': 2},
     {'color': 'red', 'name': 'Hong', 'number': 2},
     {'color': 'blue', 'name': 'Jackie', 'number': 3},
     {'color': 'blue', 'name': 'Hong', 'number': 3}]
    >>> a = [{'color':'red', 'number': 2}, {'color':'blue', 'number': 3}]
    >>> product_of_lists_of_dicts(a, [])
    [{'color': 'red', 'number': 2}, {'color': 'blue', 'number': 3}]
    >>> product_of_lists_of_dicts([], a)
    [{'color': 'red', 'number': 2}, {'color': 'blue', 'number': 3}]
    >>> product_of_lists_of_dicts([], [])
    []
    '''
    if (len(a) > 0 and len(b) > 0):
        product = itertools.product(a, b)
        merged_product = merge_pairs_of_dicts_in_list(product)
        return merged_product
    else:
        return (a if len(a) > 0 else b)
    
def product_of_list_of_lists_of_dicts(list_of_lists):
    '''
    >>> a = [{'color':'red', 'number': 2}, {'color':'blue', 'number': 3}]
    >>> b = [{'name':'Jackie'}, {'name':'Hong'}]
    >>> c = [{'hair': 'grey'}]
    >>> d = []
    >>> product = product_of_list_of_lists_of_dicts([a, b, c, d])
    >>> from pprint import pprint
    >>> pprint(product)
    [{'color': 'red', 'hair': 'grey', 'name': 'Jackie', 'number': 2},
     {'color': 'red', 'hair': 'grey', 'name': 'Hong', 'number': 2},
     {'color': 'blue', 'hair': 'grey', 'name': 'Jackie', 'number': 3},
     {'color': 'blue', 'hair': 'grey', 'name': 'Hong', 'number': 3}]
     '''
    return reduce(product_of_lists_of_dicts, list_of_lists)


def merge_parameters_and_templates(all_parameters, templates):
    all_final_params = []
    for param_config in all_parameters:
        processed_templates, params_without_template_params  = process_templates(
            templates, param_config)
        final_params = process_parameters_by_templates(params_without_template_params, processed_templates)
        all_final_params.append(final_params)
    return all_final_params

def process_templates(templates, parameters):
        processed_templates = {}
        # we need templates to replace placeholders in parameters
        # placeholders defined with $
        needed_template_names = filter(
            lambda value: isinstance(value, basestring) and value[0] == '$', 
            parameters.values())
        parameters_without_template_parameters = copy(parameters)
        
        # remove $ at start! :)
        # e.g. ["$rect_lin", "$dropout"] => ["rect_lin", "dropout"]
        needed_template_names = [name[1:] for name in needed_template_names]
        
        # now for any needed template, first substitute any $-placeholders
        # _within_ the template with a value from the parameter.
        # Then replace the parameter itself with the template
        # e.g. parameters .. {layers: "$flat", hidden_neurons: 8,...},
        # template: flat: [...$hidden_neurons...]
        # 1 => template: flat: [...8...]
        # 2 => processed_parameters .. {layers: "[...8...]", hidden_neurons:8, ...}
        #   => parameters_without_template_parameters: .. {layers: "[...8...]",..}
        for template_name in needed_template_names:
            template_string = templates[template_name]
            for param in parameters_without_template_parameters.keys():
                if ('$' + param) in template_string:
                    parameters_without_template_parameters.pop(param)
            template_string = Template(template_string).substitute(parameters)
            processed_templates[template_name] = template_string
        return processed_templates, parameters_without_template_parameters
    

def process_parameters_by_templates(parameters, templates):
    processed_parameters = copy(parameters)
    for key in parameters.keys():
        value = parameters[key]
        if isinstance(value, basestring) and value.startswith('$'):
            value = templates[value[1:]] # [1:] to remove the $ at start
            processed_parameters[key] = value
    return processed_parameters
    