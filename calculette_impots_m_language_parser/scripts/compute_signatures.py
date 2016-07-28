"""
    Computes signatures for constants in the code

    Dictionary from constant to signature
    The signature is a dictionary {value: value, deep_refering_variabless: []}    
"""

import json

with open('../../json/light_ast/formulas_light.json', 'r') as f:
    formulas_light = json.load(f)

with open('../../json/light_ast/constants_light.json', 'r') as f:
    constants_light = json.load(f)

with open('../../json/light_ast/computing_order.json', 'r') as f:
    computing_order = json.load(f)


signatures = {}


def signature_add_refering_variable(base, name, value, variable):
    signature = base.get(name, {'value': value, 'deep_refering_variables': []})
    signature['deep_refering_variables'].append(variable)
    base[name] = signature
    if value != signature['value']:
        raise ValueError('Constant has a new value :' + str(value) + ' it was '+ str(signature['value']))


def make_histogram(base):
    histogram = {}

    for key in base:
        histogram[len(base[key]['deep_refering_variables'])] = histogram.get(len(base[key]['deep_refering_variables']), 0) + 1

    for calling_var in histogram:
        print (str(calling_var) + ' : ' + str(histogram[calling_var]))


def gather_underlying_constants(node, underlying_constants):
    nodetype = node['nodetype']

    if nodetype == 'symbol':
        name = node['name']
        if name in constants_light:
            return set([name])
        if name in formulas_light:
            return underlying_constants[name]
        return set()

    if nodetype == 'float':
        return set()

    if nodetype == 'call':
        return_set = set()
        for child in node['args']:
            return_set = return_set | gather_underlying_constants(child, underlying_constants)
        return return_set

    raise ValueError('Unknown type : %s'%nodetype)


def compute_signatures():
    # Computes all constants used for each variable
    underlying_constants = {}
    for variable in computing_order:
        formula = formulas_light[variable]
        underlying_constants[variable] = gather_underlying_constants(formula, underlying_constants)

    # Computes all variable that call each constant
    constants_to_signature = {}
    for variable in underlying_constants:
        for constant in underlying_constants[variable]:
            signature_add_refering_variable(constants_to_signature, constant, constants_light[constant], variable)

    make_histogram(constants_to_signature)


compute_signatures()