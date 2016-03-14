#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Extract data from the JSON AST files.
"""


import argparse
import glob
import json
import logging
import os
import sys

from toolz import dissoc
from toolz.curried import concat, filter, get_in, map, mapcat, pipe, sorted, valmap

from m_language_parser import dependencies_visitors


# Globals


args = None
script_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(script_name)

script_dir_path = os.path.dirname(os.path.abspath(__file__))
json_dir_path = os.path.abspath(os.path.join(script_dir_path, '..', '..', 'json'))
ast_dir_path = os.path.join(json_dir_path, 'ast')
output_dir_path = os.path.join(json_dir_path, 'data')


# Helper functions


# def get_ordered_formulas_names(formulas_dependencies_by_name):
#     """Return a list of formula names in a dependencies resolution order."""
#     # Flatten keys and values.
#     writable_formulas_names = set(mapcat(
#         lambda item: set([item[0]]) | set(item[1]), formulas_dependencies_by_name.items()
#         ))
#     ordered_formulas_names = []
#     expected_formulas_count = len(writable_formulas_names)  # Store it since writable_formulas_names is mutated below.
#     while len(ordered_formulas_names) < expected_formulas_count:
#         # Iterate sorted set for stability between executions of the script.
#         for writable_variable_name in sorted(writable_formulas_names):
#             if all(map(
#                     lambda dependency_name: dependency_name in ordered_formulas_names,
#                     formulas_dependencies_by_name.get(writable_variable_name, []),
#                     )):
#                 ordered_formulas_names.append(writable_variable_name)
#                 # log.debug('{} ordered_formulas_names added (latest {})'.format(
#                 #     len(ordered_formulas_names),
#                 #     writable_variable_name,
#                 #     ))
#         writable_formulas_names -= set(ordered_formulas_names)
#     return ordered_formulas_names


def build_ordered_formulas_names(formula_name, formulas_dependencies_by_name, ordered_formulas_names):
    """Write a list of formula names in a dependencies resolution order, starting by `formula_name`."""
    # log.debug('build_ordered_formulas_names: {}: {} ordered formulas written, latest = {}'.format(
    #     formula_name,
    #     len(ordered_formulas_names),
    #     ordered_formulas_names[-1] if ordered_formulas_names else 'None',
    #     ))
    if formula_name in ordered_formulas_names:
        return
    dependencies = formulas_dependencies_by_name.get(formula_name)
    if dependencies is not None:
        for dependency_name in dependencies:
            build_ordered_formulas_names(
                formula_name=dependency_name,
                formulas_dependencies_by_name=formulas_dependencies_by_name,
                ordered_formulas_names=ordered_formulas_names,
                )
    ordered_formulas_names.append(formula_name)


# Read and write files functions


def iter_json_file_names(*pathnames):
    for json_file_path in sorted(mapcat(
                lambda pathname: glob.iglob(os.path.join(ast_dir_path, pathname)),
                pathnames,
                )):
        json_file_name = os.path.basename(json_file_path)
        yield json_file_name


def load_regles_file(json_file_name):
    regles_nodes = read_ast_json_file(json_file_name)
    regles_nodes = list(filter(
        lambda node: 'batch' in node['applications'] or 'iliad' in node['applications'],
        regles_nodes,
        ))
    return mapcat(dependencies_visitors.visit_node, regles_nodes)


def load_tgvH_file():
    json_file_name = 'tgvH.json'
    nodes = read_ast_json_file(json_file_name)
    variables_definitions = filter(
        lambda node: node['type'].startswith('variable_'),
        nodes,
        )
    return variables_definitions


def read_ast_json_file(json_file_name):
    json_file_path = os.path.join(ast_dir_path, json_file_name)
    log.info('Loading "{}"...'.format(json_file_path))
    with open(json_file_path) as json_file:
        json_str = json_file.read()
    nodes = json.loads(json_str)
    assert isinstance(nodes, list)
    return nodes


def write_json_file(file_name, data):
    file_path = os.path.join(output_dir_path, file_name)
    with open(file_path, 'w') as output_file:
        json.dump(data, fp=output_file, indent=2, sort_keys=True)
    log.info('Output file "{}" written with success'.format(file_path))


# Main


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-d', '--debug', action='store_true', default=False, help='Display debug messages')
    parser.add_argument('-v', '--verbose', action='store_true', default=False, help='Increase output verbosity')
    global args
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.debug else (logging.INFO if args.verbose else logging.WARNING),
        stream=sys.stdout,
        )

    if not os.path.isdir(output_dir_path):
        os.mkdir(output_dir_path)

    # Load variables definitions

    variables_definitions = list(load_tgvH_file())

    # Write constants

    constant_by_name = pipe(
         variables_definitions,
         filter(lambda val: val['type'] == 'variable_const'),
         map(lambda d: (d['name'], d['value'])),
         dict,
         )
    write_json_file(data=constant_by_name, file_name='constants.json')

    # Write variables definitions

    variable_definition_by_name = pipe(
         variables_definitions,
         filter(lambda val: val['type'] in ('variable_calculee', 'variable_saisie')),
         map(lambda d: (d['name'], dissoc(d, 'linecol', 'name'))),
         dict,
         )
    write_json_file(data=variable_definition_by_name, file_name='variables_definitions.json')

    # Write variables dependencies

    dependencies_dicts = list(mapcat(
        load_regles_file,
        iter_json_file_names('chap-*.json', 'res-ser*.json'),
        ))
    variables_dependencies_by_name = {}
    for dependencies_dict in dependencies_dicts:
        for variable_name, dependencies in dependencies_dict['dependencies']:
            if variable_name not in variables_dependencies_by_name or 'batch' in dependencies_dict['applications']:
                variables_dependencies_by_name[variable_name] = dependencies
    write_json_file(data=variables_dependencies_by_name, file_name='variables_dependencies.json')

    # Write ordered formula names

    def get_variable_type(variable_name):
        return variable_definition_by_name.get(variable_name, {}).get('type')

    def has_tag(variable_name, tag):
        return tag in get_in(
            ['attributes', 'tags'],
            variable_definition_by_name.get(variable_name, {}),
            default=[],
            )

    def is_calculee_variable(variable_name, tag=None):
        return get_variable_type(variable_name) == 'variable_calculee'

    formulas_dependencies_by_name = valmap(
        lambda variables_names: list(filter(
            lambda variable_name: is_calculee_variable(variable_name) and not has_tag(variable_name, 'base'),
            variables_names,
            )),
        variables_dependencies_by_name,
        )

    ordered_formulas_names = []
    log.info('{} different formulas'.format(
        len(set(formulas_dependencies_by_name.keys()) | set(concat(formulas_dependencies_by_name.values())))
        ))
    build_ordered_formulas_names(
        formula_name='IINET',
        formulas_dependencies_by_name=formulas_dependencies_by_name,
        ordered_formulas_names=ordered_formulas_names,
        )
    write_json_file(data=ordered_formulas_names, file_name='ordered_formulas.json')

    return 0


if __name__ == '__main__':
    sys.exit(main())
