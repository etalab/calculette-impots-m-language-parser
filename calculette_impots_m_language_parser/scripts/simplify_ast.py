"""
Simplify hte AST from calculette-impots-m-language-parser to allow only the
following node types :
* symbols
* floats
* function calls

Only the formulas used for application "batch" are processed.
"""


import json
import math
import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
ast_m_dir = config['main']['ast_m_dir']
file_list = os.listdir(ast_m_dir)

formulas = []
constants = []
computed_variables = []
input_variables = []
for filename in file_list:
    with open(ast_m_dir + filename, 'r') as f:
        content = json.load(f)

    for direct_child in content:
        child_type = direct_child['type']
        if child_type == 'verif':
            pass

        elif child_type == 'erreur':
            pass

        elif child_type == 'application':
            pass

        elif child_type == 'enchaineur':
            pass

        elif child_type == 'variable_calculee':
            name = direct_child['name']
            computed_variables.append({'name': name})

        elif child_type == 'variable_saisie':
            name = direct_child['name']
            alias = direct_child['alias']
            input_variables.append({'name': name, 'alias': alias})

        elif child_type == 'variable_const':
            value = float(direct_child['value'])
            name = direct_child['name']
            constants.append({'name': name, 'value': value})

        elif child_type == 'regle':
            if 'batch' in direct_child['applications']:
                formulas += direct_child['formulas']

        else:
            raise ValueError('Unknown child type %s in %s : %s'%(direct_child['type'], filename, str(direct_child)))


def loop_replace(node, old, new):
    nodetype = node['nodetype']

    if nodetype == 'symbol':
        name = node['name']
        try:
            name = name.replace(old, new)
        except TypeError:
            print(node, old, new, type(new))
            raise TypeError()
        return {'nodetype': nodetype, 'name': name}

    if nodetype == 'float':
        return node

    if nodetype == 'call':
        name = node['name']
        args = [loop_replace(child, old, new) for child in node['args']]
        return {'nodetype': nodetype, 'name': name, 'args': args}

    raise ValueError('Unknown type : %s'%nodetype)


def parse_enumeration(enumeration):
    enum_type = enumeration['type']
    if enum_type == 'enumeration_values':
        return enumeration['values']

    if enum_type == 'interval':
        first = int(enumeration['first'])
        last = int(enumeration['last'])
        return [i for i in range(first, last+1)]

    raise ValueError('Unknown enumeration type')


