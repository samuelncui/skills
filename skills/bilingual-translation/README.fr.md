# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Créez un manuscrit bilingue unique qui préserve la source et son alignement. Par défaut, l’agent principal actuel lit toute la source, choisit les coupures sémantiques, enregistre des groupes bornés, puis compare toutes les paires. La relecture indépendante est une étape distincte menée par ce même agent.

Les mises à jour indiquent environ tous les 5 % le nombre terminé et le total par étape, ainsi que la fin et tout recul de la révision après correction.

Les sous-agents peuvent perdre le contexte et créer des incohérences de terminologie, de style ou de détail. Toute délégation exige l’explication de ce risque et votre accord explicite sur son périmètre ; l’urgence seule ne suffit pas. Un accord précis déjà donné dans la demande actuelle n’est pas redemandé.

Installez le répertoire complet. L’outil JSONL exige Python 3.11+ et le verrouillage POSIX, sans paquet externe ni service réseau. Le TeX natif apparié reste une voie équivalente pour les contenus riches que l’importeur Markdown ne représente pas.

Exemple : « Avec bilingual-translation, traduisez ce guide en français en conservant les paragraphes et les cellules dans un manuscrit unique et relu. » Précisez source, langue cible, public et terminologie.

L’entrée agent est scripts/workflow.py. La préparation renvoie des unités complètes totalisant au moins 8192 points de code source, sauf le dernier lot ; toute unité dépassant 2048 doit être découpée avant de poursuivre. Traduction et relecture utilisent chacune des groupes d’au plus 2048 points de code source, sans compter la longueur cible en relecture. Enregistrer et demander le groupe suivant sont deux opérations distinctes. Utilisez une commande indépendante ou transmettez à run du JSONL sur stdin : une opération et sa propre référence par ligne. Un lot contient au plus une opération renvoyant le texte, obligatoirement en dernier. Renvoyez les références sans modification. Pour les coupures, l’agent choisit des fragments source adjacents exacts ; l’outil localise la limite et vérifie les longueurs, sans calcul manuel des positions.

Corrigez par des patchs old/new exacts, lisez la comparaison modifiée, puis acceptez séparément. Revérifiez localement un problème local ; recommencez la relecture complète pour des problèmes étendus ou globaux. Suivez les questions ouvertes avec les todos. L’export exige une relecture complète et actuelle et la résolution des todos, sans contournement pour brouillon.

[Procédure agent](SKILL.md) · [Commandes et limites](references/workflow.md)

Le JSONL relu passe directement au skill bilingual-pdf découvert séparément. HTML utilise son propre JSON de mise en page ou importe le format d’échange sémantique, sans lecture directe du JSONL. Les paires déjà fournies n’exigent pas de nouvelle traduction.

## Échange sémantique

Le [format d’échange sémantique](references/semantic-exchange.md) et l’[exemple anglais–français](references/example-guide.md) décrivent la transmission au moteur de rendu. Utilisez workflow.py export lorsque le consommateur nécessite ce JSON ; le JSONL reste le maître. Les consommateurs valident les documents d’échange avec l’API en lecture seule validate_document de translation_contract.py.

La validation contrôle la structure et l’actualité des attestations de relecture. L’agent vérifie le sens ; l’aspect du PDF se vérifie séparément sur les pages réellement rendues.

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
