# Traduction bilingue

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)


Les nouvelles traductions suivent le [flux JSONL contrôlé](references/workflow-v2.md) : lire et confirmer la source entière, choisir des limites sémantiques pour les unités de plus de 2048 points de code Unicode, puis enregistrer chaque traduction avant de passer à la suivante. Enregistrement et révision sont distincts ; le JSON v1 reste compatible.

Créez un seul manuscrit appariant source et traduction. Lisez d’abord toute la source concernée, puis traduisez et vérifiez un paragraphe complet ou une unité de sens à la fois. Enregistrez le résultat dans le même manuscrit avant de poursuivre. Des identifiants stables maintiennent l’alignement ; toute modification de la source impose une nouvelle vérification.

Installez le répertoire complet avec l’installateur de compétences de votre environnement. Le manuscrit TeX bilingue est une voie à part entière. Le JSON en texte brut et son validateur Python 3.11+ sans dépendances externes sont facultatifs et indépendants des moteurs PDF/HTML.

Exemple : « Utilise bilingual-translation pour traduire ce guide en français en conservant chaque paragraphe et chaque cellule dans un seul manuscrit bilingue. » Fournissez la source, la langue cible, le public et les consignes terminologiques. Un texte déjà apparié peut aller directement au moteur de rendu.

Consultez le [flux de travail](SKILL.md), le [contrat facultatif](references/contract-v1.md) et l’[exemple original complet anglais–français](references/example-guide.md), avec source, tableau et figure partagée. Depuis le répertoire de la compétence :

```sh
python3 -B scripts/translation_contract.py validate examples/guide/translation.json --ready
```

La commande contrôle structure, empreintes de la source et actualité des vérifications enregistrées. La justesse du sens demande toujours une lecture comparée.

[Origine de la conception](references/design-provenance.md) · [Licence MIT](LICENSE)
