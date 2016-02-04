#!/usr/bin/env bash

# Exécute le script m_source_code_to_ast.py sur les fichiers pris en charge et écrase les fichiers JSON.


SCRIPT_DIR=$(dirname $(readlink -f "$BASH_SOURCE"))
SCRIPT="$SCRIPT_DIR/m_source_code_to_ast.py"
SOURCES_DIR="$1"
OUTPUT_DIR="$SCRIPT_DIR/../json"

if [ -z "$SOURCES_DIR" -o ! -d "$SOURCES_DIR" ]; then
  echo "usage: $0 <sources_dir>"
  exit -1
fi

rm -f $OUTPUT_DIR/*

for filepath in $SOURCES_DIR/*.m
do
  filename=`basename $filepath`
  echo "Converting $filename..."
  command="python $SCRIPT $filepath"
  python $SCRIPT $filepath | jq . > $OUTPUT_DIR/${filename%.*}.json
  if [ ${PIPESTATUS[0]} != 0 ]; then
    echo "Error, exiting. Command was: \"$command\""
    exit -1
  fi
  echo "OK"
done
