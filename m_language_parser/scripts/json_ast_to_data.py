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

from toolz.curried import assoc, filter, get_in, map, mapcat, pipe, sorted, valmap

from m_language_parser import dependencies_helpers, dependencies_visitors


# Globals


args = None
script_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(script_name)

script_dir_path = os.path.dirname(os.path.abspath(__file__))
json_dir_path = os.path.abspath(os.path.join(script_dir_path, '..', '..', 'json'))
ast_dir_path = os.path.join(json_dir_path, 'ast')
output_dir_path = os.path.join(json_dir_path, 'data')


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

    # Write variables dependencies

    dependencies_dicts = list(mapcat(
        load_regles_file,
        iter_json_file_names('chap-*.json', 'res-ser*.json'),
        ))
    applications_by_variable_name = {}
    dependencies_by_variable_name = {}
    for dependencies_dict in dependencies_dicts:
        applications = dependencies_dict['applications']
        for variable_name, dependencies in dependencies_dict['dependencies']:
            applications_by_variable_name[variable_name] = applications
            if variable_name not in dependencies_by_variable_name or 'batch' in applications:
                if variable_name in dependencies_by_variable_name and 'batch' in applications:
                    log.warning('Variable "{}" already met from another application, '
                                'but this one of "batch" is prefered => keep the dependencies of this one ({}).'.format(
                                    variable_name, dependencies))
                dependencies_by_variable_name[variable_name] = dependencies
    write_json_file(data=dependencies_by_variable_name, file_name='variables_dependencies.json')

    # Write variables definitions

    variable_definition_by_name = pipe(
         variables_definitions,
         filter(lambda val: val['type'] in ('variable_calculee', 'variable_saisie')),
         map(lambda d: assoc(d, 'applications', applications_by_variable_name[d['name']])
             if d['name'] in applications_by_variable_name else d),
         map(lambda d: (d['name'], d)),  # Index by name
         dict,
         )
    write_json_file(data=variable_definition_by_name, file_name='variables_definitions.json')

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
        dependencies_by_variable_name,
        )

    formula_dependencies = []
    # log.info('{} different formulas'.format(
    #     len(set(formulas_dependencies_by_name.keys()) | set(concat(formulas_dependencies_by_name.values())))
    #     ))
    log.info('Building ordered formulas...')
    dependencies_helpers.build_formula_dependencies(
        formula_dependencies=formula_dependencies,
        formula_name='IINETIR',
        variables_dependencies_by_name=formulas_dependencies_by_name,
        )
    write_json_file(data=formula_dependencies, file_name='ordered_formulas.json')

    return 0


if __name__ == '__main__':
    sys.exit(main())
