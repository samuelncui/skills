# Bilingual PDF

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Placez les contenus correspondants là où le lecteur peut les comparer : débuts de paragraphes, éléments de liste et lignes de tableau alignés, avec un séparateur stable entre les colonnes physiques. Choisissez si les longs paragraphes restent d’un seul tenant ou se poursuivent sur plusieurs pages. LaTeX natif et JSON partagent un même paquet de mise en page de référence.

L’agent appelant fournit les contenus appariés. Cette compétence les met en page ; elle ne choisit pas les traductions, ne réécrit pas le texte et ne décide pas quelles affirmations se correspondent.

Cette compétence met en page les textes appariés fournis. Elle ne couvre pas l’OCR, l’extraction du contenu d’un PDF existant, la traduction automatique ni la conservation de sa mise en page d’origine.

## Fonctionnalités

- Aligne séparément chaque paire de paragraphes, d’éléments de liste et de lignes de tableau, quelle que soit la longueur de la traduction
- Permet à un paragraphe de se poursuivre sur plusieurs pages, puis réaligne la paire suivante
- Distingue l’ordre physique gauche/droite du sens d’écriture LTR/RTL
- Affiche une image commune sur toute la largeur avec des légendes appariées, ou deux images adaptées à chaque langue
- Partage les compteurs d’équations et de figures et génère des liens vers les pages du document
- Prend en charge les éditions bilingues, de gauche seule ou de droite seule, ainsi que la configuration du papier, de la reliure, des couvertures, des numéros de page, des styles sémantiques et de la navigation

[![Alignement des paragraphes du guide anglais/chinois](examples/en-zh-Hans/preview.png)](examples/en-zh-Hans/output.pdf)

[![Exemple anglais/hébreu](examples/en-he/preview.png)](examples/en-he/output.pdf)

Ces aperçus proviennent des sorties réelles. Ouvrez les PDF pour voir toutes les pages ; l’image de la première page facilite la consultation, mais ne constitue pas une preuve de vérification visuelle complète.

## Des exemples fondés sur leur propre mode d’emploi

Chaque édition reprend le même guide d’utilisation pour présenter des paragraphes, un tableau, des figures, des références et une courte formule. Les passages anglais et chinois récurrents sont identiques d’une édition à l’autre.

| Langues | PDF | Source structurée | Projet natif |
| --- | --- | --- | --- |
| Anglais / français | [output.pdf](examples/en-fr/output.pdf) | [source.json](examples/en-fr/source.json) | [main.tex](examples/en-fr/main.tex) |
| Anglais / chinois | [output.pdf](examples/en-zh-Hans/output.pdf) | [source.json](examples/en-zh-Hans/source.json) | [main.tex](examples/en-zh-Hans/main.tex) |
| Anglais / arabe | [output.pdf](examples/en-ar/output.pdf) | [source.json](examples/en-ar/source.json) | [main.tex](examples/en-ar/main.tex) |
| Anglais / hébreu | [output.pdf](examples/en-he/output.pdf) | [source.json](examples/en-he/source.json) | [main.tex](examples/en-he/main.tex) |
| Chinois / japonais | [output.pdf](examples/zh-Hans-ja/output.pdf) | [source.json](examples/zh-Hans-ja/source.json) | [main.tex](examples/zh-Hans-ja/main.tex) |

Les illustrations propres aux exemples n’existent qu’en un seul exemplaire dans `examples/shared/`. Le répertoire d’exécution `assets/` contient le paquet réutilisable et les profils facultatifs. Les exemples natifs se compilent sans Python ni outils de maintenance du dépôt.

## LaTeX natif

Depuis le répertoire d’installation de cette compétence :

```sh
cd examples/en-fr
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape -jobname=output main.tex
```

Pour votre propre travail, copiez un exemple complet dans un nouveau répertoire. Préservez la relation entre les chemins du paquet et des images, ou copiez les éléments nécessaires dans un projet portable. Modifiez `content.tex` et `languages.tex`. La [référence complète de l’API native](references/latex.md) documente chaque commande publique, ses arguments, ses valeurs par défaut et les conditions d’erreur ; elle comprend aussi un document minimal.

Définissez la règle générale de gestion des paragraphes dans le préambule, puis remplacez-la ponctuellement :

