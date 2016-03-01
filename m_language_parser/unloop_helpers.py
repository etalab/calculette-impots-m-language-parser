# -*- coding: utf-8 -*-


"""
Unloop helpers are functions which deal with M language loops.
They take a node containing a loop and return as many "unlooped" nodes as the number of combination of loop variables.
"""


import copy
import itertools

from toolz import mapcat


def enumeration_node_to_sequence(enumeration_node):
    if enumeration_node['type'] == 'enumeration_values':
        return enumeration_node['values']
    elif enumeration_node['type'] == 'interval':
        return range(enumeration_node['first'], enumeration_node['last'] + 1)
    else:
        raise NotImplementedError('Unknown type for enumeration_node = {}'.format(enumeration_node))


def iter_unlooped_nodes(node, loop_variables_nodes, unloop_keys=None):
    loop_variables_names, sequences = zip(*map(
        lambda loop_variable_node: (
            loop_variable_node['name'],
            mapcat(
                enumeration_node_to_sequence,
                loop_variable_node['enumerations'],
                ),
            ),
        loop_variables_nodes,
        ))
    loop_variables_values_list = itertools.product(*sequences)
    for loop_variables_values in loop_variables_values_list:
        value_by_loop_variable_name = dict(zip(loop_variables_names, loop_variables_values))
        yield unlooped(
            node=node,
            unloop_keys=unloop_keys,
            value_by_loop_variable_name=value_by_loop_variable_name,
            )


def unlooped(node, value_by_loop_variable_name, unloop_keys=None):
    """
    Replace loop variables names by values given by `value_by_loop_variable_name` in symbols recursively found
    in `node`.
    """
    new_node = copy.deepcopy(node)
    update_symbols(
        node=new_node,
        value_by_loop_variable_name=value_by_loop_variable_name,
        )
    if unloop_keys is not None:
        for key in unloop_keys:
            for loop_variable_name, loop_variable_value in value_by_loop_variable_name.items():
                new_node[key] = new_node[key].replace(loop_variable_name, str(loop_variable_value), 1)
    return new_node


def update_symbols(node, value_by_loop_variable_name):
    """
    This function mutates `node` and returns nothing. Better use the `unlooped` function.
    """
    if isinstance(node, dict):
        if node['type'] == 'symbol':
            for loop_variable_name, loop_variable_value in value_by_loop_variable_name.items():
                node['value'] = node['value'].replace(loop_variable_name, str(loop_variable_value), 1)
        else:
            update_symbols(
                node=list(node.values()),
                value_by_loop_variable_name=value_by_loop_variable_name,
                )
    elif isinstance(node, list):
        for child_node in node:
            update_symbols(
                node=child_node,
                value_by_loop_variable_name=value_by_loop_variable_name,
                )
