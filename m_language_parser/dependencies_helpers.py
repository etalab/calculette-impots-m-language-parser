# -*- coding: utf-8 -*-


import json
import logging
import os
import pkg_resources

from toolz import get_in, valmap


log = logging.getLogger(__name__)


def filter_formulas_dependencies(definition_by_variable_name, dependencies_by_formula_name):
    def get_variable_type(variable_name):
        return definition_by_variable_name.get(variable_name, {}).get('type')

    def has_tag(variable_name, tag):
        return tag in get_in(
            ['attributes', 'tags'],
            definition_by_variable_name.get(variable_name, {}),
            default=[],
            )

    def is_calculee_variable(variable_name, tag=None):
        return get_variable_type(variable_name) == 'variable_calculee'

    formulas_dependencies_by_formula_name = valmap(
        lambda variables_names: list(filter(
            lambda variable_name: is_calculee_variable(variable_name) and not has_tag(variable_name, 'base'),
            variables_names,
            )),
        dependencies_by_formula_name,
        )
    return formulas_dependencies_by_formula_name


def load_dependencies_by_formula_name():
    m_language_parser_dir_path = pkg_resources.get_distribution('m_language_parser').location
    variables_dependencies_file_path = os.path.join(m_language_parser_dir_path, 'json', 'data',
                                                    'formulas_dependencies.json')
    with open(variables_dependencies_file_path) as variables_dependencies_file:
        variables_dependencies_str = variables_dependencies_file.read()
    dependencies_by_formula_name = json.loads(variables_dependencies_str)
    return dependencies_by_formula_name


def find_dependencies(formula_name, dependencies_by_formula_name):
    """Return a list of dependencies of `formula_name`."""
    def walk_dependencies(formula_name, dependencies, depth=0):
        if formula_name in dependencies:
            return
        formula_dependencies = dependencies_by_formula_name.get(formula_name)
        if formula_dependencies is None:
            # log.warning('Formula "{}" is referenced in a formula but is not defined'.format(formula_name))
            pass
        else:
            # log.debug('find_dependencies:{}{}({})'.format(' ' * depth, formula_name, formula_dependencies))
            for dependency_name in formula_dependencies:
                walk_dependencies(
                    dependencies=dependencies,
                    depth=depth+1,
                    formula_name=dependency_name,
                    )
        dependencies.append(formula_name)

    dependencies = []
    walk_dependencies(
        dependencies_by_formula_name=dependencies_by_formula_name,
        dependencies=dependencies,
        formula_name=formula_name,
        )
    return dependencies
