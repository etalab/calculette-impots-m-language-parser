#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
Convert M language source code to a JSON AST.
"""


from __future__ import unicode_literals

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


# Helpers


def clean_lines(lines):
    return ' '.join(
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


def find_many(nodes, type):
    results = find_many_or_none(nodes, type)
    assert results is not None and len(results) > 1, (nodes, type, results)
    return results


def find_one(nodes, type):
    results = find_many_or_none(nodes, type)
    assert results is not None and len(results) == 1, (nodes, type, results)
    return results[0]


def find_one_or_none(nodes, type):
    results = find_many_or_none(nodes, type)
    assert results is None or len(results) == 1, (nodes, type, results)
    return results[0] if results else None


def make_json_ast_node(node, type=None, **kwargs):
    linecol = m_parser.pos_to_linecol(node.position)
    if type is None:
        type = node.rule_name
    # log.debug(type)
    return without_empty_values(linecol=linecol, type=type, **kwargs)


def to_list(value):
    return value if isinstance(value, list) else [value]


def without_empty_values(**kwargs):
    """Allows 0 values but not None, [], {}."""
    return {
        key: value
        for key, value in kwargs.iteritems()
        if value is not None or isinstance(value, (list, dict)) and value
        }


# PEG parser visitor


class MLanguageVisitor(PTNodeVisitor):
    """
    Visitor class to transform AST in JSON.

    Useful line to debug visitor in ipython:
    print(node); node; len(node); print(json.dumps(children, indent=2)); len(children)
    """

    def visit__default__(self, node, children):
        """Ensure all grammar rules are implemented in visitor class."""
        if node.rule_name and node.rule_name != 'EOF':
            infos = {'rule': node.rule_name, 'node': node, 'children': children}
            raise NotImplementedError(infos)

    def visit_alias(self, node, children):
        value = find_one(children, type='symbol')
        return make_json_ast_node(
            name='alias',
            node=node,
            value=value,
            )

    def visit_application_declaration(self, node, children):
        name = find_one(children, type='symbol')
        return make_json_ast_node(
            name=name,
            node=node,
            )

    def visit_applications_reference(self, node, children):
        return make_json_ast_node(
            names=children[0],
            node=node,
            )

    def visit_attribute(self, node, children):
        name = find_one(children, type='symbol')
        value = find_one(children, type='integer')
        return make_json_ast_node(
            name=name,
            node=node,
            value=value,
            )

    def visit_brackets(self, node, children):
        value = find_one(children, type='symbol')
        return make_json_ast_node(
            node=node,
            value=value,
            )

    def visit_comment(self, node, children):
        return None

    def visit_comparaison(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            operators = [
                node[index].value
                for index in xrange(1, len(node), 2)
                ]
            # TODO Write and call a function infix_to_tree(operators=operators, operands=children)
            return make_json_ast_node(
                node=node,
                operands=children,
                operators=operators,
                )

    def visit_dans(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            import ipdb; ipdb.set_trace()

    def visit_enchaineur_declaration(self, node, children):
        name = find_one(children, type='symbol')
        applications = find_one(children, type='applications_reference')
        return make_json_ast_node(
            applications=applications,
            name=name,
            node=node,
            )

    def visit_erreur_declaration(self, node, children):
        name = find_one(children, type='symbol')
        erreur_type = find_one(children, type='erreur_type')
        strings = find_many(children, type='string')
        description = strings[3]
        codes = strings[:3] + [strings[4]]
        return make_json_ast_node(
            codes=codes,
            description=description,
            erreur_type=erreur_type,
            name=name,
            node=node,
            )

    def visit_erreur_type(self, node, children):
        return make_json_ast_node(
            node=node,
            value=node.value,
            )

    def visit_expression(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            operators = [
                node[index].value
                for index in xrange(1, len(node), 2)
                ]
            # TODO Write and call a function infix_to_tree(operators=operators, operands=children)
            return make_json_ast_node(
                node=node,
                operands=children,
                operators=operators,
                )

    def visit_factor(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            if children[0]['type'] == 'unary':
                result = children[1].copy()
                if result['type'] in ('float', 'integer'):
                    if children[0]['value'] == '-':
                        result['value'] = -result['value']
                else:
                    result['unary'] = children[0]['value']
            else:
                result = children[0]
            return result

    def visit_float(self, node, children):
        return make_json_ast_node(
            node=node,
            value=float(node.value),
            )

    def visit_function_call(self, node, children):
        return make_json_ast_node(
            parameters=to_list(children[1]),
            name=children[0],
            node=node,
            )

    def visit_function_parameters(self, node, children):
        return children

    def visit_group(self, node, children):
        assert len(children) == 1, children
        return children[0]

    def visit_integer(self, node, children):
        return make_json_ast_node(
            node=node,
            value=int(node.value),
            )

    def visit_integer_range(self, node, children):
        bounds = find_one_or_many(children, type='integer')
        assert len(bounds) == 2, bounds
        return make_json_ast_node(
            node=node,
            start=bounds[0],
            stop=bounds[1],
            )

    def visit_litteral(self, node, children):
        assert len(children) == 1, children
        return children[0]

    def visit_loop_expression(self, node, children):
        return make_json_ast_node(
            expression=children[1],
            node=node,
            variables=children[0]['value'],
            )

    def visit_loop_variable1(self, node, children):
        name = find_one(children, type='symbol')
        domain = find_one(children, type='loop_variable_domain')
        return make_json_ast_node(
            domain=domain,
            name=name,
            node=node,
            )

    def visit_loop_variable2(self, node, children):
        return make_json_ast_node(
            domain=children[1]['value'],
            name=children[0]['value'],
            node=node,
            type='loop_variable',
            )

    def visit_loop_variables(self, node, children):
        value = find_one_or_many(children, type='loop_variable')
        return make_json_ast_node(
            node=node,
            value=value,
            )

    def visit_loop_variable_domain(self, node, children):
        return make_json_ast_node(
            node=node,
            value=children,
            )

    def visit_m_source_file(self, node, children):
        # Do not wrap root rule in a sub-key.
        return children

    def visit_pour_variable_definition(self, node, children):
        loop_variables = find_one(children, type='loop_variables')
        variable_definition = find_one(children, type='variable_definition')
        return make_json_ast_node(
            loop_variables=loop_variables,
            node=node,
            variable_definition=variable_definition,
            )

    def visit_product(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            operators = [
                node[index].value
                for index in xrange(1, len(node), 2)
                ]
            # TODO Write and call a function infix_to_tree(operators=operators, operands=children)
            return make_json_ast_node(
                node=node,
                operands=children,
                operators=operators,
                )

    def visit_regle_declaration(self, node, children):
        application = find_one(children, type='applications_reference')
        enchaineur = find_one_or_none(children, type='regle_enchaineur')
        symbols = find_one_or_many(children, type='symbol')
        name, tags = symbols[-1], symbols[:-1] or None
        variable_definition_list = find_many_or_none(children, type='variable_definition')
        pour_variable_definition_list = find_many_or_none(children, type='pour_variable_definition')
        variables = ([] + (variable_definition_list or []) + (pour_variable_definition_list or [])) or None
        return make_json_ast_node(
            application=application,
            enchaineur=enchaineur,
            name=name,
            node=node,
            tags=tags,
            variables=variables,
            )

    def visit_regle_enchaineur(self, node, children):
        name = find_one_or_many(children, type='symbol')
        return make_json_ast_node(
            name=name,
            node=node,
            )

    def visit_string(self, node, children):
        return make_json_ast_node(
            node=node,
            value=node[1].value,
            )

    def visit_sum(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            operators = [
                node[index].value
                for index in xrange(1, len(node), 2)
                ]
            return make_json_ast_node(
                node=node,
                operands=children,
                operators=operators,
                )

    def visit_symbol(self, node, children):
        return make_json_ast_node(
            node=node,
            value=node.value,
            )

    def visit_symbol_enumeration(self, node, children):
        assert isinstance(children, list), children
        return children

    def visit_symbol_or_integer_range(self, node, children):
        assert len(children) == 1, children
        return children[0]

    def visit_tableau(self, node, children):
        value = find_one(children, type='integer')
        return make_json_ast_node(
            node=node,
            value=value,
            )

    def visit_ternary_operator(self, node, children):
        if len(children) == 1:
            return children[0]
        else:
            return make_json_ast_node(
                condition=children[0],
                node=node,
                value_if_false=children[2],
                value_if_true=children[1],
                )

    def visit_type(self, node, children):
        return make_json_ast_node(
            name='type',
            node=node,
            value=node[1].value,
            )

    def visit_unary(self, node, children):
        return make_json_ast_node(
            node=node,
            value=node.value,
            )

    def visit_variable_calculee_declaration(self, node, children):
        name = find_one(children, type='symbol')
        description = find_one(children, type='string')
        variable_calculee_tags = find_one_or_none(children, type='variable_calculee_tags')
        attributes = None if variable_calculee_tags is None else \
            {'type_tags': variable_calculee_tags}
        return make_json_ast_node(
            attributes=attributes,
            description=description,
            name=name,
            node=node,
            variable_type='calculee',
            )

    def visit_variable_calculee_tags(self, node, children):
        tags = [
            qualifier_node.value
            for qualifier_node in node
            ]
        return make_json_ast_node(
            node=node,
            value=tags,
            )

    def visit_variable_const_declaration(self, node, children):
        name = find_one(children, type='symbol')
        value = find_one(children, type='float')
        return make_json_ast_node(
            name=name,
            node=node,
            value=value,
            variable_type='const',
            )

    def visit_variable_declaration(self, node, children):
        assert len(children) == 1, children
        return children[0]

    def visit_variable_definition(self, node, children):
        brackets = find_one_or_none(children, type='brackets')
        if brackets:
            import ipdb; ipdb.set_trace()
        return make_json_ast_node(
            definition=children[-1],
            index=brackets,
            name=children[0],
            node=node,
            )

    def visit_variable_saisie_declaration(self, node, children):
        name = find_one(children, type='symbol')
        description = find_one(children, type='string')
        attributes = find_many_or_none(children, type='attribute')
        return make_json_ast_node(
            attributes=attributes,
            description=description,
            name=name,
            node=node,
            variable_type='saisie',
            )

    def visit_verif_declaration(self, node, children):
        symbols = find_one_or_many(children, type='symbol')
        name, tags = symbols[-1], symbols[:-1] or None
        application = find_one(children, type='applications_reference')
        conditions = find_one_or_many(children, type='verif_declaration_condition')
        return make_json_ast_node(
            application=application,
            conditions=conditions,
            name=name,
            node=node,
            tags=tags,
            )

    def visit_verif_declaration_condition(self, node, children):
        erreurs = find_one_or_many(children, type='verif_declaration_erreurs')
        # TODO Rename
        expression = find_one(children, type='verif_declaration_condition_expression')
        return make_json_ast_node(
            erreurs=erreurs,
            expression=expression,
            node=node,
            )

    def visit_verif_declaration_condition_expression(self, node, children):
        # TODO Rename
        value = clean_lines(node.value)
        return make_json_ast_node(
            node=node,
            value=value,
            )

    def visit_verif_declaration_erreurs(self, node, children):
        names = find_one_or_many(children, type='symbol')
        return make_json_ast_node(
            names=names,
            node=node,
            )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--debug', action='store_true', default=False, help='Debug Arpeggio parser')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Increase output verbosity')
    parser.add_argument('--no-visit', action='store_true', default=False, help='Do not visit the parsed tree')
    # parser.add_argument(
    #     '--no-reduce', dest='reduce', action='store_false', default=True, help='Do not reduce the parsed tree',
    #     )
    parser.add_argument('--rule', default='m_source_file', help='Do not reduce the parsed tree')
    parser.add_argument('source_file', help='Source file to parse')
    global args
    args = parser.parse_args()
    logging.basicConfig(level=logging.DEBUG if args.verbose or args.debug else logging.WARNING, stream=sys.stdout)

    with open(args.source_file) as source_file:
        source_code = source_file.read().decode('utf-8')
    log.debug('Source file "{}" was read with success.'.format(args.source_file))

    with open(m_grammar_file_path) as m_grammar_file:
        m_grammar = m_grammar_file.read()
    global m_parser
    # log.debug('reduce_tree = {}'.format(args.reduce))
    # m_parser = ParserPEG(m_grammar, args.rule, debug=args.debug, reduce_tree=args.reduce)
    m_parser = ParserPEG(m_grammar, args.rule, debug=args.debug, reduce_tree=False)
    log.debug('M language clean-PEG grammar was parsed with success.')

    parse_tree = m_parser.parse(source_code)
    log.debug('Source file "{}" was parsed with success.'.format(args.source_file))

    if not args.no_visit:
        result = visit_parse_tree(parse_tree, MLanguageVisitor(debug=args.debug))
        print json.dumps(result)

    return 0


if __name__ == '__main__':
    sys.exit(main())
