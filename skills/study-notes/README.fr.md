# Study Notes

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Créez les outils d’apprentissage dont le lecteur a réellement besoin. Choisissez des notes explicatives, un aide-mémoire unifié, un index compact de mots-clés ou un arbre de décision, seuls ou combinés. Les manuscrits sont en LaTeX natif ; le rendu est assuré par la compétence `bilingual-pdf` installée.

## Quatre formes facultatives

| Forme | Question du lecteur | Sortie |
| --- | --- | --- |
| Notes | « Que signifie ceci et comment cela fonctionne-t-il ? » | `notes.pdf` |
| Aide-mémoire unifié | « Je me souviens d’un terme ou d’une tâche. Quelle est l’idée pertinente ? » | `quick-reference.pdf` |
| Index de mots-clés | « Où se trouvent les concepts pertinents ? » | `keyword-index.pdf` |
| Arbre de décision | « Avec ce que je sais, que dois-je faire ensuite ? » | `decision-tree.pdf` |

La sélection par défaut associe les notes à l’aide-mémoire. Celui-ci entrelace les concepts canoniques, les alias et les renvois par mots-clés dans un seul ensemble trié de vedettes. Le lecteur n’a pas à choisir entre une section de mots-clés et une section de concepts. Un livret séparé de mots-clés est facultatif, et ne constitue pas un second lieu de recherche obligatoire.

[![Exemple de recherche unifiée](examples/quick-reference-preview.png)](examples/quick-reference.pdf)

[![Exemple de décision menant d’une question à une méthode](examples/decision-tree-preview.png)](examples/decision-tree.pdf)

## Un exemple pédagogique fondé sur son propre usage

La [source pédagogique originale](examples/source.md) explique comment choisir et construire ces quatre formes. Sa [carte des sources](examples/source-map.json), les manuscrits natifs, les PDF et les aperçus restent ensemble sous `examples/` :

- [Notes](examples/notes.pdf) : explications et exemples de choix
- [Aide-mémoire unifié](examples/quick-reference.pdf) : un seul espace de recherche aux entrées entrelacées
- [Index de mots-clés](examples/keyword-index.pdf) : renvois compacts générés automatiquement
- [Arbre de décision](examples/decision-tree.pdf) : questions naturelles, options, clarifications et méthodes

Ces exemples présentent la compétence en prenant son propre fonctionnement comme sujet. Le guide d’utilisation indépendant, les [conseils de rédaction](references/authoring.md), l’[API native](references/native-api.md), le [guide de compilation](references/rendering.md) et la [liste de contrôle](references/review-release.md) restent des documents Markdown lisibles.

## Installer et localiser le moteur de rendu

Installez `study-notes` et `bilingual-pdf` via votre hôte. Recherchez leurs répertoires d’installation réels ; leurs chemins peuvent être sans rapport. Ne supposez pas une installation dans des répertoires voisins.

```sh
export BILINGUAL_PDF_SKILL="/path/reported/by/host/bilingual-pdf"
export STUDY_NOTES_SKILL="/path/reported/by/host/study-notes"
```

`bilingual-pdf/assets/paralleltext.sty` gère la géométrie, les polices, l’alignement des paragraphes, leur continuation, les figures, les rôles, les couvertures et les contrôles de rendu. Le fichier `studytools.sty` de cette compétence ajoute les enregistrements natifs et la navigation. Il ne télécharge jamais de dépendances et n’embarque pas de second moteur.

Consultez les références indépendantes de la compétence bilingue sur l’API native, les langues et la configuration pour l’API de mise en page commune. La compilation native nécessite XeLaTeX, latexmk et les polices/paquets documentés. Python est facultatif pour les contrôles qualité du dépôt et des PDF ; cette compétence ne fournit aucun adaptateur de manuscrits JSON.

## Compiler uniquement les formes souhaitées

Copiez `examples/` dans un nouveau projet, conservez les chemins des compétences identifiés et remplacez les manuscrits pédagogiques par du contenu que vous êtes autorisé à utiliser. Depuis ce projet :

```sh
make BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='notes quick-reference keyword-index decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
```

