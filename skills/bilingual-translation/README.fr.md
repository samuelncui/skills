# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Créez un manuscrit bilingue unique qui préserve la source et son alignement. Par défaut, l’agent principal actuel lit toute la source, choisit les coupures sémantiques, enregistre des groupes bornés, puis compare toutes les paires. La relecture indépendante est une étape distincte menée par ce même agent.

Les sous-agents peuvent perdre le contexte et créer des incohérences de terminologie, de style ou de détail. Toute délégation exige l’explication de ce risque et votre accord explicite sur son périmètre ; l’urgence seule ne suffit pas. Un accord précis déjà donné dans la demande actuelle n’est pas redemandé.

Installez le répertoire complet. L’outil JSONL exige Python 3.11+ et le verrouillage POSIX, sans paquet externe ni service réseau. Le TeX natif apparié reste une voie équivalente pour les contenus riches que l’importeur Markdown ne représente pas.

Exemple : « Avec bilingual-translation, traduisez ce guide en français en conservant les paragraphes et les cellules dans un manuscrit unique et relu. » Précisez source, langue cible, public et terminologie.

L’entrée agent est scripts/workflow.py. prepare lit et initialise la source ; translate distribue des groupes totalisant au plus 2048 points de code source ; review enregistre une comparaison complète et indépendante. Enregistrer ou accepter renvoie le groupe suivant. Des références courtes remplacent la copie manuelle des empreintes ; les contrôles de révision, d’empreinte et de répétition restent internes. Seules les paires modifiées sont relues à nouveau.

[Procédure agent](SKILL.md) · [Commandes et limites](references/workflow-v2.md)

Le JSONL relu passe directement au skill bilingual-pdf découvert séparément. HTML utilise son propre JSON de mise en page ou l’import v1 historique, sans lecture directe du JSONL. Les paires déjà fournies n’exigent pas de nouvelle traduction.

## Compatibilité v1 historique

Le [contrat v1](references/contract-v1.md), l’[exemple anglais–français](references/example-guide.md) et les API translation_contract.py restent disponibles, séparément du parcours JSONL contrôlé. Utilisez workflow.py export seulement si le consommateur nécessite du JSON v1 ; le JSONL reste le maître.

La validation contrôle la structure et l’actualité des attestations de relecture. L’agent vérifie le sens ; l’aspect du PDF se vérifie séparément sur les pages réellement rendues.

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
