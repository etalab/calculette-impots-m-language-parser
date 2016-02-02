#! /usr/bin/env python
# -*- coding: utf-8 -*-


"""
Convert M language source code to AST.
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
script_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(script_name)

script_dir_name = os.path.dirname(os.path.abspath(__file__))
m_grammar_file_path = os.path.join(script_dir_name, '..', 'data', 'm_language.cleanpeg')


# Primary AST make functions


def make_application_declaration(name):
    return {
        'name': name,
        'type': u'application_declaration',
        }


def make_enchaineur_declaration(name, applications):
    return {
        'applications': applications,
        'name': name,
        'type': u'enchaineur_declaration',
        }


def make_variable_declaration(name, type, attributes = None, description = None):
    return {
        'attributes': attributes,
        'name': name,
        'description': description,
        'type': u'variable_declaration',
        'variable_type': type,
        }


# Secondary AST make functions


def make_attribute(name, value):
    return {
        'name': name,
        'value': value,
        'type': u'attribute',
        }


def make_string(value):
    return {
        'type': u'string',
        'value': value,
        }


def make_symbol(name):
    return {
        'name': name,
        'type': u'symbol',
        }


def make_variable_calculee_qualifiers(value):
    return {
        'type': u'variable_calculee_qualifiers',
        'value': value,
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
        if node['type'] == type
        ] or None


def find_one(nodes, type, attribute = None):
    results = find_many_or_none(nodes, type, attribute)
    assert len(results) == 1, (nodes, type, attribute, results)
    return results[0]


def find_one_or_none(nodes, type, attribute = None):
    results = find_many_or_none(nodes, type, attribute)
    return results[0] if results else None


class MLanguageVisitor(PTNodeVisitor):
    def visit__default__(self, node, children):
        if node.rule_name and node.rule_name != 'EOF':
            raise NotImplementedError(node.rule_name)

    def visit_alias(self, node, children):
        return make_attribute(name = u'alias', value = children[0]['name'])

    def visit_application_declaration(self, node, children):
        return make_application_declaration(name = children[0]['name'])

    def visit_attribute(self, node, children):
        return make_attribute(name = children[0]['name'], value = children[1])

    def visit_comment(self, node, children):
        return None

    def visit_enchaineur_declaration(self, node, children):
        return make_enchaineur_declaration(name = children[0]['name'], applications = children[1])

    def visit_float(self, node, children):
        return float(node.value)

    def visit_integer(self, node, children):
        return int(node.value)

    def visit_root(self, node, children):
        return children

    def visit_string(self, node, children):
        return make_string(value = node[1].value)

    def visit_symbol(self, node, children):
        return make_symbol(name = node.value)

    def visit_symbol_enumeration(self, node, children):
        return [
            child['name']
            for child in children
            ]

    def visit_tableau(self, node, children):
        return make_attribute(name = u'tableau', value = children[0])

    def visit_type(self, node, children):
        return make_attribute(name = u'type', value = node[1].value)

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
        return make_variable_declaration(name = name, description = description, type = 'variable_calculee',
            attributes = attributes)

    def visit_variable_calculee_qualifiers(self, node, children):
        attributes = [
            attribute_node.value
            for attribute_node in node
            ]
        return make_variable_calculee_qualifiers(value = attributes)

    def visit_variable_const_declaration(self, node, children):
        name = children[0]['name']
        return make_variable_declaration(name = name, type = 'variable_const', attributes = {'value': children[1]})

    def visit_variable_declaration(self, node, children):
        return children[0]

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
    parser = ParserPEG(m_grammar, "root", debug = args.debug)
    log.debug(u'M language clean-PEG grammar was parsed with success.')

    parse_tree = parser.parse(source_code)
    log.debug(u'Source file "{}" was parsed with success.'.format(args.source_file))

    result = visit_parse_tree(parse_tree, MLanguageVisitor(debug = args.debug))

    print json.dumps(result)

    return 0


if __name__ == '__main__':
    sys.exit(main())
