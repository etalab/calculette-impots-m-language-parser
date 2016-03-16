# -*- coding: utf-8 -*-


import json
import logging
import os
import pkg_resources


log = logging.getLogger(__name__)


def build_formula_dependencies(formula_name, formula_dependencies, variables_dependencies_by_name=None):
    """Write a list of formula names in a dependencies resolution order, starting with `formula_name`."""
    # log.debug('build_formula_dependencies: {}: {} ordered formulas written, latest = {}'.format(
    #     formula_name,
    #     len(formula_dependencies),
    #     formula_dependencies[-1] if formula_dependencies else 'None',
    #     ))
    if variables_dependencies_by_name is None:
        m_language_parser_dir_path = pkg_resources.get_distribution('m_language_parser').location
        variables_dependencies_file_path = os.path.join(m_language_parser_dir_path, 'json', 'data',
                                                        'variables_dependencies.json')
        with open(variables_dependencies_file_path) as variables_dependencies_file:
            variables_dependencies_str = variables_dependencies_file.read()
        variables_dependencies_by_name = json.loads(variables_dependencies_str)
    if formula_name in formula_dependencies:
        return
    dependencies = variables_dependencies_by_name.get(formula_name)
    if dependencies is None:
        log.warning('Formula "{}" is used in a formula but is not defined'.format(formula_name))
    else:
        for dependency_name in dependencies:
            build_formula_dependencies(
                formula_dependencies=formula_dependencies,
                formula_name=dependency_name,
                variables_dependencies_by_name=variables_dependencies_by_name,
                )
    formula_dependencies.append(formula_name)
