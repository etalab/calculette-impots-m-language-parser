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


def make_application_declaration(name, linecol=None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'application_declaration',
        })


def make_comment(value, linecol=None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'comment',
        })


def make_const_variable_declaration(name, value, linecol=None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'variable_declaration',
        'value': value,
        'variable_type': u'const',
        })


def make_enchaineur_declaration(name, applications, linecol=None):
    return clean({
        'applications': applications,
        'linecol': linecol,
        'name': name,
        'type': u'enchaineur_declaration',
        })


def make_regle_declaration(name, application, variables, enchaineur=None, qualifiers=None, linecol=None):
    return clean({
        'application': application,
        'enchaineur': enchaineur,
        'linecol': linecol,
        'name': name,
        'qualifiers': qualifiers,
        'type': u'regle_declaration',
        'variables': variables,
        })


def make_variable_declaration(name, type, attributes=None, description=None, linecol=None):
    return clean({
        'attributes': attributes,
        'description': description,
        'linecol': linecol,
        'name': name,
        'type': u'variable_declaration',
        'variable_type': type,
        })


# Secondary AST node makers


def make_applications_reference(names, linecol=None):
    return clean({
        'linecol': linecol,
        'names': names,
        'type': u'applications_reference',
        })


def make_attribute(name, value, linecol=None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'attribute',
        'value': value,
        })


def make_brackets(value, linecol=None):
    return clean({
        'linecol': linecol,
        'type': u'brackets',
        'value': value,
        })


def make_float(value, linecol=None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'float',
        })


def make_integer(value, linecol=None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'integer',
        })


def make_integer_range(start, stop, linecol=None):
    return clean({
        'linecol': linecol,
        'start': start,
        'stop': stop,
        'type': u'integer_range',
        })


def make_loop_variable(name, domain, linecol=None):
    return clean({
        'domain': domain,
        'linecol': linecol,
        'name': name,
        'type': u'loop_variable',
        })


def make_loop_variable_domain(value, linecol=None):
    return clean({
        'linecol': linecol,
        'type': u'loop_variable_domain',
        'value': value,
        })


def make_loop_variables(value, linecol=None):
    return clean({
        'linecol': linecol,
        'type': u'loop_variables',
        'value': value,
        })


def make_pour_variable_definition(loop_variables, variable_definition, linecol=None):
    return clean({
        'linecol': linecol,
        'loop_variables': loop_variables,
        'type': u'pour_variable_definition',
        'variable_definition': variable_definition,
        })


def make_regle_enchaineur(name, linecol=None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'regle_enchaineur',
        })


def make_string(value, linecol=None):
    return clean({
        'linecol': linecol,
        'type': u'string',
        'value': value,
        })


def make_symbol(name, linecol=None):
    return clean({
        'linecol': linecol,
        'name': name,
        'type': u'symbol',
        })


def make_symbol_enumeration(value, linecol=None):
    return clean({
        'linecol': linecol,
        'value': value,
        'type': u'symbol_enumeration',
        })


def make_variable_calculee_qualifiers(value, linecol=None):
    return clean({
        'linecol': linecol,
        'type': u'variable_calculee_qualifiers',
        'value': value,
        })


def make_variable_definition(name, expression, brackets=None, linecol=None):
    return clean({
        'brackets': brackets,
        'expression': expression,
        'linecol': linecol,
        'name': name,
        'type': u'variable_definition',
        })


def make_variable_definition_expression(value, linecol=None):
    return clean({
        'linecol': linecol,
        'type': u'variable_definition_expression',
        'value': value,
        })


def make_verif_declaration(name, application, conditions, qualifiers=None, linecol=None):
    return clean({
        'application': application,
        'conditions': conditions,
        'linecol': linecol,
        'name': name,
        'qualifiers': qualifiers,
        'type': u'verif_declaration',
        })


def make_verif_declaration_condition(expression, erreurs, linecol=None):
    return clean({
        'erreurs': erreurs,
        'expression': expression,
        'linecol': linecol,
        'type': u'verif_declaration_condition',
        })


def make_verif_declaration_condition_expression(value, linecol=None):
    return clean({
        'linecol': linecol,
        'type': u'verif_declaration_condition_expression',
        'value': value,
        })


def make_verif_declaration_erreurs(names, linecol=None):
    return clean({
        'linecol': linecol,
        'names': names,
        'type': u'verif_declaration_erreurs',
        })


# AST children helpers


