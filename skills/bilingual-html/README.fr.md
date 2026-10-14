# Bilingual HTML

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Transformez des textes bilingues déjà appariés en un document portable, consultable hors ligne. Les deux langues de chaque passage restent ensemble : deux colonnes sur ordinateur, puis source et cible sur écran étroit. Cette compétence convient aux articles en lecture parallèle, aux instructions et aux supports à consulter dans un navigateur.

Le demandeur fournit les textes correspondants. Cette compétence les conserve et les met en page ; l’extraction des sources, la traduction et le choix des correspondances relèvent du processus appelant.

## Fonctionnalités

- Aligne le début de chaque paire de titres, de paragraphes et d’éléments de liste
- Conserve de véritables lignes et cellules de tableau, avec les deux langues dans chaque cellule et un défilement horizontal au clavier pour les tableaux larges
- Affiche une image commune par figure, accompagnée de légendes et de descriptions alternatives appariées
- Distingue le sens LTR/RTL de chaque langue de l’ordre physique des colonnes sur ordinateur
- Permet de régler les largeurs, espacements, couleurs et familles de polices par langue
- Produit du HTML, du CSS et des ressources locales, sans JavaScript, polices distantes ni serveur d’exécution

## Exemple complet et aperçu

Le tutoriel original anglais/français explique cette compétence en présentant titres, texte courant, listes numérotées ou non, tableau et figure :

- [JSON de mise en page modifiable](examples/tutorial/layout.json)
- [Page HTML complète générée](examples/tutorial/site/index.html), à consulter après avoir téléchargé tout le dossier `site/`
- [Figure originale](examples/tutorial/images/pairs.png) et [manifeste des exemples](examples/MANIFEST.json)

Depuis le répertoire d’installation de cette compétence :

```sh
set -eu
python3 --version
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

Utilisez Python 3.11 ou ultérieur. Le dossier de sortie `page` doit être nouveau et son parent doit exister. Ouvrez directement `page/index.html` dans un navigateur. Aucun serveur ni outil de compilation n’est nécessaire pour le consulter ; le site du dépôt peut afficher le code source plutôt que la page rendue.

## JSON structuré : paires fournies

Rédigez une entrée au format de mise en page version 1 à l’aide de l’[exemple minimal exécutable](references/rendering.md#minimal-structured-example), du [contrat des champs](references/rendering.md#embedded-pair-layout) et du [JSON Schema](schemas/layout.schema.json). Pour adapter le tutoriel complet sans modifier l’exemple fourni :

```sh
set -eu
mkdir html-work
cp examples/tutorial/layout.json html-work/layout.json
cp -R examples/tutorial/images html-work/images
python3 scripts/bilingual_html.py render html-work/layout.json --output html-work/page
```

Modifiez la copie de `layout.json`, en conservant un identifiant unique pour chaque paire de titres, paragraphes, éléments de liste, cellules, légendes et textes alternatifs. Gardez les rôles source/cible stables et définissez explicitement les étiquettes de langue et les directions. Les chemins des images sont relatifs au dossier du JSON.

`render` valide le document et les ressources avant d’écrire `index.html`, `style.css`, `LICENSE` et les images nécessaires. L’entrée reste inchangée. Après une modification, générez dans un autre dossier neuf, par exemple `html-work/page-v2`. Il n’existe ni commande `build` incrémentale ni commande `preflight` séparée. Consultez le [contrat CLI et le cycle de sortie](references/rendering.md#commands-and-output-lifecycle).

## HTML natif : rédaction manuelle de contenu fiable

La page générée est du HTML ordinaire, modifiable. Pour partir de l’exemple complet sans Python :

```sh
set -eu
test ! -e native-page && cp -R examples/tutorial/site native-page
```

Modifiez `native-page/index.html` et `native-page/style.css`, puis rouvrez la page. La [page native minimale et les règles DOM](references/rendering.md#native-html-authoring) montrent comment garder un conteneur `.pair` avec deux enfants source/cible munis de leurs attributs de langue. Réutilisez la feuille de style fournie, la véritable structure des tableaux et les descriptions bilingues des figures.

Cette voie HTML/CSS nécessite une révision manuelle. Le moteur JSON n’importe pas de HTML, ne valide pas les modifications manuelles et ne reconvertit pas fidèlement les balises enrichies en JSON. Choisissez comme source de travail le JSON ou la page native modifiée. Examinez séparément les balises, liens, ressources et comportements ajoutés ; du HTML non fiable peut exécuter du code ou accéder au réseau.

## De la traduction à la mise en page

Pour une source à traduire, repérez d’abord la compétence `bilingual-translation`, installée séparément, via l’hôte et suivez son processus de traduction et de révision. Définissez `TRANSLATION_SKILL` avec le chemin d’installation vérifié. Avec un `master.jsonl` à jour et relu :

```sh
set -eu
python3 "$TRANSLATION_SKILL/scripts/workflow.py" export master.jsonl --output reviewed.json
python3 scripts/bilingual_html.py import-pairs reviewed.json \
  --translation-skill "$TRANSLATION_SKILL" --contract-version 1 --output imported