```tex
\ParallelSetup{paragraph-flow=breakable}
\ParallelParagraph{explanation}{Left paragraph.}{Right paragraph.}
\ParallelParagraph[flow=keep]{short}{Keep this pair together.}{Keep this pair together.}
```

`ParallelText` forme toujours une unité indivisible ; `ParallelProse` autorise explicitement la continuation. Une unité à conserver d’un seul tenant qui dépasse la taille disponible provoque une erreur explicite. Le moteur ne réduit ni ne tronque son contenu.

## JSON structuré

Depuis le répertoire d’installation de cette compétence :

```sh
python3 scripts/bilingual_pdf.py export examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-project
python3 scripts/bilingual_pdf.py render examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-build
```

`export` crée du LaTeX portable et modifiable. `render` le compile et le vérifie également. Un répertoire de sortie existant est refusé. Ajoutez `--mode left` ou `--mode right` pour une édition dans la seule langue choisie.

Utilisez le [JSON Schema](schemas/document.schema.json) indépendant et la [référence des champs](references/input.md). `layout.paragraph_flow` prend la valeur `keep` ou `breakable` ; le champ `flow` d’un paragraphe la remplace localement. `atomic` reste un alias de compatibilité pour `keep`. Des contrôles à l’exécution portant sur les identifiants, dimensions, références, polices et chemins d’assets complètent la validation du schéma.

Les chemins d’images doivent se résoudre à l’intérieur du répertoire d’entrée ou du `--asset-root` explicite ; les chemins absolus, traversées de répertoires et sorties par lien symbolique sont refusés. L’adaptateur ne télécharge jamais d’assets ni de dépendances.

## Configurer sans dupliquer la mise en page

La [référence de configuration](references/configuration.md) couvre la géométrie, la reliure, l’apparence du séparateur, les numéros de page, les espacements, les styles, les rôles sémantiques, les couvertures et la navigation. Les valeurs par défaut fonctionnent sans configuration. Ne surchargez que les réglages utiles ou utilisez les points d’extension natifs documentés, en séparant contenu, correspondance langue/police et présentation.

Le tableau JSON aligne les lignes, mais conserve l’ensemble du tableau et de sa légende d’un seul tenant. Les lignes appariées natives peuvent être placées hors de `ParallelKeep` pour permettre des sauts de page entre les lignes. Chaque ligne reste indivisible ; la division automatique d’une ligne et les en-têtes répétés de type longtable ne sont pas proposés.

## Dépendances, contrôles et livraison

Utilisez XeLaTeX, latexmk et les paquets TeX et polices documentés. Consultez la [configuration des langues](references/languages.md) pour la césure française, la composition bidirectionnelle arabe/hébreu, les polices CJK et les séquences mêlant plusieurs écritures. L’import structuré et les contrôles PDF facultatifs utilisent `requirements.txt`, Fontconfig et `kpsewhich`.

Suivez les [critères d’acceptation du rendu](references/acceptance.md) : examinez les pages réelles pour vérifier l’alignement, les continuations, les glyphes, la mise en forme RTL, les éléments coupés, les images, les références et la géométrie d’impression. Les contrôles mécaniques ne prouvent pas la justesse sémantique. Indiquez séparément les contrôles réussis, échoués et non exécutés.

Livrez le PDF, le projet source natif portable et le JSON, s’il a été utilisé. Incluez les assets et licences nécessaires. Le TeX natif et la configuration latexmk exécutent du code ; `-no-shell-escape` n’est pas un bac à sable. Utilisez des sources fiables ou une isolation adaptée. L’écriture verticale, les flottants arbitraires et le contenu verbatim dans les arguments de macros, la découverte native des polices sous Windows et PDF/UA restent hors du périmètre testé.

Le code original, le texte du tutoriel et les schémas sont sous [licence MIT](LICENSE). Les dépendances tierces conservent leurs propres licences. Aucun contenu documentaire privé ne doit figurer dans ces exemples publics.

## De la traduction à la mise en page

Pour traduire une source, utilisez bilingual-translation, installé séparément, afin de préparer un manuscrit bilingue unique et relu. Les paires déjà fournies restent directement utilisables. Le [guide de transmission](references/translation.md) décrit la découverte de la dépendance, les révisions testées et l’import facultatif du format v1. La voie TeX native reste pleinement disponible.