def clean_lines(lines):
    return u' '.join(
        line.strip()
        for line in lines.split('\n')
        )


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
    assert results is None or len(results) == 1, (nodes, type, results)
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
        value = find_one(children, type='symbol')
        return make_attribute(
            linecol=m_parser.pos_to_linecol(node.position),
            name=u'alias',
            value=value,
            )

    def visit_application_declaration(self, node, children):
        name = find_one(children, type='symbol')
        return make_application_declaration(
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            )

    def visit_applications_reference(self, node, children):
        names = find_one_or_many(children, type='symbol_enumeration')
        return make_applications_reference(
            linecol=m_parser.pos_to_linecol(node.position),
            names=names,
            )

    def visit_attribute(self, node, children):
        name = find_one(children, type='symbol')
        value = find_one(children, type='integer')
        return make_attribute(
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            value=value,
            )

    def visit_brackets(self, node, children):
        value = find_one(children, type='symbol')
        return make_brackets(
            linecol=m_parser.pos_to_linecol(node.position),
            value=value,
            )

    def visit_comment(self, node, children):
        return make_comment(
            linecol=m_parser.pos_to_linecol(node.position),
            value=node.value,
            )

    def visit_enchaineur_declaration(self, node, children):
        name = find_one(children, type='symbol')
        applications = find_one(children, type='applications_reference')
        return make_enchaineur_declaration(
            applications=applications,
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            )

    def visit_float(self, node, children):
        return make_float(
            linecol=m_parser.pos_to_linecol(node.position),
            value=float(node.value),
            )

    def visit_integer(self, node, children):
        return make_integer(
            linecol=m_parser.pos_to_linecol(node.position),
            value=int(node.value),
            )

    def visit_integer_range(self, node, children):
        bounds = find_one_or_many(children, type='integer')
        assert len(bounds) == 2, bounds
        return make_integer_range(
            linecol=m_parser.pos_to_linecol(node.position),
            start=bounds[0],
            stop=bounds[1],
            )

    def visit_loop_variable(self, node, children):
        name = find_one(children, type='symbol')
        domain = find_one(children, type='loop_variable_domain')
        return make_loop_variable(
            domain=domain,
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            )

    def visit_loop_variables(self, node, children):
        value = find_one_or_many(children, type='loop_variable')
        return make_loop_variables(
            linecol=m_parser.pos_to_linecol(node.position),
            value=value,
            )

    def visit_loop_variable_domain(self, node, children):
        return make_loop_variable_domain(
            linecol=m_parser.pos_to_linecol(node.position),
            value=children,
            )

    def visit_pour_variable_definition(self, node, children):
        loop_variables = find_one(children, type='loop_variables')
        variable_definition = find_one(children, type='variable_definition')
        return make_pour_variable_definition(
            linecol=m_parser.pos_to_linecol(node.position),
            loop_variables=loop_variables,
            variable_definition=variable_definition,
            )

    def visit_regle_declaration(self, node, children):
        application = find_one(children, type='applications_reference')
        enchaineur = find_one_or_none(children, type='regle_enchaineur')
        symbols = find_one_or_many(children, type='symbol')
        name, qualifiers = symbols[-1], symbols[:-1] or None
        variable_definition_list = find_many_or_none(children, type='variable_definition')
        pour_variable_definition_list = find_many_or_none(children, type='pour_variable_definition')
        variables = ([] + (variable_definition_list or []) + (pour_variable_definition_list or [])) or None
        return make_regle_declaration(
            application=application,
            enchaineur=enchaineur,
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            qualifiers=qualifiers,
            variables=variables,
            )

    def visit_regle_enchaineur(self, node, children):
        name = find_one_or_many(children, type='symbol')
        return make_regle_enchaineur(
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            )

    def visit_root(self, node, children):
        # Do not wrap root rule in a sub-key.
        return children

    def visit_string(self, node, children):
        return make_string(
            linecol=m_parser.pos_to_linecol(node.position),
            value=node[1].value,
            )

    def visit_symbol(self, node, children):
        return make_symbol(
            linecol=m_parser.pos_to_linecol(node.position),
            name=node.value,
            )

    def visit_symbol_enumeration(self, node, children):
        return make_symbol_enumeration(
            linecol=m_parser.pos_to_linecol(node.position),
            value=children,
            )

    def visit_symbol_or_integer_range(self, node, children):
        # Just return sub-rules JSON objects without wrapping them.
        return children[0]

    def visit_tableau(self, node, children):
        value = find_one(children, type='integer')
        return make_attribute(
            linecol=m_parser.pos_to_linecol(node.position),
            name=u'tableau',
            value=value,
            )

    def visit_type(self, node, children):
        return make_attribute(
            linecol=m_parser.pos_to_linecol(node.position),
            name=u'type',
            value=node[1].value,
            )

    def visit_variable_calculee_declaration(self, node, children):
        name = find_one(children, type='symbol')
        description = find_one(children, type='string')
        variable_calculee_qualifiers = find_one_or_none(children, type='variable_calculee_qualifiers')
        attributes = None if variable_calculee_qualifiers is None else \
            {'type_qualifiers': variable_calculee_qualifiers}
        return make_variable_declaration(
            attributes=attributes,
            description=description,
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            type='calculee',
            )

    def visit_variable_calculee_qualifiers(self, node, children):
        qualifiers = [
            qualifier_node.value
            for qualifier_node in node
            ]
        return make_variable_calculee_qualifiers(
            linecol=m_parser.pos_to_linecol(node.position),
            value=qualifiers,
            )

    def visit_variable_const_declaration(self, node, children):
        name = find_one(children, type='symbol')
        value = find_one(children, type='float')
        return make_const_variable_declaration(
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            value=value,
            )

    def visit_variable_declaration(self, node, children):
        # Just return sub-rules JSON objects without wrapping them.
        return children[0]

    def visit_variable_definition(self, node, children):
        name = find_one(children, type='symbol')
        expression = find_one(children, type='variable_definition_expression')
        brackets = find_one_or_none(children, type='brackets')
        return make_variable_definition(
            brackets=brackets,
            expression=expression,
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            )

    def visit_variable_definition_expression(self, node, children):
        value = clean_lines(node.value)
        return make_variable_definition_expression(
            linecol=m_parser.pos_to_linecol(node.position),
            value=value,
            )

    def visit_variable_saisie_declaration(self, node, children):
        name = find_one(children, type='symbol')
        description = find_one(children, type='string')
        attributes = find_many_or_none(children, type='attribute')
        return make_variable_declaration(
            attributes=attributes,
            description=description,
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            type='saisie',
            )

    def visit_verif_declaration(self, node, children):
        symbols = find_one_or_many(children, type='symbol')
        name, qualifiers = symbols[-1], symbols[:-1] or None
        application = find_one(children, type='applications_reference')
        conditions = find_one_or_many(children, type='verif_declaration_condition')
        return make_verif_declaration(
            application=application,
            conditions=conditions,
            linecol=m_parser.pos_to_linecol(node.position),
            name=name,
            qualifiers=qualifiers,
            )

    def visit_verif_declaration_condition(self, node, children):
        erreurs = find_one_or_many(children, type='verif_declaration_erreurs')
        expression = find_one(children, type='verif_declaration_condition_expression')
        return make_verif_declaration_condition(
            erreurs=erreurs,
            expression=expression,
            linecol=m_parser.pos_to_linecol(node.position),
            )

    def visit_verif_declaration_condition_expression(self, node, children):
        value = clean_lines(node.value)
        return make_verif_declaration_condition_expression(
            linecol=m_parser.pos_to_linecol(node.position),
            value=value,
            )

    def visit_verif_declaration_erreurs(self, node, children):
        names = find_one_or_many(children, type='symbol')
        return make_verif_declaration_erreurs(
            linecol=m_parser.pos_to_linecol(node.position),
            names=names,
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--debug', action='store_true', default=False, help=u'Debug Arpeggio parser')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help=u'Increase output verbosity')
    parser.add_argument('source_file', help=u'Source file to parse')
    global args
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose or args.debug else logging.WARNING, stream=sys.stdout)

    with open(args.source_file) as source_file:
        source_code = source_file.read().decode('utf-8')
    log.debug(u'Source file "{}" was read with success.'.format(args.source_file))

    with open(m_grammar_file_path) as m_grammar_file:
        m_grammar = m_grammar_file.read()
    global m_parser
    m_parser = ParserPEG(m_grammar, 'root', debug=args.debug)
    log.debug(u'M language clean-PEG grammar was parsed with success.')

    parse_tree = m_parser.parse(source_code)
    log.debug(u'Source file "{}" was parsed with success.'.format(args.source_file))

    result = visit_parse_tree(parse_tree, MLanguageVisitor(debug=args.debug))

    print json.dumps(result)

    return 0


if __name__ == '__main__':
    sys.exit(main())
