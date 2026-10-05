# Compétences agent pour PDF bilingues, notes et tests

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Des compétences pour les documents bilingues, les supports d’apprentissage et la vérification logicielle attentive aux coûts.

- [bilingual-pdf](skills/bilingual-pdf/README.fr.md) : aligne les débuts de paragraphes, les lignes de tableau et les éléments de liste dans des colonnes physiques fixes. Les longs paragraphes peuvent se poursuivre sur plusieurs pages ; la paire suivante se réaligne. LaTeX natif et JSON partagent un moteur de rendu, avec des profils de langues LTR, RTL et CJK.
- [study-notes](skills/study-notes/README.fr.md) : produit des notes explicatives, un aide-mémoire unifié, un index de mots-clés ou un arbre de décision. Choisissez une forme ou plusieurs. Les enregistrements LaTeX natifs réutilisent le moteur bilingue installé.
- [testing-workflow](skills/testing-workflow/SKILL.md) : conçoit et maintient les tests automatisés et les benchmarks avec les outils natifs du projet. Regroupe les vérifications et choisit des preuves proportionnées au risque et au coût.

[![Un guide d’utilisation bilingue](skills/bilingual-pdf/examples/en-zh-Hans/preview.png)](skills/bilingual-pdf/examples/en-zh-Hans/output.pdf)

Les exemples expliquent comment utiliser les compétences tout en montrant leur résultat. Sources, PDF et aperçus restent ensemble. Les guides d’utilisation, références de l’API native, documents de configuration et JSON Schema restent des textes lisibles et indépendants.

## Partir de votre tâche

- Vous avez des textes appariés pour un article, un rapport ou un support bilingue côte à côte ? Utilisez `bilingual-pdf` : [LaTeX minimal et compilation](skills/bilingual-pdf/references/latex.md#project-and-build-contract), ou [JSON minimal, vérification préalable et rendu](skills/bilingual-pdf/references/input.md#minimal-input). Les deux produisent des sources modifiables ; vérifiez d’abord les [polices et prérequis linguistiques](skills/bilingual-pdf/references/languages.md).
- Pour transformer des sources pédagogiques en explications ou références navigables, commencez par [study-notes](skills/study-notes/README.fr.md) et installez explicitement sa dépendance de rendu.
- Pour un plan de test, des tests de régression ou des benchmarks logiciels, commencez par [testing-workflow](skills/testing-workflow/SKILL.md).

Le parcours PDF met en page les textes appariés fournis. Il ne couvre pas l’OCR, l’extraction du contenu d’un PDF existant, la traduction automatique ni la conservation de sa mise en page d’origine.

## Installation

Avec le [Skills CLI](https://github.com/vercel-labs/skills) ou un outil d’installation compatible :

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
```

Pour les documents ordinaires en regard, installez uniquement `bilingual-pdf`. `study-notes` en dépend. Vous pouvez aussi copier les répertoires complets des compétences nécessaires vers les emplacements pris en charge par votre hôte. `testing-workflow` est indépendant et ne nécessite aucune des deux compétences PDF.

Recherchez le répertoire d’installation réel de `bilingual-pdf` via l’hôte, puis fournissez-le comme `BILINGUAL_PDF_SKILL` lors de la compilation des documents d’apprentissage. Les compétences ne supposent pas des installations voisines et ne téléchargent jamais automatiquement leurs dépendances. Chaque guide précise les dépendances TeX, les polices et les outils Python facultatifs de contrôle qualité.

## Une seule implémentation, des responsabilités explicites

`bilingual-pdf` gère `paralleltext.sty`, l’import structuré, la mise en page et les contrôles de rendu. `study-notes` ajoute une petite couche native d’enregistrements et de navigation ainsi qu’un processus de rédaction pédagogique ; il n’embarque pas de second moteur. Les projets documentaires qui les utilisent doivent fixer une révision testée et séparer leur propre contenu de leur configuration.

L’agent appelant fournit le contenu et les correspondances sémantiques. L’outil de mise en page contrôle leur position dans le document. Le TeX natif peut exécuter du code ; désactiver shell escape ne crée pas de bac à sable pour le système de fichiers. La publication, le traitement externe et les droits sur les sources demandent des autorisations distinctes.

Consultez le [guide de validation](tests/README.md) pour les tests reproductibles et la distinction entre résultats historiques et actuels. Les PDF d’exemple sélectionnés sont versionnés à côté de leurs sources ; Actions vérifie le dépôt et ne sert pas de canal de livraison des exemples.

Le code original et le contenu des exemples sont sous [licence MIT](LICENSE). Les dépendances conservent [leurs propres licences](THIRD_PARTY_NOTICES.md). Aucune certification universelle de prise en charge des langues, des imprimantes ou de l’accessibilité n’est revendiquée.
