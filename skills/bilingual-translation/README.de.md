# Bilingual translation

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Erstellen Sie ein einziges, quelltexttreues Übersetzungsmanuskript mit stabiler Zuordnung. Standardmäßig liest der aktuelle Hauptagent die gesamte Quelle, wählt semantische Trennstellen, speichert begrenzte Gruppen und prüft anschließend sämtliche Textpaare. Die unabhängige Prüfung ist ein eigener Lesedurchgang desselben Agenten.

Fortschrittsmeldungen nennen etwa alle 5 % den erledigten Anteil und die Gesamtzahl je Phase, einschließlich Abschluss und Rückschritten bei der Prüfung nach Korrekturen.

Unteragenten können Kontext verlieren und uneinheitliche Terminologie, Stil oder Details erzeugen. Eine Delegation erfordert die Erläuterung dieses Risikos und Ihre ausdrückliche Zustimmung zum Umfang; Dringlichkeit allein reicht nicht. Eine konkrete Zustimmung in der aktuellen Anfrage muss nicht erneut eingeholt werden.

Installieren Sie das vollständige Skill-Verzeichnis. Das JSONL-Werkzeug benötigt Python 3.11+ und POSIX-Dateisperren, aber keine externen Pakete oder Netzwerkdienste. Für Inhalte außerhalb des Markdown-Importers bleibt natives zweisprachiges TeX ein gleichberechtigter Weg.

Beispiel: „Übersetze diesen Leitfaden mit bilingual-translation ins Französische und erhalte Absätze und Tabellenzellen in einem einzigen geprüften Manuskript.“ Geben Sie Quelle, Zielsprache, Zielgruppe und Terminologie an.

Der Agent-Einstieg ist scripts/workflow.py. Die Vorbereitung liefert vollständige Einheiten mit insgesamt mindestens 8192 Quell-Codepoints; der letzte Stapel darf kleiner sein. Einheiten über 2048 müssen vor dem Weitergehen geteilt werden. Übersetzung und Prüfung verwenden jeweils Gruppen mit höchstens 2048 Quell-Codepoints; die Zieltextlänge zählt bei der Prüfung nicht mit. Speichern und Abrufen der nächsten Gruppe sind getrennte Aktionen. Nutzen Sie einzelne Befehle oder übergeben Sie run JSONL über stdin: eine Aktion mit eigener Referenz pro Zeile. Pro Stapel ist höchstens eine textliefernde Aktion erlaubt, und zwar zuletzt. Geben Sie Referenzen unverändert zurück. Für Trennstellen wählt der Agent exakte benachbarte Quelltextanker; das Werkzeug ermittelt die Position und prüft die Längen, ohne manuelle Offset-Berechnung.

Korrigieren Sie mit exakten old/new-Patches, lesen Sie den geänderten Vergleich und bestätigen Sie ihn erst danach separat. Prüfen Sie lokale Probleme lokal nach; beginnen Sie bei weitreichenden oder globalen Problemen eine vollständige neue Prüfung. Offene Punkte werden als Todos erfasst. Der Export verlangt eine vollständige aktuelle Prüfung und erledigte Todos; es gibt keine Entwurfsumgehung.

[Agent-Ablauf](SKILL.md) · [Befehle und Grenzen](references/workflow.md)

Geprüftes JSONL geht direkt an den separat ermittelten Skill bilingual-pdf. HTML verwendet sein eigenes Layout-JSON oder importiert das semantische Austauschformat und liest JSONL nicht direkt. Vorhandene Textpaare müssen nicht erneut übersetzt werden.

## Semantisches Austauschformat

Das [semantische Austauschformat](references/semantic-exchange.md) und das [englisch-französische Beispiel](references/example-guide.md) beschreiben die Übergabe an den Renderer. Nutzen Sie workflow.py export, wenn ein Verbraucher dieses Austausch-JSON benötigt; JSONL bleibt das Hauptmanuskript. Verbraucher validieren Austauschdokumente mit der schreibgeschützten API validate_document in translation_contract.py.

Die Validierung prüft Struktur und Aktualität dokumentierter Prüfungen. Die Bedeutung prüft der Agent; das PDF-Erscheinungsbild wird separat an tatsächlich gerenderten Seiten geprüft.

[Design provenance](references/design-provenance.md) · [MIT](LICENSE)
