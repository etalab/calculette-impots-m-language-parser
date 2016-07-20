# -*- coding: utf-8 -*-

import os
import pkg_resources

from arpeggio import visit_parse_tree
from arpeggio.cleanpeg import ParserPEG
from nose.tools import assert_equal

from calculette_impots_m_language_parser.scripts import m_to_ast


script_dir_path = os.path.dirname(os.path.abspath(__file__))
distribution_dir_path = pkg_resources.get_distribution('calculette_impots_m_language_parser').location
m_grammar_file_path = os.path.join(distribution_dir_path, 'm_language.cleanpeg')

with open(m_grammar_file_path) as m_grammar_file:
    m_grammar = m_grammar_file.read()
m_parser = m_to_ast.m_parser = ParserPEG(m_grammar, 'm_source_file', reduce_tree=False)


class args(object):
    debug = False
    no_order = False

m_to_ast.args = args


def test_smoke():
    smoke_m_file_path = os.path.join(script_dir_path, 'valid_formulas.m')

    with open(smoke_m_file_path) as smoke_m_file:
        source_code = smoke_m_file.read()

    parse_tree = m_parser.parse(source_code)
    nodes = visit_parse_tree(parse_tree, m_to_ast.MLanguageVisitor())
    assert_equal(isinstance(nodes, list), True)


def test_name():
    '''Tests on format of the name that keeps 0'''
    source_code = '''
regle 007:
application : iliad , batch  ;
a = 1;
'''
    parse_tree = m_parser.parse(source_code)
    nodes = visit_parse_tree(parse_tree, m_to_ast.MLanguageVisitor())
    assert_equal(len(nodes), 1)
    assert_equal(nodes[0]['type'], 'regle')
    assert_equal(nodes[0]['name'], '007')


def test_assign():
    '''Test that an assignment is legal'''
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


def test_add():
    '''
    Test that an addition formula is legal
    Positive terms are grouped together first, then negative terms
    '''
    source_code = '''
regle 123:
application : iliad, batch  ;
apple = 1 - 3 + a;
'''
    parse_tree = m_parser.parse(source_code)
    nodes = visit_parse_tree(parse_tree, m_to_ast.MLanguageVisitor())
    assert_equal(len(nodes), 1)
    assert_equal(nodes[0]['type'], 'regle')
    assert_equal(nodes[0]['name'], '123')
    assert_equal(nodes[0]['applications'], ['iliad', 'batch'])
    assert_equal(len(nodes[0]['formulas']), 1)
    assert_equal(nodes[0]['formulas'][0]['type'], 'formula')
    assert_equal(nodes[0]['formulas'][0]['name'], 'apple')
    assert_equal(nodes[0]['formulas'][0]['expression']['type'], 'sum')
    assert_equal(len(nodes[0]['formulas'][0]['expression']['operands']), 3)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['type'], 'integer')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['value'], 1)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][1]['type'], 'symbol')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][1]['value'], 'a')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][2]['type'], 'negate')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][2]['operand']['type'], 'integer')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][2]['operand']['value'], 3)


def test_mult_div():
    ''''
    Test that a multiplication formula is legal
    The M language specifies that multiplication are first, and last is the division
    '''
    source_code = '''
regle 123:
application : iliad, batch;
apple = 3* a * b /c;
'''
    parse_tree = m_parser.parse(source_code)
    nodes = visit_parse_tree(parse_tree, m_to_ast.MLanguageVisitor())
    assert_equal(len(nodes), 1)
    assert_equal(nodes[0]['type'], 'regle')
    assert_equal(nodes[0]['name'], '123')
    assert_equal(len(nodes[0]['formulas']), 1)
    assert_equal(nodes[0]['formulas'][0]['type'], 'formula')
    assert_equal(nodes[0]['formulas'][0]['name'], 'apple')
    assert_equal(nodes[0]['formulas'][0]['expression']['type'], 'product')
    assert_equal(len(nodes[0]['formulas'][0]['expression']['operands']), 4)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['type'], 'integer')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['value'], 3)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][1]['type'], 'symbol')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][1]['value'], 'a')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][2]['type'], 'symbol')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][2]['value'], 'b')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][3]['type'], 'invert')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][3]['operand']['type'], 'symbol')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][3]['operand']['value'], 'c')


def test_mult_div_2():
    ''''
    Test that a combination of multiplication and division with brackets
    The M language specifies that multiplication are first, and last is the division
    '''
    source_code = '''
regle 123:
application : iliad, batch;
apple = 3.14*a / (b + 3) - 4;
'''
    parse_tree = m_parser.parse(source_code)
    nodes = visit_parse_tree(parse_tree, m_to_ast.MLanguageVisitor())
    assert_equal(len(nodes), 1)
    assert_equal(nodes[0]['type'], 'regle')
    assert_equal(nodes[0]['name'], '123')
    assert_equal(len(nodes[0]['formulas']), 1)
    assert_equal(nodes[0]['formulas'][0]['type'], 'formula')
    assert_equal(nodes[0]['formulas'][0]['name'], 'apple')
    assert_equal(nodes[0]['formulas'][0]['expression']['type'], 'sum')
    assert_equal(len(nodes[0]['formulas'][0]['expression']['operands']), 2)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['type'], 'product')
    assert_equal(len(nodes[0]['formulas'][0]['expression']['operands'][0]['operands']), 3)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][0]['type'], 'float')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][0]['value'], 3.14)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][1]['type'], 'symbol')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][1]['value'], 'a')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][2]['type'], 'invert')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][2]['operand']['type'], 'sum')
    assert_equal(len(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][2]['operand']['operands']), 2)
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][2]['operand']['operands'][0]['type'],
                 'symbol')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][0]['operands'][2]['operand']['operands'][0]['value'],
                 'b')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][1]['type'], 'negate')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][1]['operand']['type'], 'integer')
    assert_equal(nodes[0]['formulas'][0]['expression']['operands'][1]['operand']['value'], 4)
