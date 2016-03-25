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

from toolz.curried import assoc, dissoc, filter, map, mapcat, merge, merge_with, pipe, pluck, sorted

from calculette_impots_m_language_parser import dependencies_visitors, unloop_helpers


# Globals


args = None
script_name = os.path.splitext(os.path.basename(__file__))[0]
log = logging.getLogger(script_name)

script_dir_path = os.path.dirname(os.path.abspath(__file__))
json_dir_path = os.path.abspath(os.path.join(script_dir_path, '..', '..', 'json'))
ast_dir_path = os.path.join(json_dir_path, 'ast')


# Read and write files functions


def iter_json_file_names(*pathnames):
    for json_file_path in sorted(mapcat(
                lambda pathname: glob.iglob(os.path.join(ast_dir_path, pathname)),
                pathnames,
                )):
        json_file_name = os.path.basename(json_file_path)
        yield json_file_name


def load_regles_nodes(json_file_name):
    return pipe(
        read_ast_json_file(json_file_name),
        filter(lambda node: 'batch' in node['applications']),
        map(lambda d: assoc(d, 'source_file_name', '{}.m'.format(os.path.splitext(json_file_name)[0]))),
        )


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
    file_path = os.path.join(json_dir_path, file_name)
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

    if not os.path.isdir(json_dir_path):
        os.mkdir(json_dir_path)
    if not os.path.isdir(ast_dir_path):
        os.mkdir(ast_dir_path)

    # Load variables definitions

    tgvh_infos = list(load_tgvH_file())

    # Write constants

    constant_by_name = pipe(
         tgvh_infos,
         filter(lambda val: val['type'] == 'variable_const'),
         map(lambda d: (d['name'], d['value'])),
         dict,
         )
    write_json_file(data=constant_by_name, file_name='constants.json')

    # Write variables dependencies

    regles_nodes = list(mapcat(load_regles_nodes, iter_json_file_names('chap-*.json', 'res-ser*.json')))
    dependencies_by_formula_name = dict(list(mapcat(dependencies_visitors.visit_node, regles_nodes)))
    write_json_file(data=dependencies_by_formula_name, file_name='formulas_dependencies.json')

    # Write variables definitions

    ast_infos_by_variable_name = {}
    for regle_node in regles_nodes:
        regle_infos = {
            'regle_applications': regle_node['applications'],
            'regle_linecol': regle_node['linecol'],
            'regle_name': regle_node['name'],
            'source_file_name': regle_node['source_file_name'],
            }
        regle_tags = list(pluck('value', regle_node.get('tags', [])))
        if regle_tags:
            regle_infos['regle_tags'] = regle_tags
        for formula_node in regle_node['formulas']:
            if formula_node['type'] == 'formula':
                ast_infos_by_variable_name[formula_node['name']] = assoc(
                    regle_infos, 'formula_linecol', formula_node['linecol'])
            elif formula_node['type'] == 'pour_formula':
                for unlooped_formula_node in unloop_helpers.iter_unlooped_nodes(
                        loop_variables_nodes=formula_node['loop_variables'],
                        node=formula_node['formula'],
                        unloop_keys=['name'],
                        ):
                    pour_formula_infos = merge(regle_infos, {
                        'pour_formula_linecol': formula_node['formula']['linecol'],
                        'pour_formula_name': formula_node['formula']['name'],
                        })
                    ast_infos_by_variable_name[unlooped_formula_node['name']] = pour_formula_infos
            else:
                assert False, 'Unhandled formula_node type: {}'.format(formula_node)

    def rename_key(d, key_name, key_new_name):
        return assoc(dissoc(d, key_name), key_new_name, d[key_name])

    tgvh_infos_by_variable_name = pipe(
        tgvh_infos,
        filter(lambda d: d['type'] in ('variable_calculee', 'variable_saisie')),
        map(lambda d: rename_key(d, 'linecol', 'tgvh_linecol')),
        map(lambda d: (d['name'], d)),  # Index by name
        dict,
        )

    definition_by_variable_name = merge_with(merge, ast_infos_by_variable_name, tgvh_infos_by_variable_name)

    write_json_file(data=definition_by_variable_name, file_name='variables_definitions.json')

    return 0


if __name__ == '__main__':
    sys.exit(main())
