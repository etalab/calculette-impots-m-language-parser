# -*- coding: utf-8 -*-


"""
Dependencies helpers are functions dealing with enumerating formulas in the right order.
"""


import logging

from toolz import mapcat

from ..core import get_variable_type


log = logging.getLogger(__name__)


# Helpers


def is_writable(formula_name):
    return get_variable_type(formula_name) == 'variable_calculee'


# Main function


def get_ordered_formulas_names(formula_dependencies_by_name):
    """Return a list of formula names in a dependencies resolution order."""
    writable_formula_dependencies_by_name = {
        key: set(filter(is_writable, values))
        for key, values in formula_dependencies_by_name.items()
        if is_writable(key)
        }
    writable_formulas_names = set(mapcat(
        lambda item: set([item[0]]) | set(item[1]), writable_formula_dependencies_by_name.items()
        ))
    assert all(map(is_writable, writable_formulas_names))
    ordered_formulas_names = []
    expected_formulas_count = len(writable_formulas_names)  # Store it since writable_formulas_names is mutated below.
    while len(ordered_formulas_names) < expected_formulas_count:
        # Iterate sorted set for stability between executions of the script.
        for writable_formula_name in sorted(writable_formulas_names):
            if all(map(
                    lambda dependency_name: dependency_name in ordered_formulas_names,
                    writable_formula_dependencies_by_name.get(writable_formula_name, []),
                    )):
                ordered_formulas_names.append(writable_formula_name)
                log.debug('{} ordered_formulas_names added (latest {})'.format(
                    len(ordered_formulas_names),
                    writable_formula_name,
                    ))
        writable_formulas_names -= set(ordered_formulas_names)
    return ordered_formulas_names
