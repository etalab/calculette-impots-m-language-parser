import os
import inspect

import calculette_impots_m_language_parser
from calculette_impots_m_language_parser import m_to_ast, simplify_ast, lighten_ast


source_base_dir = '/data/projects/impots/sources_m/sources-utf8'
package_base_dir = os.path.dirname(os.path.dirname(inspect.getfile(calculette_impots_m_language_parser)))
target_base_dir = os.path.join(package_base_dir, 'json')

source_dirs = sorted(os.listdir(source_base_dir))
for millesime_name in source_dirs:
    print('***{}***'.format(millesime_name))

    millesime_target_dir = os.path.join(target_base_dir, millesime_name)
    os.mkdir(millesime_target_dir)


    # 1_ast_by_file

    millesime_source_dir = os.path.join(source_base_dir, millesime_name)
    filenames = os.listdir(millesime_source_dir)

    millesime_ast_by_file_dir = os.path.join(millesime_target_dir, '1_ast_by_file')
    os.mkdir(millesime_ast_by_file_dir)

    for filename in filenames:
        barename = os.path.splitext(filename)[0]
        source_file_path = os.path.join(millesime_source_dir, filename)
        target_file_path = os.path.join(millesime_ast_by_file_dir, barename + '.json')

        with open(source_file_path, 'r') as f:
            source_code = f.read()

        ast = m_to_ast.parse_m_file(source_code)

        with open(target_file_path, 'w') as f:
            f.write(ast)

    # 2_simplified_ast

    millesime_simplified_ast_dir = os.path.join(millesime_target_dir, '2_simplified_ast')
    os.mkdir(millesime_simplified_ast_dir)

    simplify_ast.simplify_ast(millesime_ast_by_file_dir, millesime_simplified_ast_dir)


    # 3_light_ast

    millesime_light_ast_dir = os.path.join(millesime_target_dir, '3_light_ast')
    os.mkdir(millesime_light_ast_dir)

    lighten_ast.lighten_ast(millesime_simplified_ast_dir, millesime_light_ast_dir)
