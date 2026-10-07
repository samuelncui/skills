# Compétences agent pour PDF bilingues, notes et tests

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Des compétences pour les documents bilingues, les supports d’apprentissage et la vérification logicielle attentive aux coûts.

- [bilingual-translation](skills/bilingual-translation/README.fr.md): Traduit une unité sémantique à la fois, avec le contexte intégral de la source, dans un manuscrit bilingue unique et relu.
- [bilingual-html](skills/bilingual-html/README.fr.md): Produit du HTML responsive et portable à partir de paires fournies, avec ordre logique, RTL, tableaux réels et images partagées.
- [bilingual-pdf](skills/bilingual-pdf/README.fr.md): Met en page des articles, rapports et supports bilingues côte à côte à partir de textes appariés.
- [study-notes](skills/study-notes/README.fr.md): Transforme des sources pédagogiques en notes explicatives, aide-mémoire, index de mots-clés ou arbres de décision.
- [testing-workflow](skills/testing-workflow/README.fr.md): Conçoit et exécute des tests automatisés et des benchmarks adaptés au coût et au risque des changements logiciels.
- [write-if-statements](skills/write-if-statements/README.fr.md) : Écrire et relire des instructions if lisibles, puis refactoriser les conditions sans changer le comportement.
- [skill-optimization](skills/skill-optimization/README.fr.md): Améliorer les compétences par des essais réalistes en contexte neuf et des corrections ciblées.

## Installation

Avec le [Skills CLI](https://github.com/vercel-labs/skills) ou un outil d’installation compatible :

```sh
npx skills add samuelncui/skills --skill bilingual-translation
npx skills add samuelncui/skills --skill bilingual-html
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
npx skills add samuelncui/skills --skill write-if-statements
npx skills add samuelncui/skills --skill skill-optimization
```

Installez les répertoires complets des compétences nécessaires avec les commandes ci-dessus ou la méthode prise en charge par votre hôte. `study-notes` nécessite aussi `bilingual-pdf` ; `testing-workflow` est indépendant. Les guides liés ci-dessus décrivent la configuration, l’utilisation et les exemples de chaque compétence.

## Conventions du dépôt

Chaque compétence gère son implémentation et sa documentation. Les guides d’utilisation résident dans ses README ; les procédures destinées aux agents, dans SKILL.md. Chaque implémentation partagée a un seul propriétaire. Les dépendances installées sont localisées via l’hôte, sans supposer des répertoires voisins. Les projets utilisateurs doivent fixer une révision testée.

Consultez le [guide de validation](tests/README.md) pour les vérifications reproductibles du dépôt et la distinction entre résultats historiques et actuels. Les exemples sélectionnés restent dans la compétence qui les gère. Excluez tout contenu privé de ce dépôt public ; le traitement externe et la publication nécessitent les autorisations applicables.

Le code original et le contenu des exemples sont sous [licence MIT](LICENSE). Les dépendances conservent [leurs propres licences](THIRD_PARTY_NOTICES.md).

bilingual-pdf et bilingual-html mettent en page les paires fournies de manière indépendante. Installez bilingual-translation séparément pour traduire ou importer le format v1 ; aucune dépendance n’est installée automatiquement.
