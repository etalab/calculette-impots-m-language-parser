# -*- coding: utf-8 -*-

import os
import pkg_resources

from arpeggio import visit_parse_tree
from arpeggio.cleanpeg import ParserPEG
from nose.tools import assert_equal

from calculette_impots_m_language_parser.scripts import m_to_ast


distribution_dir_path = pkg_resources.get_distribution('calculette_impots_m_language_parser').location
m_grammar_file_path = os.path.join(distribution_dir_path, 'm_language.cleanpeg')

with open(m_grammar_file_path) as m_grammar_file:
    m_grammar = m_grammar_file.read()
m_parser = m_to_ast.m_parser = ParserPEG(m_grammar, 'm_source_file', reduce_tree=False)


class args(object):
    debug = False
    no_order = False

m_to_ast.args = args


def test_regle():
    source_code = '''
regle 999:
application : iliad , batch  ;
a = 1;
'''
    parse_tree = m_parser.parse(source_code)
    nodes = visit_parse_tree(parse_tree, m_to_ast.MLanguageVisitor())
    assert_equal(len(nodes), 1)
    assert_equal(nodes[0]['type'], 'regle')
    assert_equal(nodes[0]['name'], '999')
    assert_equal(nodes[0]['applications'], ['iliad', 'batch'])
    assert_equal(len(nodes[0]['formulas']), 1)
    assert_equal(nodes[0]['formulas'][0]['type'], 'formula')
    assert_equal(nodes[0]['formulas'][0]['name'], 'a')
    assert_equal(nodes[0]['formulas'][0]['expression']['type'], 'integer')
    assert_equal(nodes[0]['formulas'][0]['expression']['value'], 1)

