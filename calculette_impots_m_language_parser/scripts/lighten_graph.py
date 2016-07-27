import json
import collections
import os
import numpy as np

script_dir = os.path.dirname(os.path.realpath(__file__))
input_dir = script_dir + '/../../json/simplified_ast/'
output_dir = script_dir + '/../../json/light_ast/'

with open(input_dir + 'formulas.json', 'r') as f:
    formulas = json.load(f)
with open(input_dir + 'constants.json', 'r') as f:
    constants = json.load(f)
with open(input_dir + 'input_variables.json', 'r') as f:
    input_variables = json.load(f)

# important variables
roots = ['NBPT', 'REVKIRE', 'BCSG', 'BRDS', 'IBM23', 'TXMOYIMP', 'NAPTIR',
         'IINET', 'RRRBG', 'RNI', 'IDRS3', 'IAVIM']
print('The important variables are : {}'.format(roots))

# Get dependancies

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


children_dict = {}
for name, formula in formulas.items():
    children_dict[name] = get_children(formula)


# Find dependencies without formula

inputs_list = []
for e in input_variables:
    inputs_list.append(e['alias'])
    inputs_list.append(e['name'])

unknown_variables = set()
for k, v in children_dict.items():
    for var in v:
        if (var not in formulas) and (var not in constants) and (var not in inputs_list):
            unknown_variables.add(var)

print('Found {} unknown variables.'.format(len(unknown_variables)))


# Get direct parents

parents_dict = {}

for k in children_dict:
    parents_dict[k] = set()

for parent, children in children_dict.items():
    for child in children:
        if child in children_dict:
            parents_dict[child].add(parent)


# List nodes used somewhere

to_inspect = roots[:]
dependencies_formulas = []
dependencies_constants = []
dependencies_inputs = []
dependencies_unknown = []

while to_inspect:
    node = to_inspect.pop()

    if node in dependencies_formulas:
        continue

    for child in children_dict[node]:
        if child in formulas:
            if (child not in dependencies_formulas) and (child not in to_inspect):
                to_inspect.append(child)
        elif child in constants:
            if child not in dependencies_constants:
                dependencies_constants.append(child)
        elif child in inputs_list:
            if child not in dependencies_inputs:
                dependencies_inputs.append(child)
        elif child in unknown_variables:
            if child not in dependencies_unknown:
                dependencies_unknown.append(child)
        else:
            raise Exception('Unknown variable category : %s for parent %s.'%(child, node))

    dependencies_formulas.append(node)

print('{} formulas are used to compute an important variable.'.format(
    len(dependencies_formulas)))

print('{} constants are used to compute an important variable.'.format(
    len(dependencies_constants)))

print('{} inputs are used to compute an important variable.'.format(
    len(dependencies_inputs)))

print('{} undefined symbols are used to compute an important variable.'.format(
    len(dependencies_unknown)))

# Ignore useless variables (= not used to compute an important variables)

formulas_light = {k: formulas[k] for k in dependencies_formulas}
constants_light = {k: constants[k] for k in dependencies_constants}
inputs_light = dependencies_inputs
unknowns_light = dependencies_unknown


# Compute childrens
children_light = {}
for formula in formulas_light:
    children_light[formula] = []
    for child in children_dict[formula]:
        if child in formulas_light:
            children_light[formula].append(child)


# Compute a non-recursive computing order

def find_order(node):
    is_leaf = True
    for child in children_light[node]:
        if child not in computing_order:
            find_order(child)

    computing_order.append(node)

computing_order = []
for root in roots:
    find_order(root)

# Save everything

with open(output_dir + 'computing_order.json', 'w') as f:
    f.write(json.dumps(computing_order))

with open(output_dir + 'children_light.json', 'w') as f:
    f.write(json.dumps(children_light))

with open(output_dir + 'formulas_light.json', 'w') as f:
    f.write(json.dumps(formulas_light))

with open(output_dir + 'constants_light.json', 'w') as f:
    f.write(json.dumps(constants_light))

with open(output_dir + 'inputs_light.json', 'w') as f:
    f.write(json.dumps(inputs_light))

with open(output_dir + 'unknowns_light.json', 'w') as f:
    f.write(json.dumps(unknowns_light))
