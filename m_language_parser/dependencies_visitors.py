# -*- coding: utf-8 -*-


import logging

from toolz.curried import concat, filter, mapcat, pipe

from .unloop_helpers import iter_unlooped_nodes


log = logging.getLogger(__name__)


# Main visitor


deep_level = 0


def visit_node(node):
    """Main visitor which calls the specific visitors below."""
    global deep_level
    visitor = globals()['visit_' + node['type']]
    log.debug('{}:{}:{}'.format(deep_level, visitor.__name__, node))
    deep_level += 1
    result = list(visitor(node))
    deep_level -= 1
    log.debug('{}:{}: => {}'.format(deep_level, visitor.__name__, result))
    assert deep_level >= 0, deep_level
    return result


# Specific visitors


def visit_boolean_expression(node):
    return mapcat(visit_node, node['operands'])


def visit_comparaison(node):
    return mapcat(visit_node, (node['left_operand'], node['right_operand']))


def visit_dans(node):
    return visit_node(node['expression'])


# def visit_enumeration_values(node):


def visit_float(node):
    return []


def visit_formula(node):
    formula_name = node['name']
    dependencies = set(visit_node(node['expression']))
    return (formula_name, dependencies)


def visit_function_call(node):
    return mapcat(visit_node, node['arguments'])


def visit_integer(node):
    return []


def visit_interval(node):
    return []


def visit_loop_expression(node):
    return mapcat(visit_node, iter_unlooped_nodes(
        loop_variables_nodes=node['loop_variables'],
        node=node['expression'],
        ))


def visit_pour_formula(node):
    return map(visit_node, iter_unlooped_nodes(
        loop_variables_nodes=node['loop_variables'],
        node=node['formula'],
        unloop_keys=['name'],
        ))


def visit_product_expression(node):
    return mapcat(visit_node, node['operands'])


def visit_regle(node):
    return mapcat(
        lambda node: visit_node(node) if node['type'] == 'pour_formula' else [visit_node(node)],
        node['formulas'],
        )


def visit_sum_expression(node):
    return mapcat(visit_node, node['operands'])


def visit_symbol(node):
    return [node['value']]


def visit_ternary_operator(node):
    return pipe([
        visit_node(node['value_if_true']),
        visit_node(node['condition']),
        visit_node(node['value_if_false']) if 'value_if_false' in node else None,
        ],
        filter(None),
        concat,
        )
