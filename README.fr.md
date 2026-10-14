# Compétences agent pour les documents et le logiciel

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Sept compétences pour la traduction, la mise en page, les supports pédagogiques, la qualité logicielle et l’amélioration des compétences.

## Traduction et documents

- [bilingual-translation](skills/bilingual-translation/README.fr.md): Lit la source entière, enregistre des groupes sémantiques bornés et relit séparément un manuscrit bilingue unique.
- [bilingual-html](skills/bilingual-html/README.fr.md): Produit du HTML responsive et portable à partir de paires fournies, avec ordre logique, RTL, tableaux réels et images partagées.
- [bilingual-pdf](skills/bilingual-pdf/README.fr.md): Met en page des articles, rapports et supports bilingues côte à côte à partir de textes appariés.
- [study-notes](skills/study-notes/README.fr.md): Transforme des sources pédagogiques en notes explicatives, aide-mémoire, index de mots-clés ou arbres de décision.
## Qualité du logiciel et des compétences

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

Installez les répertoires complets des compétences utiles. Des paires déjà fournies nécessitent seulement bilingual-pdf ou bilingual-html ; traduire une source nécessite bilingual-translation. PDF accepte directement le JSONL relu ; HTML utilise son propre JSON de mise en page ou l’importeur de données sémantiques. study-notes dépend de bilingual-pdf. Les trois guides de qualité n’ont pas de dépendance d’exécution propre : les projets testés fournissent leurs outils. Les dépendances sont découvertes via l’hôte, jamais installées automatiquement. Consultez chaque guide pour la configuration et les exemples.

## Conventions du dépôt

Chaque compétence gère son implémentation et sa documentation. Les guides d’utilisation résident dans ses README ; les procédures destinées aux agents, dans SKILL.md. Chaque implémentation partagée a un seul propriétaire. Les dépendances installées sont localisées via l’hôte, sans supposer des répertoires voisins. Les projets utilisateurs doivent fixer une révision testée.

Consultez le [guide de validation](tests/README.md) pour les vérifications reproductibles du dépôt et la distinction entre résultats historiques et actuels. Les exemples sélectionnés restent dans la compétence qui les gère. Excluez tout contenu privé de ce dépôt public ; le traitement externe et la publication nécessitent les autorisations applicables.

Le code original et le contenu des exemples sont sous [licence MIT](LICENSE). Les dépendances conservent [leurs propres licences](THIRD_PARTY_NOTICES.md).
