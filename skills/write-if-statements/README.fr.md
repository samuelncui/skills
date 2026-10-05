# Comment écrire une instruction if

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Cette compétence aide à écrire une nouvelle logique conditionnelle, à relire une fonction riche en branches ou à simplifier du code sans changer son comportement. Le but est de rendre les décisions lisibles, pas de réduire le nombre de `if`.

## Installation et utilisation

Utilisez Skills CLI ou un installateur compatible avec votre hôte :

```sh
npx skills add samuelncui/skills --skill write-if-statements
```

Conservez le dossier complet, avec sa licence, ses références et ses exemples. La lecture du guide ne nécessite aucune autre compétence ni installation de Python ; Python 3 sert uniquement à exécuter les exemples.

Demandez à votre assistant de programmation d'utiliser `$write-if-statements`, ou sélectionnez cette compétence dans votre hôte. Fournissez le code concerné, ses appelants, le comportement attendu et la commande de test disponible. Exemples de demandes :

- « Écris la condition de nouvelle tentative de ce client : uniquement après une erreur transitoire et s'il reste des tentatives. Reste simple et teste les limites. »
- « Relis cette fonction de routage. Une table de correspondance préserverait-elle la priorité à la première condition satisfaite et les traitements évités ? Ne modifie rien pour l'instant. »
- « Réduis l'imbrication de ce gestionnaire sans changer les valeurs de retour, les exceptions ni la libération des ressources. Ajoute des tests de régression et lance les tests concernés. »

Le résultat attendu est une revue ou un correctif au périmètre défini, les raisons du choix de structure et les résultats des tests avec leurs limites. Une branche simple et claire peut rester telle quelle. Une correction de bug présumé doit être distinguée d'une refactorisation à comportement constant.

## Essayer les exemples

Lisez l'[implémentation](examples/conditionals.py) avec ses [tests](examples/test_conditionals.py). Depuis le dossier de cette compétence :

```sh
python3 -B -m unittest discover -s examples -p 'test_conditionals.py' -v
```

Sept méthodes de test vérifient les résultats et le nettoyage des clauses de garde, la propagation des exceptions, les règles ordonnées qui se chevauchent, les prédicats non évalués, l'exécution du seul gestionnaire sélectionné et une conjonction simple à conserver. Elles utilisent uniquement la bibliothèque standard et vérifient ces exemples pédagogiques, pas votre application.

## Limites et références

Une chaîne de conditions ordonnées n'est pas forcément équivalente à un dictionnaire. Déplacer une décision peut changer le moment des traitements ou des exceptions et l'état observé. Consultez les [pièges sémantiques et sources primaires](references/semantic-traps.md) ; [SKILL.md](SKILL.md) décrit le processus destiné à l'agent.

Les textes et exemples rédigés indépendamment sont couverts par la [licence MIT](LICENSE) incluse. Les œuvres externes liées conservent leurs propres droits.
