# Parser du langage M

Ce dépôt contient un "[parser](https://fr.wiktionary.org/wiki/parser)" du langage dédié nommé "M" utilisé par le code source de la [calculette des impôts sur les revenus](https://github.com/etalab/calculette-impots-m-source-code), ainsi que le code parsé, au format json.

- [`scripts/parse_code.py`](scripts/parse_code.py) est le script de transformation du code source vers un AST en JSON
- [`m_language.cleanpeg`](calculette_impots_m_language_parser/m_language.cleanpeg) contient la description de la grammaire du langage M au format [cleanpeg](http://igordejanovic.net/Arpeggio/grammars/#grammars-written-in-peg-notations)


## Données produites

Les fichiers JSON du répertoire `json` sont la traduction sous forme d'AST (abstract syntax tree) des fichiers du langage M. Chaque sous-répertoire de ce dossier contient la traduction d'un code source pour une année. Par exemple, le dossier `json/sourcesm2015m_4_6` contient la traduction du code pour le calcul de l'impôt sur les revenus de 2015.

Pour chaque année, un sous-répertoire `1_ast_by_file` contient une traduction directe, fichier par fichier, qui conserve toutes les informations des fichiers sources (sauf les commentaires en milieu de ligne). Ces fichiers sont créés par le module `m_to_ast.py`.

Le sous-répertoire `2_simplified_ast` contient les formules définies par l'application `batch`. L'AST a une forme simplifiée, avec des symboles, des constantes et des appels de fonctions mais sans boucles. Ces fichiers sont créés par le module `simplify_ast.py`.

Le sous-répertoire `3_light_ast` contient un AST avec la même structure que dans le répertoire `2_simplified_ast`, mais seules sont conservées les variables utiles pour calculer un ensemble de variables "racines" déterminé par une équipe d'experts de la DGFiP. Ces fichiers sont créés par le module `lighten_ast.py`.


## Installation

Le langage Python 3 est utilisé.

Ce paquet n'est pas publié sur le dépôt [PyPI](https://pypi.python.org/pypi) donc pour l'installer il faut passer par `git clone`.

```
git clone https://github.com/etalab/calculette-impots-m-language-parser.git
cd calculette-impots-m-language-parser
pip3 install --editable . --user
```

> L'option `--user` sert sur les systèmes GNU/Linux.

> Pour les utilisateurs expérimentés, il est préférable d'utiliser un environnement virtuel. Voir par exemples [pew](https://github.com/berdario/pew).


## Utilisation

Ce projet est à considérer comme un dépôt de données JSON qui peuvent être utilisées par tout projet faisant des calcul d'imposition, par exemple [calculette-impots-exemples](https://github.com/etalab/calculette-impots-exemples).


## Grammaire

Le fichier de grammaire [`m_language.cleanpeg`](calculette_impots_m_language_parser/m_language.cleanpeg) est au format [Clean PEG](http://igordejanovic.net/Arpeggio/grammars/).

La bibliothèque utilisée pour le "parsing" est [Arpeggio](http://igordejanovic.net/Arpeggio/).

La partie de la grammaire touchant aux expressions est basée sur [ce tutoriel](http://igordejanovic.net/Arpeggio/tutorials/calc/).


## Regénérer les fichiers JSON

Les étapes suivantes sont a exécuter lorsque les fichiers source M, la grammaire ou bien le code du parser a changé.

* Renseigner le dossier source dans le script `scripts/parse_code_m.py`. (TODO: en faire une option CLI)

* Exécuter le script `python calculette_impots_m_language_parser/scripts/parse_code_m.py > logs.txt`


## Tests

`python3 setup.py test`


## Licence

Les fichiers json sont soumises à la licence CeCILL v2.1.

Le code source du parser est soumise à la licence MIT.


## Autre

Le fichiers suivants ont été produits lors du hackathon CodeImpôt début avril 2016 et ne sont actuellement pas maintenus :
* `scripts/check_grammar.sh`
* `scripts/compute_signatures.py`
* `notebooks/common_ast.ipynb`
* `notebooks/graph-stats.ipynb`
* `dependencies_visitor.py`
* `unloop_herlpers.py`
