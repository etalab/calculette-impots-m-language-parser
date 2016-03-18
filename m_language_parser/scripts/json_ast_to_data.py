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

from toolz.curried import filter, map, mapcat, pipe, sorted

from m_language_parser import dependencies_visitors


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

    regles_dependencies_dicts = list(mapcat(
        load_regles_file,
        iter_json_file_names('chap-*.json', 'res-ser*.json'),
        ))

    def iter_formula_name_and_dependencies_pairs(preferred_application='batch'):
        visited_applications_by_variable_name = {}
        for regle_dependencies_dict in regles_dependencies_dicts:
            applications = regle_dependencies_dict['applications']
            assert applications is not None
            for variable_name, dependencies in regle_dependencies_dict['dependencies']:
                visited_applications = visited_applications_by_variable_name.get(variable_name)
                if visited_applications is not None:
                    is_double_defined_in_preferred_application = preferred_application in applications and \
                        preferred_application in visited_applications
                    assert not is_double_defined_in_preferred_application, (variable_name, visited_applications)
                    log.debug(
                        'Variable "{}" already visited and had another application, '
                        'but this one of "{}" is prefered => keep the dependencies ({}) '
                        'and the applications({}) of this one.'.format(
                            variable_name, preferred_application, dependencies, applications))
                if preferred_application in applications or visited_applications is None:
                    yield variable_name, dependencies
                visited_applications_by_variable_name[variable_name] = applications

    dependencies_by_formula_name = dict(iter_formula_name_and_dependencies_pairs())
    write_json_file(data=dependencies_by_formula_name, file_name='formulas_dependencies.json')

    # Write variables definitions

    definition_by_variable_name = pipe(
        variables_definitions,
        filter(lambda d: d['type'] in ('variable_calculee', 'variable_saisie')),
        map(lambda d: (d['name'], d)),  # Index by name
        dict,
        )
    write_json_file(data=definition_by_variable_name, file_name='variables_definitions.json')

    return 0


if __name__ == '__main__':
    sys.exit(main())
