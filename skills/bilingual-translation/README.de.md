# Zweisprachige Übersetzung

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)


Neue Übersetzungen nutzen den [zustandsgesteuerten JSONL-Ablauf](references/workflow-v2.md): den vollständigen Ausgangstext lesen und bestätigen, Einheiten über 2048 Unicode-Codepunkte an selbst gewählten Sinnabschnitten teilen und jeweils die aktive Übersetzung speichern, bevor die nächste folgt. Speichern und Prüfen bleiben getrennt; JSON v1 bleibt kompatibel.

Erstellen Sie ein einziges Manuskript mit zugeordnetem Ausgangs- und Zieltext. Lesen Sie zuerst die gesamte relevante Quelle. Übersetzen und prüfen Sie danach jeweils einen vollständigen Absatz oder eine Sinneinheit und speichern Sie den Zieltext im selben Manuskript, bevor Sie fortfahren. Stabile IDs erhalten die Zuordnung; Quelltextänderungen erfordern eine erneute Prüfung.

Installieren Sie das vollständige Verzeichnis mit dem Skill-Installer Ihrer Umgebung. Ein direkt verfasstes zweisprachiges TeX-Manuskript ist gleichwertig. Das Klartext-JSON-Format und der Prüfer mit Python 3.11+ ohne externe Pakete sind optional und von PDF/HTML-Renderern unabhängig.

Beispiel: „Übersetze diesen Leitfaden mit bilingual-translation ins Französische und behalte jeden Absatz und jede Tabellenzelle in einem gemeinsamen zweisprachigen Manuskript.“ Geben Sie Quelle, Zielsprache, Zielgruppe und Terminologie an. Bereits zugeordnete Texte können direkt an einen Renderer gehen.

Siehe [Arbeitsablauf](SKILL.md), [optionalen Formatvertrag](references/contract-v1.md) und [vollständiges originales Englisch–Französisch-Beispiel](references/example-guide.md) mit Quelle, Tabelle und gemeinsamer Abbildung. Im Skill-Verzeichnis ausführen:

```sh
python3 -B scripts/translation_contract.py validate examples/guide/translation.json --ready
```

Der Befehl prüft Struktur, Quelltext-Hashes und die Aktualität dokumentierter Prüfungen. Inhaltliche Genauigkeit erfordert weiterhin einen Vergleich von Quelle und Übersetzung.

[Entwurfsquellen](references/design-provenance.md) · [MIT-Lizenz](LICENSE)
