#!/usr/bin/env bash

# Exécute le script m_source_code_to_ast.py sur les fichiers pris en charge et écrase les fichiers JSON.


SCRIPT_DIR=$(dirname $(readlink -f "$BASH_SOURCE"))
SCRIPT="$SCRIPT_DIR/m_source_file_to_json_ast.py"
OPTIONS=""
# OPTIONS="--no-visit"
SOURCES_DIR="${1%/}"
OUTPUT_DIR="$SCRIPT_DIR/../json"

if [ -z "$SOURCES_DIR" -o ! -d "$SOURCES_DIR" ]; then
  echo "usage: $0 <sources_dir>"
  exit -1
fi

echo "==========================================="
echo "JSON files are kept. Remove them if wanted."
echo "==========================================="
# rm -f $OUTPUT_DIR/*

for filepath in $SOURCES_DIR/*.m
do
  filename=`basename $filepath`
  echo -n "Converting $filename... "
  command="python $SCRIPT $filepath $OPTIONS"
  output_file=`realpath $OUTPUT_DIR/${filename%.*}.json`
  if [ -e $output_file ] ; then
    echo
    echo "    File $output_file exists, skip"
  else
    python $SCRIPT $filepath $OPTIONS | jq . > $output_file
  fi
  if [ ${PIPESTATUS[0]} != 0 ]; then
    rm $output_file
    echo "Error, exiting. Command was: \"$command\""
    exit -1
  fi
  echo "OK"
done
