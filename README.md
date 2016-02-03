# Parser du langage M

Ce dépôt contient un "[parser](https://fr.wiktionary.org/wiki/parser)" de code source
du [calculateur des impôts sur les revenus](https://git.framasoft.org/openfisca/code-source-impots-revenus)
écrit dans un langage dédié nommé "M".

- [`data/m.cleanpeg`](data/m.cleanpeg) contient la description de la grammaire du langage M
au format [cleanpeg](http://igordejanovic.net/Arpeggio/grammars/#grammars-written-in-peg-notations)
- [`scripts/m_source_code_to_ast.py`](scripts/m_source_code_to_ast.py) est le script de transformation du code source
vers un AST en JSON
- [`json/chap-1.json`](json/chap-1.json.json) est un exemple de la transformation en JSON du fichier
[`chap-1.m`](https://git.framasoft.org/openfisca/code-source-impots-revenus/tree/master/src/chap-1.m)

## Installation des dépendances

```
pip install -r requirements.txt --user
```

L'option `--user` sert sur les systèmes GNU/Linux.

Un utilisateur plus expérimenté en Python peut utiliser
un [`virtualenv`](https://virtualenv.readthedocs.org/en/latest/) s'il le souhaite.

## Exécution du script

```
$ python scripts/m_source_code_to_ast.py
```
