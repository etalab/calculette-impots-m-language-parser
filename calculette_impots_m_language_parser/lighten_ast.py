"""
Keep only the variables that are useful to compute a set of "root" variables. These variables were selected by a team of experts of the DGFiP.
"""


import collections
import os
import json

import numpy as np

from calculette_impots_m_language_parser import json_dump


# List of variables used to compute taxes (this list was written with M code
# experts during the hackathon  CodeImpot)
roots = ['NBPT', 'REVKIRE', 'BCSG', 'BRDS', 'IBM23', 'TXMOYIMP', 'NAPTIR',
         'IINET', 'RRRBG', 'RNI', 'IDRS3', 'IAVIM']
print('The important variables are : {}'.format(roots))


# Public functions

def lighten_ast(source_dir, target_dir):
    formulas, constants, input_variables, inputs_list = load_data(source_dir)

    # Get deep children (dependancies)
    children_dict = {}
    for name, formula in formulas.items():
        children_dict[name] = get_children(formula)


    unknown_names = find_undefined_names(formulas, constants, inputs_list, children_dict)
    print('Found {} undefined names.'.format(len(unknown_names)))

    parents_dict = get_parents(children_dict)

    useful_formulas, useful_constants, useful_inputs, useful_unknown = get_useful_nodes(roots, formulas, constants, inputs_list, children_dict, unknown_names)

    print('{} formulas are used to compute a useful variable.'.format(len(useful_formulas)))
    print('{} constants are used to compute a useful variable.'.format(len(useful_constants)))
    print('{} inputs are used to compute a useful variable.'.format(len(useful_inputs)))
    print('{} undefined symbols are used to compute a useful variable.'.format(len(useful_unknown)))


    # Ignore useless variables (= not used to compute a useful variables)
    formulas_light = {k: formulas[k] for k in useful_formulas}
    constants_light = {k: constants[k] for k in useful_constants}
    inputs_light = useful_inputs
    unknowns_light = useful_unknown

    children_light = compute_children_light(children_dict, formulas_light)

    computing_order = compute_non_recursive_computing_order(children_light)

    save_data(target_dir, computing_order, children_light, formulas_light, constants_light, inputs_light, unknowns_light)


# Helper functions

def load_data(source_dir):
    with open(os.path.join(source_dir, 'formulas.json'), 'r') as f:
        formulas = json.load(f)
    with open(os.path.join(source_dir, 'constants.json'), 'r') as f:
        constants = json.load(f)
    with open(os.path.join(source_dir, 'input_variables.json'), 'r') as f:
        input_variables = json.load(f)

    inputs_list = []
    for e in input_variables:
        inputs_list.append(e['alias'])
        inputs_list.append(e['name'])

    return formulas, constants, input_variables, inputs_list


def get_children(node):
    nodetype = node['nodetype']

    if nodetype == 'symbol':
        name = node['name']
        return set([name])

    elif nodetype == 'float':
        return set()

    elif nodetype == 'call':
        args = node['args']
        children = set()
        for arg in args:
            children = children | get_children(arg)

        return children

    raise ValueError('Unknown type : %s'%nodetype)


def find_undefined_names(formulas, constants, inputs_list, children_dict):
    unknown_names = set()
    for k, v in children_dict.items():
        for var in v:
            if (var not in formulas) and (var not in constants) and (var not in inputs_list):
                unknown_names.add(var)
    return unknown_names


def get_parents(children_dict):
    parents_dict = {}

    for k in children_dict:
        parents_dict[k] = set()

    for parent, children in children_dict.items():
        for child in children:
            if child in children_dict:
                parents_dict[child].add(parent)

    return parents_dict


def get_useful_nodes(roots, formulas, constants, inputs_list, children_dict, unknown_names):
    # List nodes used somewhere, with a graph traversal

    to_inspect = []
    for root in roots:
        if root in children_dict:
            to_inspect.append(root)
        else:
            print('Warning: root formula {} is not defined.'.format(root))

    useful_formulas = []
    useful_constants = []
    useful_inputs = []
    useful_unknown = []

    while to_inspect:
        node = to_inspect.pop()

        if node in useful_formulas:
            continue

        for child in children_dict[node]:
            if child in formulas:
                if (child not in useful_formulas) and (child not in to_inspect):
                    to_inspect.append(child)
            elif child in constants:
                if child not in useful_constants:
                    useful_constants.append(child)
            elif child in inputs_list:
                if child not in useful_inputs:
                    useful_inputs.append(child)
            elif child in unknown_names:
                if child not in useful_unknown:
                    useful_unknown.append(child)
            else:
                raise Exception('Unknown variable category : %s for parent %s.'%(child, node))

        useful_formulas.append(node)

    return useful_formulas, useful_constants, useful_inputs, useful_unknown


def compute_children_light(children_dict, formulas_light):
    children_light = {}
    for formula in formulas_light:
        children_light[formula] = []
        for child in children_dict[formula]:
            if child in formulas_light:
                children_light[formula].append(child)
    return children_light


def compute_non_recursive_computing_order(children_light):
    def find_order(node):
        is_leaf = True
        for child in children_light[node]:
            if child not in computing_order:
                find_order(child)

        computing_order.append(node)

    computing_order = []
    for root in roots:
        if root in children_light:
            find_order(root)

    return computing_order

def save_data(target_dir, computing_order, children_light, formulas_light, constants_light, inputs_light, unknowns_light):
    with open(os.path.join(target_dir, 'computing_order.json'), 'w') as f:
        f.write(json_dump.dumps(computing_order))

    with open(os.path.join(target_dir, 'children_light.json'), 'w') as f:
        f.write(json_dump.dumps(children_light))

    with open(os.path.join(target_dir, 'formulas_light.json'), 'w') as f:
        f.write(json_dump.dumps(formulas_light))

    with open(os.path.join(target_dir, 'constants_light.json'), 'w') as f:
        f.write(json_dump.dumps(constants_light))

    with open(os.path.join(target_dir, 'inputs_light.json'), 'w') as f:
        f.write(json_dump.dumps(inputs_light))

    with open(os.path.join(target_dir, 'unknowns_light.json'), 'w') as f:
        f.write(json_dump.dumps(unknowns_light))
