#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
Extract semantic data from the JSON AST files.
"""


import argparse
import glob
import json
import logging
import os
import sys

from toolz import dissoc
from toolz.curried import filter, map, mapcat, pipe, sorted, valmap

from m_language_parser import dependencies_visitors


# Globals


args = None
script_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(script_name)

script_dir_path = os.path.dirname(os.path.abspath(__file__))
json_dir_path = os.path.abspath(os.path.join(script_dir_path, '..', '..', 'json'))
ast_dir_path = os.path.join(json_dir_path, 'ast')
output_dir_path = os.path.join(json_dir_path, 'semantic_data')


# Source code helper functions


def read_ast_json_file(json_file_name):
    json_file_path = os.path.join(ast_dir_path, json_file_name)
    with open(json_file_path) as json_file:
        json_str = json_file.read()
    nodes = json.loads(json_str)
    assert isinstance(nodes, list)
    return nodes


def write_json_file(file_name, data):
    file_path = os.path.join(output_dir_path, file_name)
    with open(file_path, 'w') as output_file:
        output_file.write(json.dumps(data, indent=2, sort_keys=True))
    log.info('Output file "{}" written with success'.format(file_path))


# Load files functions


def iter_json_file_names(*pathnames):
    for json_file_path in sorted(mapcat(
                lambda pathname: glob.iglob(os.path.join(ast_dir_path, pathname)),
                pathnames,
                )):
        json_file_name = os.path.basename(json_file_path)
        yield json_file_name


def load_regles_file(json_file_name):
    log.info('Loading "{}"...'.format(json_file_name))
    regles_nodes = read_ast_json_file(json_file_name)
    batch_application_regles_nodes = list(filter(
        lambda node: 'batch' in node['applications'],
        regles_nodes,
        ))
    formula_name_and_dependencies_pairs = mapcat(dependencies_visitors.visit_node, batch_application_regles_nodes)
    return formula_name_and_dependencies_pairs


def load_tgvH_file():
    json_file_name = 'tgvH.json'
    log.info('Loading "{}"...'.format(json_file_name))
    nodes = read_ast_json_file(json_file_name)
    variables_definitions = filter(
        lambda node: node['type'].startswith('variable_'),
        nodes,
        )
    return variables_definitions


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

    constant_by_name = pipe(
         variables_definitions,
         filter(lambda val: val['type'] == 'variable_const'),
         map(lambda d: (d['name'], d['value'])),
         dict,
         )
    write_json_file(data=constant_by_name, file_name='constants.json')

    variable_definition_by_name = pipe(
         variables_definitions,
         filter(lambda val: val['type'] in ('variable_calculee', 'variable_saisie')),
         map(lambda d: (d['name'], dissoc(d, 'linecol', 'name'))),
         dict,
         )
    write_json_file(data=variable_definition_by_name, file_name='variables_definitions.json')

    # Load regles

    formula_dependencies_by_name = dict(list(mapcat(
        load_regles_file,
        iter_json_file_names('chap-*.json', 'res-ser*.json'),
        )))
    formula_dependencies_by_name = valmap(lambda val: list(sorted(val)), formula_dependencies_by_name)
    write_json_file(data=formula_dependencies_by_name, file_name='variables_dependencies.json')

    return 0


if __name__ == '__main__':
    sys.exit(main())
