#!/usr/bin/env bash

# Exécute le script m_source_code_to_ast.py sur les fichiers pris en charge et écrase les fichiers JSON.


set -x


python scripts/m_source_code_to_ast.py ../code-source-impots-revenus/src/chap-1.m | jq . > json/chap-1.json
python scripts/m_source_code_to_ast.py ../code-source-impots-revenus/src/chap-2.m | jq . > json/chap-2.json
python scripts/m_source_code_to_ast.py ../code-source-impots-revenus/src/chap-3.m | jq . > json/chap-3.json
python scripts/m_source_code_to_ast.py ../code-source-impots-revenus/src/chap-4.m | jq . > json/chap-4.json
python scripts/m_source_code_to_ast.py ../code-source-impots-revenus/src/tgvH.m | jq . > json/tgvH.json