La première commande sélectionne les notes et l’aide-mémoire. Compilez les notes associées sélectionnées avant les documents qui y font référence. L’omission d’un document associé ne doit pas laisser de liens externes cassés. Conservez les PDF ensemble s’ils utilisent des liens relatifs entre documents ; leur prise en charge varie selon le lecteur PDF.

Pour transmettre un projet natif portable, incluez les fichiers nécessaires `paralleltext.sty`, `studytools.sty`, `study-tree.tex`, `study-graph-components.tex`, les manuscrits, les fichiers de configuration et les licences. Une copie de livraison est distincte de la maintenance d’un autre moteur installé. Le [guide de compilation](references/rendering.md) donne les commandes latexmk directes et les contrôles des dépendances.

## Un registre de recherche unique

Déclarez les concepts canoniques une seule fois, avec des sous-entrées pertinentes. Orientez les mots dont le lecteur se souvient, les alias et les acronymes directement vers le concept ou la sous-entrée exacte. Les références générées indiquent le titre ou le contexte pertinent et la page réelle de destination, ainsi que l’identité du document associé et sa section/page lorsque ces informations sont disponibles.

L’identité de recherche est explicite et distincte de la clé de tri. Les enregistrements qui partagent délibérément un groupe de vedettes apparaissent ensemble ; la seule normalisation de la ponctuation ne doit pas fusionner des sens différents. Une définition de glossaire sans explication canonique équivalente reste un contenu à part entière et ne doit pas être supprimée au profit d’un simple lien « connexe ».

Le même registre natif produit l’aide-mémoire unifié ou un index compact. Consultez les [déclarations natives](references/native-api.md) pour les regroupements, alias, renvois vers plusieurs cibles, sous-entrées, titres courants courts et points d’extension de navigation.

## Des questions qui mènent à des méthodes

Utilisez les [composants natifs de graphe](references/graph-components.md) pour poser des questions naturelles avec leurs prérequis sur place. Testez A/B/C dans l’ordre et retenez la première condition satisfaite. Les références N1, N2, … générées restent distinctes des clés sémantiques internes. Chaque solution explique le raisonnement, les opérations et les vérifications nécessaires.

Résolvez les informations manquantes auprès de la question lorsque c’est possible. Une branche dédiée convient à une collecte substantielle, mais n’est pas obligatoire partout. Une boucle réelle précise l’état transmis, la progression et la condition de sortie. Le moteur commun conserve les questions en bleu et les solutions en vert.

## Paragraphes longs et présentation réutilisable

Utilisez `ParallelSetup{paragraph-flow=breakable}` avec `ParallelParagraph` et remplacez ce choix par `[flow=keep]` pour certains paragraphes si nécessaire. N’enfermez pas un texte continu dans une boîte privée indivisible. Le moteur de référence prend en charge la continuation des versions bilingues et dans une seule langue, puis rétablit l’alignement avant l’unité suivante. Un bloc indivisible trop grand provoque une erreur, sans tronquer ni réduire le contenu.

Les projets utilisateurs doivent fixer une révision testée de la compétence et conserver dans leur propre projet le contenu privé, les métadonnées et les adaptateurs légers de compatibilité. Ajoutez les capacités génériques manquantes au moteur partagé plutôt que de maintenir une variante privée de mise en page.

## Relecture et livraison

Vérifiez séparément la couverture des sources, la qualité des explications, les parcours de recherche réalistes, les chemins de décision, les liens et les pages PDF réelles. Ne revendiquez ni exhaustivité ni audit indépendant sans preuves. Livrez les PDF sélectionnés, la carte des sources et le projet portable modifiable ; indiquez les contrôles réussis, échoués et non exécutés.

Le TeX natif et la configuration latexmk exécutent du code. Désactiver shell escape n’isole pas l’accès aux fichiers. Excluez des exemples publics les sources privées, noms, identifiants et données de provenance, et obtenez les autorisations applicables avant un traitement externe ou une publication. Le code et le contenu originaux sont sous [licence MIT](LICENSE) ; les dépendances conservent leurs propres licences.
