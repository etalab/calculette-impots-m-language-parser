#! /usr/bin/env python
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


# Primary AST make functions


def make_application_declaration(name, linecol = None):
    return {
        'linecol': linecol,
        'name': name,
        'type': u'application_declaration',
        }


def make_enchaineur_declaration(name, applications, linecol = None):
    return {
        'applications': applications,
        'linecol': linecol,
        'name': name,
        'type': u'enchaineur_declaration',
        }


def make_regle_declaration(name, applications, variables, linecol = None):
    return {
        'applications': applications,
        'linecol': linecol,
        'name': name,
        'type': u'regle_declaration',
        'variables': variables,
        }


def make_variable_declaration(name, type, attributes = None, description = None, linecol = None):
    return {
        'attributes': attributes,
        'linecol': linecol,
        'name': name,
        'description': description,
        'type': u'variable_declaration',
        'variable_type': type,
        }


# Secondary AST make functions


def make_attribute(name, value, linecol = None):
    return {
        'linecol': linecol,
        'name': name,
        'type': u'attribute',
        'value': value,
        }


def make_string(value, linecol = None):
    return {
        'linecol': linecol,
        'type': u'string',
        'value': value,
        }


def make_symbol(name, linecol = None):
    return {
        'linecol': linecol,
        'name': name,
        'type': u'symbol',
        }


def make_symbol_enumeration(value, linecol = None):
    return {
        'linecol': linecol,
        'value': value,
        'type': u'symbol_enumeration',
        }


def make_variable_calculee_qualifiers(value, linecol = None):
    return {
        'linecol': linecol,
        'type': u'variable_calculee_qualifiers',
        'value': value,
        }


def make_variable_definition(name, expression, linecol = None):
    return {
        'expression': expression,
        'linecol': linecol,
        'name': name,
        'type': u'variable_definition',
        }


# AST Helpers


def find_many(nodes, type, attribute = None):
    results = find_many_or_none(nodes, type, attribute)
    assert len(results) > 0, (nodes, type, attribute, results)
    return results


def find_many_or_none(nodes, type, attribute = None):
    return [
        node[attribute] if attribute is not None else node
        for node in nodes
        if isinstance(node, dict) and node['type'] == type
        ] or None


def find_one(nodes, type, attribute = None):
    results = find_many_or_none(nodes, type, attribute)
    assert len(results) == 1, (nodes, type, attribute, results)
    return results[0]


def find_one_or_none(nodes, type, attribute = None):
    results = find_many_or_none(nodes, type, attribute)
    return results[0] if results else None


def without_keys(dict, keys):
    return {
        key: value
        for key, value in dict.iteritems()
        if key not in keys
        }


class MLanguageVisitor(PTNodeVisitor):
    def visit__default__(self, node, children):
        if node.rule_name and node.rule_name != 'EOF':
            infos = {'rule': node.rule_name, 'node': node, 'children': children}
            raise NotImplementedError(infos)

    def visit_alias(self, node, children):
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = u'alias',
            value = children[0]['name'],
            )

    def visit_application_declaration(self, node, children):
        return make_application_declaration(
            linecol = m_parser.pos_to_linecol(node.position),
            name = children[0]['name'],
            )

    def visit_attribute(self, node, children):
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = children[0]['name'],
            value = children[1],
            )

    def visit_comment(self, node, children):
        return None

    def visit_enchaineur_declaration(self, node, children):
        return make_enchaineur_declaration(
            applications = children[1]['value'],
            linecol = m_parser.pos_to_linecol(node.position),
            name = children[0]['name'],
            )

    def visit_expression(self, node, children):
        return u' '.join(
            line.strip()
            for line in node.value.split('\n')
            )

    def visit_float(self, node, children):
        return float(node.value)

    def visit_integer(self, node, children):
        return int(node.value)

    def visit_regle_declaration(self, node, children):
        variables = [
            without_keys(variable_definition, ['type'])
            for variable_definition in find_many(children, type = 'variable_definition')
            ]
        return make_regle_declaration(
            applications = children[1]['value'],
            linecol = m_parser.pos_to_linecol(node.position),
            name = children[0],
            variables = variables,
            )

    def visit_root(self, node, children):
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
            value = [
                child['name']
                for child in children
                ],
            )

    def visit_tableau(self, node, children):
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = u'tableau',
            value = children[0],
            )

    def visit_type(self, node, children):
        return make_attribute(
            linecol = m_parser.pos_to_linecol(node.position),
            name = u'type',
            value = node[1].value,
            )

    def visit_variable_calculee_declaration(self, node, children):
        name = children[0]['name']
        description = find_one(children, type = 'string', attribute = 'value')
        variable_calculee_qualifiers = find_one_or_none(
            children,
            attribute = 'value',
            type = 'variable_calculee_qualifiers',
            )
        attributes = None if variable_calculee_qualifiers is None else \
            {'type_qualifiers': variable_calculee_qualifiers}
        return make_variable_declaration(
            attributes = attributes,
            description = description,
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            type = 'variable_calculee',
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
        name = children[0]['name']
        return make_variable_declaration(
            attributes = {'value': children[1]},
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            type = 'variable_const',
            )

    def visit_variable_declaration(self, node, children):
        return children[0]

    def visit_variable_definition(self, node, children):
        return make_variable_definition(
            expression = children[1],
            linecol = m_parser.pos_to_linecol(node.position),
            name = children[0]['name'],
            )

    def visit_variable_saisie_declaration(self, node, children):
        name = children[0]['name']
        description = find_one(children, type = 'string', attribute = 'value')
        attribute_ast_nodes = find_many_or_none(children, type = 'attribute')
        attributes = {
            attribute_ast_node['name']: attribute_ast_node['value']
            for attribute_ast_node in attribute_ast_nodes
            } if attribute_ast_nodes is not None else None
        return make_variable_declaration(
            attributes = attributes,
            description = description,
            linecol = m_parser.pos_to_linecol(node.position),
            name = name,
            type = 'variable_saisie',
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