python3 scripts/bilingual_html.py render imported/layout.json --output translated-page
```

Adaptez les chemins d’entrée au projet et choisissez des destinations nouvelles. La première commande exporte le format d’échange de traduction v1 ; la deuxième le convertit vers le format de mise en page v1 propre au HTML. HTML ne lit pas directement le JSONL. Un JSON d’échange v1 déjà relu permet de commencer à `import-pairs`.

L’import appelle le validateur de traduction sélectionné, refuse les traductions inachevées ou obsolètes et conserve les chaînes, identifiants et ordres. Il produit `layout.json`, les images compatibles copiées et `import-record.json`. Gardez le manuscrit JSONL et le fichier d’échange pour l’historique de traduction ; le JSON de mise en page est un dérivé de rendu. L’export réunit les fragments divisés dans leurs paires parentes : HTML ne conserve ni l’alignement interne des fragments ni leurs traces de révision. Voir la [préparation des ressources, la fixation des versions/hachages et les limites du transfert](references/rendering.md#optional-translation-import). Les paires de mise en page fournies n’ont pas besoin de compétence de traduction ; les dépendances manquantes ne sont jamais installées automatiquement.

## Configurer et vérifier

Les valeurs par défaut fonctionnent sans configuration. L’objet facultatif `config` accepte `browser_title`, `desktop_order` et des surcharges ciblées dans `styles`. Par exemple :

```json
{"desktop_order":"target-first","styles":{"column_gap":"2rem","source_weight":1,"target_weight":1.25,"source_font":["Noto Sans","sans-serif"],"target_font":["Noto Naskh Arabic","serif"]}}
```

Placez cet objet dans `config` et adaptez les polices aux langues déclarées. [Toutes les clés, unités et valeurs par défaut](references/rendering.md#styling) sont regroupées dans une référence. L’ordre des colonnes ne modifie que la présentation CSS sur ordinateur ; le DOM et l’affichage mobile restent source puis cible, avec un seuil à 48rem. Les polices doivent être disponibles sur l’appareil de consultation ; elles ne sont ni téléchargées ni intégrées par la compétence.

Avant livraison, suivez la [liste de vérification](references/rendering.md#review-boundaries) :

1. Lisez les deux langues en les comparant aux documents fournis pour vérifier le sens et l’exhaustivité.
2. Ouvrez la page réelle hors ligne, à des largeurs d’ordinateur et d’écran étroit, y compris avec l’ordre inversé et les textes RTL/CJK concernés. Examinez les glyphes, la mise en forme, les retours à la ligne, les cellules longues, les nombres et le zoom du navigateur.
3. Utilisez le clavier pour atteindre et faire défiler les tableaux larges ; examinez les images, légendes et deux descriptions alternatives. Vérifiez les contrastes et les technologies d’assistance nécessaires au public visé.
4. Distinguez les contrôles structurels, la révision linguistique et la révision visuelle/d’accessibilité, en indiquant les échecs et les contrôles non effectués. Une génération réussie ne vaut ni approbation de traduction ni certification d’accessibilité.

## Installation indépendante, dépendances et livraison

Installez le dossier complet `bilingual-html` par la procédure de l’hôte, en conservant `SKILL.md`, scripts, ressources, schémas, références, exemples et `LICENSE`. La compétence fonctionne sans copie du dépôt, outils de maintenance, `bilingual-pdf` ni `bilingual-translation`. Hors du dossier installé, utilisez le chemin découvert du script ; si l’installation est en lecture seule, travaillez dans un dossier de projet accessible en écriture.

La génération et l’import utilisent Python 3.11+ et sa bibliothèque standard. Consulter ou modifier un ensemble natif existant nécessite seulement un navigateur/éditeur de texte et des polices locales adaptées. Seul l’import de traduction exige en plus une compétence de traduction compatible, explicitement découverte.

Livrez tout le dossier de sortie, en préservant les chemins relatifs, avec le JSON ou les sources natives modifiables selon la voie choisie. Conservez dans le projet la provenance de l’import et le manuscrit de traduction utilisés. Ne livrez pas uniquement `index.html` s’il dépend du CSS ou des images associés.

## Limites et sécurité

Le format de mise en page v1 accepte du texte Unicode littéral et des figures PNG/JPEG locales. HTML, Markdown et TeX restent du texte ; le JSON ne propose aucune syntaxe de texte enrichi, formule, hyperlien ou script. Ce n’est ni un outil d’OCR, ni un traducteur, ni un extracteur de mise en page existante. Les styles d’impression sont une aide élémentaire à l’impression du navigateur, sans pagination PDF contrôlée.

Les chemins, tailles et structures des images sont limités ; les URL distantes, traversées de répertoires, liens symboliques et entrées SVG sont refusés. Voir les [contraintes des ressources](references/rendering.md#assets-and-output) et les [dérivés matriciels fidèles de SVG fiables](references/rendering.md#faithful-derivatives-of-trusted-svg-originals). Les contrôles d’en-tête ne décodent pas entièrement les images. Vérifiez le résultat réel dans le navigateur ; quelques exemples linguistiques ne prouvent pas une prise en charge universelle ni la conformité d’accessibilité.

La [procédure pour l’agent](SKILL.md) résume les étapes. Le code, la documentation et les exemples originaux sont sous [licence MIT](LICENSE) ; conservez les licences des ressources ajoutées et excluez les contenus privés des exemples publics.
