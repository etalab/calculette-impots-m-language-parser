#!/usr/bin/env bash

SCRIPT_DIR=$(dirname $(readlink -f "$BASH_SOURCE"))
DEPS_FILE="$SCRIPT_DIR/../../json/semantic_data/variables_dependencies.json"

VARIABLE="$1"

[ -z "$1" ] && echo "usage: $0 variable" && exit -1

jq -r "[to_entries | .[] | select(.value | bsearch(\"$1\") >= 0) | .key] | sort | unique | .[]" $DEPS_FILE
