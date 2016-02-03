#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Convert M language source code to a JSON AST.
"""


import argparse
import json
import logging
import os
import sys

from arpeggio import PTNodeVisitor, visit_parse_tree
from arpeggio.cleanpeg import ParserPEG


# Globals


args = None
m_parser = None
script_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(script_name)

script_dir_name = os.path.dirname(os.path.abspath(__file__))
m_grammar_file_path = os.path.join(script_dir_name, '..', 'data', 'm_language.cleanpeg')


# Primary AST node makers


def make_application_declaration(name, linecol = None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'application_declaration',
        })


def make_comment(value, linecol = None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'comment',
        })


def make_const_variable_declaration(name, value, linecol = None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'variable_declaration',
        'value': value,
        'variable_type': u'const',
        })


def make_enchaineur_declaration(name, applications, linecol = None):
    return clean({
        'applications': applications,
        'linecol': linecol,
        'name': name,
        'type': u'enchaineur_declaration',
        })


def make_regle_declaration(name, applications, variables, isf, linecol = None):
    return clean({
        'applications': applications,
        'isf': isf,
        'linecol': linecol,
        'name': name,
        'type': u'regle_declaration',
        'variables': variables,
        })


def make_variable_declaration(name, type, attributes = None, description = None, linecol = None):
    return clean({
        'attributes': attributes,
        'description': description,
        'linecol': linecol,
        'name': name,
        'type': u'variable_declaration',
        'variable_type': type,
        })


# Secondary AST node makers


def make_attribute(name, value, linecol = None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'attribute',
        'value': value,
        })


def make_expression(value, linecol = None):
    return clean({
        'linecol': linecol,
        'type': u'expression',
        'value': value,
        })


def make_float(value, linecol = None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'float',
        })


def make_integer(value, linecol = None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'integer',
        })


def make_integer_range(start, stop, linecol = None):
    return clean({
        'linecol': linecol,
        'start': start,
        'stop': stop,
        'type': u'integer_range',
        })


def make_pour_variable_definition(loop_domain, loop_variable, variable_definition, linecol = None):
    return clean({
        'linecol': linecol,
        'loop_domain': loop_domain,
        'loop_variable': loop_variable,
        'type': u'pour_variable_definition',
        'variable_definition': variable_definition,
        })


def make_regle_isf_qualifier(value, linecol = None):
    return clean({
        'linecol': linecol,
        'type': u'regle_isf_qualifier',
        'value': value,
        })


def make_string(value, linecol = None):
    return clean({
        'linecol': linecol,
        'type': u'string',
        'value': value,
        })


def make_symbol(name, linecol = None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'symbol',
        })


def make_symbol_enumeration(value, linecol = None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'symbol_enumeration',
        })


def make_variable_calculee_qualifiers(value, linecol = None):
    return clean({
        'linecol': linecol,
        'type': u'variable_calculee_qualifiers',
        'value': value,
        })


def make_variable_definition(name, expression, linecol = None):
    return clean({
        'expression': expression,
        'linecol': linecol,
        'name': name,
        'type': u'variable_definition',
        })


# AST children helpers


def find_one_or_many(nodes, type):
    results = find_many_or_none(nodes, type)
    assert results is not None and len(results) > 0, (nodes, type, results)
    return results


def find_many_or_none(nodes, type):
    return [
        node
        for node in nodes
        if node['type'] == type
        ] or None


def find_one(nodes, type):
    results = find_many_or_none(nodes, type)
    assert results is not None and len(results) == 1, (nodes, type, results)
    return results[0]


def find_one_or_none(nodes, type):
    results = find_many_or_none(nodes, type)
    return results[0] if results else None


# Dict helpers


def clean(dict_):
    """Allows 0 values but not None, [], {}."""
    return {
        key: value
        for key, value in dict_.iteritems()
        if value is not None or isinstance(value, (list, dict)) and value
        }


# PEG parser visitor


class MLanguageVisitor(PTNodeVisitor):
    def visit__default__(self, node, children):
        """Ensure all grammar rules are implemented in visitor class."""
        if node.rule_name and node.rule_name != 'EOF':
            infos = {'rule': node.rule_name, 'node': node, 'children': children}
            raise NotImplementedError(infos)

    def visit_alias(self, node, children):
        value = find_one(children, type = 'symbol')
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = u'alias',
            value = value,
            )

    def visit_application_declaration(self, node, children):
        name = find_one(children, type = 'symbol')
        return make_application_declaration(
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            )

    def visit_attribute(self, node, children):
        name = find_one(children, type = 'symbol')
        value = find_one(children, type = 'integer')
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            value = value,
            )

    def visit_comment(self, node, children):
        return make_comment(
            linecol = m_parser.pos_to_linecol(node.position),
            value = node.value,
            )

    def visit_enchaineur_declaration(self, node, children):
        name = find_one(children, type = 'symbol')
        applications = find_one_or_many(children, type = 'symbol_enumeration')
        return make_enchaineur_declaration(
            applications = applications,
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            )

    def visit_expression(self, node, children):
        return make_expression(
            linecol = m_parser.pos_to_linecol(node.position),
            value = u' '.join(
                line.strip()
                for line in node.value.split('\n')
                ),
            )

    def visit_float(self, node, children):
        return make_float(
            linecol = m_parser.pos_to_linecol(node.position),
            value = float(node.value),
            )

    def visit_integer(self, node, children):
        return make_integer(
            linecol = m_parser.pos_to_linecol(node.position),
            value = int(node.value),
            )

    def visit_integer_range(self, node, children):
        bounds = find_one_or_many(children, type = 'integer')
        assert len(bounds) == 2, bounds
        return make_integer_range(
            linecol = m_parser.pos_to_linecol(node.position),
            start = bounds[0],
            stop = bounds[1],
            )

    def visit_pour_variable_definition(self, node, children):
        loop_variable = find_one(children, type = 'symbol')
        symbols_enumeration = find_one_or_none(children, type = 'symbol_enumeration')
        integer_range = find_one_or_none(children, type = 'integer_range')
        loop_domain = symbols_enumeration or integer_range
        assert loop_domain is not None, (loop_domain, symbols_enumeration, integer_range)
        variable_definition = find_one(children, type = 'variable_definition')
        return make_pour_variable_definition(
            linecol = m_parser.pos_to_linecol(node.position),
            loop_domain = loop_domain,
            loop_variable = loop_variable,
            variable_definition = variable_definition,
            )

    def visit_regle_declaration(self, node, children):
        name = find_one(children, type = 'integer')
        applications = find_one(children, type = 'symbol_enumeration')
        isf_qualifier = find_one_or_none(children, type = 'regle_isf_qualifier')
        variable_definition_list = find_many_or_none(children, type = 'variable_definition')
        pour_variable_definition_list = find_many_or_none(children, type = 'pour_variable_definition')
        variables = ([] + (variable_definition_list or []) + (pour_variable_definition_list or [])) or None
        return make_regle_declaration(
            applications = applications,
            isf = isf_qualifier,
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            variables = variables,
            )

    def visit_regle_isf_qualifier(self, node, children):
        return make_regle_isf_qualifier(
            linecol = m_parser.pos_to_linecol(node.position),
            value = node.value,
            )

    def visit_root(self, node, children):
        # Do not wrap root rule in a sub-key.
        return children

    def visit_string(self, node, children):
        return make_string(
            linecol = m_parser.pos_to_linecol(node.position),
            value = node[1].value,
            )

    def visit_symbol(self, node, children):
        return make_symbol(
            linecol = m_parser.pos_to_linecol(node.position),
            name = node.value,
            )

    def visit_symbol_enumeration(self, node, children):
        return make_symbol_enumeration(
            linecol = m_parser.pos_to_linecol(node.position),
            value = children,
            )

    def visit_symbols_enumeration(self, node, children):
        return make_symbol_enumeration(
            linecol = m_parser.pos_to_linecol(node.position),
            value = children,
            )

    def visit_tableau(self, node, children):
        value = find_one(children, type = 'integer')
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = u'tableau',
            value = value,
            )

    def visit_type(self, node, children):
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = u'type',
            value = node[1].value,
            )

    def visit_variable_calculee_declaration(self, node, children):
        name = find_one(children, type = 'symbol')
        description = find_one(children, type = 'string')
        variable_calculee_qualifiers = find_one_or_none(children, type = 'variable_calculee_qualifiers')
        attributes = None if variable_calculee_qualifiers is None else \
            {'type_qualifiers': variable_calculee_qualifiers}
        return make_variable_declaration(
            attributes = attributes,
            description = description,
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            type = 'calculee',
            )

    def visit_variable_calculee_qualifiers(self, node, children):
        qualifiers = [
            qualifier_node.value
            for qualifier_node in node
            ]
        return make_variable_calculee_qualifiers(
            linecol = m_parser.pos_to_linecol(node.position),
            value = qualifiers,
            )

    def visit_variable_const_declaration(self, node, children):
        name = find_one(children, type = 'symbol')
        value = find_one(children, type = 'float')
        return make_const_variable_declaration(
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            value = value,
            )

    def visit_variable_declaration(self, node, children):
        # Just return sub-rules JSON objects without wrapping them.
        return children[0]

    def visit_variable_definition(self, node, children):
        name = find_one(children, type = 'symbol')
        expression = find_one(children, type = 'expression')
        return make_variable_definition(
            expression = expression,
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            )

    def visit_variable_saisie_declaration(self, node, children):
        name = find_one(children, type = 'symbol')
        description = find_one(children, type = 'string')
        attributes = find_many_or_none(children, type = 'attribute')
        return make_variable_declaration(
            attributes = attributes,
            description = description,
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            type = 'saisie',
            )


def main():
    parser = argparse.ArgumentParser(description = __doc__)
    parser.add_argument('-d', '--debug', action = 'store_true', default = False, help = u'Debug Arpeggio parser')
    parser.add_argument('-v', '--verbose', action = 'store_true', default = False, help = u'Increase output verbosity')
    parser.add_argument('source_file', help = u'Source file to parse')
    global args
    args = parser.parse_args()
    logging.basicConfig(level = logging.DEBUG if args.verbose or args.debug else logging.WARNING, stream = sys.stdout)

    with open(args.source_file) as source_file:
        source_code = source_file.read().decode('utf-8')
    log.debug(u'Source file "{}" was read with success.'.format(args.source_file))

    with open(m_grammar_file_path) as m_grammar_file:
        m_grammar = m_grammar_file.read()
    global m_parser
    m_parser = ParserPEG(m_grammar, 'root', debug = args.debug)
    log.debug(u'M language clean-PEG grammar was parsed with success.')

    parse_tree = m_parser.parse(source_code)
    log.debug(u'Source file "{}" was parsed with success.'.format(args.source_file))

    result = visit_parse_tree(parse_tree, MLanguageVisitor(debug = args.debug))

    print json.dumps(result)

    return 0


if __name__ == '__main__':
    sys.exit(main())
