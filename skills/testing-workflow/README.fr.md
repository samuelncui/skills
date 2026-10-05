# Méthode de test

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Ce skill aide à choisir et maintenir les tests d'une modification, à examiner une régression ou à accélérer une vérification lente. Il privilégie le framework du projet et une portée proportionnée au risque, tout en conservant les contrôles de publication obligatoires.

## Utilisation

Installez `testing-workflow` avec l'installateur de skills de votre environnement, ou copiez son répertoire complet. Il ne dépend pas des skills PDF. Exemples de demandes :

- « Utilise testing-workflow pour tester cette correction du parseur. Conserve un test de régression et vérifie les appelants concernés. »
- « Examine pourquoi cette suite est lente et propose des contrôles moins coûteux sans perdre de couverture utile. »

Fournissez la modification ou le dépôt, les échecs connus, les contrôles obligatoires et les services exclus ou plafonds de coût. Vous obtiendrez une courte définition du périmètre, les tests exécutables nécessaires et un compte rendu distinguant réussite, échec, omission volontaire, blocage et absence d'exécution. La [procédure agent](SKILL.md) et la [référence coût et performance](references/cost-and-performance.md) détaillent la méthode.

## Essayer l'exemple

Lisez le [normaliseur d'étiquettes](examples/tags.py) et ses [tests](examples/test_tags.py). Depuis le répertoire du skill installé, avec Python 3.11 ou ultérieur, sans paquet tiers, exécutez :

```sh
python3 -B -m unittest discover -s examples -p 'test_tags.py' -v
```

Trois méthodes de test couvrent les entrées normales, l'idempotence, le repli de casse Unicode et les entrées refusées. unittest exécute les assertions et renvoie un statut d'échec si nécessaire. Ces exemples pédagogiques ne valident pas votre produit : adaptez leur approche au framework existant.

Les résultats automatisés ne prouvent pas l'exactitude factuelle, linguistique, visuelle ou l'accessibilité. Les services externes, exécutions payantes, publications et évaluations explicitement exclues restent soumis aux autorisations applicables. [Licence MIT](LICENSE).
