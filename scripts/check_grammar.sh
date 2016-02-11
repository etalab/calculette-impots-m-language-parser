#!/usr/bin/env bash

# Verify that all the rules declared in the grammar file are handled by conversion script.

SCRIPT_DIR=$(dirname $(readlink -f "$BASH_SOURCE"))
SCRIPT="$SCRIPT_DIR/m_source_code_to_ast.py"
GRAMMAR_FILE=`realpath $SCRIPT_DIR/../data/m_language.cleanpeg`

EXTRACT_GRAMMAR_RULES="grep -o -E '^\w+' $GRAMMAR_FILE | grep -v EOF | sort"
EXTRACT_MAKE_FUNCTIONS_RULES="grep -Po '(?<=def make_).+(?=\(.+:)' $SCRIPT | sort"
EXTRACT_VISIT_FUNCTIONS_RULES="grep -Po '(?<=def visit_).+(?=\(.+:)' $SCRIPT | grep -v _default__ | sort"

echo "========= rules VERSUS make_ functions ========="
diff --side-by-side --suppress-common-lines <(eval $EXTRACT_GRAMMAR_RULES) <(eval $EXTRACT_MAKE_FUNCTIONS_RULES)

echo "========= rules VERSUS visit_ functions ========="
diff --side-by-side --suppress-common-lines <(eval $EXTRACT_GRAMMAR_RULES) <(eval $EXTRACT_VISIT_FUNCTIONS_RULES)
