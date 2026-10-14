# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Erstellen Sie ein einziges, quelltexttreues Übersetzungsmanuskript mit stabiler Zuordnung. Der Agent liest die gesamte Quelle, wählt semantische Trennstellen, speichert begrenzte Gruppen und prüft anschließend sämtliche Quell-/Zielpaare in einem getrennten Durchgang.

Installieren Sie das vollständige Skill-Verzeichnis. Das JSONL-Werkzeug benötigt Python 3.11+ und POSIX-Dateisperren, aber keine externen Pakete oder Netzwerkdienste. Für Inhalte außerhalb des Markdown-Importers bleibt natives zweisprachiges TeX ein gleichberechtigter Weg.

Beispiel: „Übersetze diesen Leitfaden mit bilingual-translation ins Französische und erhalte Absätze und Tabellenzellen in einem einzigen geprüften Manuskript.“ Geben Sie Quelle, Zielsprache, Zielgruppe und Terminologie an.

Der Agent-Einstieg ist scripts/workflow.py. prepare liest und initialisiert die Quelle; translate liefert Gruppen mit insgesamt höchstens 2048 Quell-Codepoints; review dokumentiert einen unabhängigen vollständigen Vergleich. Speichern und Bestätigen liefern die nächste Gruppe. Kurze Referenzen ersetzen manuell kopierte Hashes; Revisions-, Hash- und Wiederholungsprüfungen bleiben intern erhalten. Nur geänderte Paare werden erneut geprüft.

[Agent-Ablauf](SKILL.md) · [Befehle und Grenzen](references/workflow-v2.md)

Geprüftes JSONL geht direkt an den separat ermittelten Skill bilingual-pdf. HTML verwendet sein eigenes Layout-JSON oder den bisherigen v1-Import und liest JSONL nicht direkt. Vorhandene Textpaare müssen nicht erneut übersetzt werden.

## Bestehende v1-Kompatibilität

Der [v1-Vertrag](references/contract-v1.md), das [englisch-französische Beispiel](references/example-guide.md) und die translation_contract.py-APIs bleiben erhalten, getrennt vom kontrollierten JSONL-Ablauf. Nutzen Sie workflow.py export nur für Verbraucher, die v1-JSON benötigen; JSONL bleibt das Hauptmanuskript.

Die Validierung prüft Struktur und Aktualität dokumentierter Prüfungen. Die Bedeutung prüft der Agent; das PDF-Erscheinungsbild wird separat an tatsächlich gerenderten Seiten geprüft.

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
