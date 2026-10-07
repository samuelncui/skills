# Bilingual HTML

Transformez des textes déjà appariés en une page HTML portable, consultable hors ligne. Chaque passage conserve ses deux langues ensemble : en colonnes sur ordinateur, puis source et cible sur mobile. Les tableaux, listes, images partagées et légendes bilingues gardent une structure sémantique.

Python 3.11 ou une version ultérieure suffit. Aucun paquet Python tiers ni compétence de traduction n’est nécessaire pour des paires déjà fournies.

```sh
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

Exécutez la commande depuis le dossier de cette compétence. Le dossier de sortie ne doit pas encore exister ; son parent doit exister. Ouvrez `page/index.html` et livrez le dossier complet.

- [Entrée du tutoriel complet](examples/tutorial/layout.json) et [page générée](examples/tutorial/site/index.html)
- [Format, styles, polices, images et vérification](references/rendering.md)
- [Schéma de rendu](schemas/layout.schema.json)
- [Procédure pour l’agent](SKILL.md)

La version 1 affiche du texte littéral et des images PNG/JPEG locales. Elle n’interprète ni HTML, ni Markdown, ni TeX. Les polices sont configurables par langue ; vérifiez les glyphes réels, car un nom de police ne garantit pas la couverture des caractères. Les contrôles de structure ne remplacent pas la révision linguistique, visuelle ou d’accessibilité.

Pour un texte source à traduire, recherchez la compétence `bilingual-translation` installée séparément. Ses paires v1 révisées peuvent être importées avec un chemin `--translation-skill` explicite. Aucune dépendance n’est installée automatiquement. [Importation et fixation de version](references/rendering.md#optional-translation-import).

Le code, la documentation et les exemples originaux sont sous [licence MIT](LICENSE).