def traversal(node):
    nodetype = node['type']

    if nodetype == 'symbol':
        name = node['value']
        return {'nodetype': 'symbol', 'name': name}

    if nodetype == 'integer':
        value = node['value']
        return {'nodetype': 'float', 'value': float(value)}

    if nodetype == 'float':
        value = node['value']
        return {'nodetype': 'float', 'value': float(value)}

    if nodetype == 'function_call':
        name = node['name']

        if name == 'somme':
            assert(len(node['arguments']) == 1)
            arg = node['arguments'][0]
            assert(arg['type'] == 'loop_expression')
            template = traversal(arg['expression'])
            loop_variables = arg['loop_variables']

            templates = [template]
            for loop_variable in loop_variables:
                assert(loop_variable['type'] == 'loop_variable')
                variable_name = loop_variable['name']
                enumerations = loop_variable['enumerations']
                loop_values = []
                for enumeration in enumerations:
                    loop_values += [str(i) for i in parse_enumeration(enumeration)]
                templates = [loop_replace(template, variable_name, v) for v in loop_values for template in templates]
            args = templates
            return {'nodetype': 'call', 'name': '+', 'args': args}

        args = [traversal(child) for child in node['arguments']]
        return {'nodetype': 'call', 'name': name, 'args': args}

    if nodetype == 'sum_expression':
        args = [traversal(child) for child in node['operands']]
        for i, sign in enumerate(node['operators']):
            if sign == '+':
                pass
            elif sign == '-':
                args[i+1] = {
                    'nodetype': 'call',
                    'name': '-',
                    'args': [args[i+1]]
                }
            else:
                raise ValueError('Unknown sign : %s'%sign)
        return {'nodetype': 'call', 'name': '+', 'args': args}

    if nodetype == 'product_expression':
        args = [traversal(child) for child in node['operands']]
        for i, sign in enumerate(node['operators']):
            if sign == '*':
                pass
            elif sign == '/':
                args[i+1] = {
                    'nodetype': 'call',
                    'name': 'inverse',
                    'args': [args[i+1]]
                }
            else:
                raise ValueError('Unknown sign : %s'%sign)
        return {'nodetype': 'call', 'name': '*', 'args': args}

    if nodetype == 'ternary_operator':
        arg1 = traversal(node['condition'])
        arg2 = traversal(node['value_if_true'])
        if 'value_if_false' in node:
            arg3 = traversal(node['value_if_false'])
            return {'nodetype': 'call', 'name': 'ternary', 'args': [arg1, arg2, arg3]}
        else:
            return {'nodetype': 'call', 'name': 'si', 'args': [arg1, arg2]}

    if nodetype == 'comparaison':
        arg1 = traversal(node['left_operand'])
        arg2 = traversal(node['right_operand'])
        name = 'operator:' + node['operator']
        return {'nodetype': 'call', 'name': name, 'args': [arg1, arg2]}

    if nodetype == 'boolean_expression':
        args = [traversal(child) for child in node['operands']]
        operators = node['operators']

        if len(operators) == 1:
            name = 'boolean:' + operators[0]
            return {'nodetype': 'call', 'name': name, 'args': args}

        args_ou = []
        args_et = []
        operators.append('ou')
        for i, operator in enumerate(operators):
            arg_left = args[i]
            if operator == 'ou':
                if args_et:
                    args_et.append(arg_left)
                    args_ou.append({'nodetype': 'call', 'name': 'boolean:et', 'args': args_et})
                    args_et = []
                else:
                    args_ou.append(arg_left)
            elif operator == 'et':
                args_et.append(arg_left)
            else:
                raise ValueError('Unknown operator %s'%operator)
        return {'nodetype': 'call', 'name': 'boolean:ou', 'args': args_ou}

    if nodetype == 'dans':
        arg1 = traversal(node['expression'])
        enum_values = parse_enumeration(node['enumeration'])
        args = [arg1]
        args += [{'nodetype': 'float', 'value': float(v)} for v in enum_values]
        return {'nodetype': 'call', 'name': 'dans', 'args': args}

    if nodetype == 'unary':
        arg = traversal(node['expression'])
        name = 'unary:' + node['operator']
        return {'nodetype': 'call', 'name': name, 'args':[arg]}

    raise ValueError('Unknown type %s : %s'%(nodetype, node))


formulas_clean = []
for formula in formulas:
    formula_type = formula['type']
    if formula_type == 'formula':
        name = formula['name']
        expression = formula['expression']
        expression_clean = traversal(expression)
        formulas_clean.append({'name': name, 'expression': expression_clean})

    elif formula_type == 'pour_formula':
        template_exp = traversal(formula['formula']['expression'])
        template_name = formula['formula']['name']

        templates_exp = [template_exp]
        templates_name = [template_name]
        loop_variables = formula['loop_variables']
        for loop_variable in loop_variables:
            assert(loop_variable['type'] == 'loop_variable')
            variable_name = loop_variable['name']
            enumerations = loop_variable['enumerations']
            loop_values = []
            for enumeration in enumerations:
                loop_values += [str(i) for i in parse_enumeration(enumeration)]
            templates_exp = [loop_replace(template, variable_name, v) for v in loop_values for template in templates_exp]
            templates_name = [template.replace(variable_name, v) for v in loop_values for template in templates_name]

        for exp, name in zip(templates_exp, templates_name):
            formulas_clean.append({'name': name, 'expression': exp})

    else:
        raise ValueError('Unknown formula type %s'%formula_type)


formulas_dict = {
    formula['name']: formula['expression']
    for formula in formulas_clean
}

constants_dict = {
    constant['name']: constant['value']
    for constant in constants
}

with open('../json/formulas.json', 'w') as f:
    f.write(json.dumps(formulas_dict))
    print('Wrote %d formulas.'%len(formulas_dict))
with open('../json/constants.json', 'w') as f:
    f.write(json.dumps(constants_dict))
    print('Wrote %d constants.'%len(constants_dict))
with open('../json/input_variables.json', 'w') as f:
    f.write(json.dumps(input_variables))
    print('Wrote %d input variables.'%len(input_variables))
