# Parser du langage M

Ce dépôt contient un "[parser](https://fr.wiktionary.org/wiki/parser)" de code source
du [calculateur des impôts sur les revenus](https://git.framasoft.org/openfisca/code-source-impots-revenus)
écrit dans un langage dédié nommé "M".

- [`data/m_language.cleanpeg`](data/m_language.cleanpeg) contient la description de la grammaire du langage M
au format [cleanpeg](http://igordejanovic.net/Arpeggio/grammars/#grammars-written-in-peg-notations)
- [`scripts/m_source_file_to_json_ast.py`](scripts/m_source_file_to_json_ast.py) est le script de transformation du code source
vers un AST en JSON
- [`json/chap-1.json`](json/chap-1.json.json) est un exemple de la transformation en JSON du fichier
[`chap-1.m`](https://git.framasoft.org/openfisca/code-source-impots-revenus/tree/master/src/chap-1.m)

## Installation

Le langage Python 3 est utilisé.

```
pip3 install --editable . --user
```

> L'option `--user` sert sur les systèmes GNU/Linux.

Un utilisateur plus expérimenté en Python peut utiliser
un [`virtualenv`](https://virtualenv.readthedocs.org/en/latest/) s'il le souhaite.

## Utilisation

```
# Convertir un répertoire de sources M entier en AST :
$ ./m_language_parser/scripts/convert_dir.sh /path/to/code-source-impots-revenus/src

# Convertir un fichier M particulier :
$ python3 m_language_parser/scripts/m_source_file_to_json_ast.py file.m

# Extraire les données JSON sémantiques :
$ python3 m_language_parser/scripts/json_ast_to_semantic_data.py -v
```

> Ceci n'est utile que si les fichiers source M changent car les fichiers JSON ont été commités dans le répertoire
> [json](json).

## Grammaire

Le fichier de grammaire [`m_language.cleanpeg`](data/m_language.cleanpeg) est au format [Clean PEG](http://igordejanovic.net/Arpeggio/grammars/).

La bibliothèque utilisée pour le "parsing" est [Arpeggio](http://igordejanovic.net/Arpeggio/).

La partie de la grammaire touchant aux expressions est basée
sur [ce tutoriel](http://igordejanovic.net/Arpeggio/tutorials/calc/).
