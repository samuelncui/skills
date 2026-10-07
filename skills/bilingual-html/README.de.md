# Bilingual HTML

Erstellen Sie aus bereits zugeordneten zweisprachigen Texten eine portable HTML-Seite für die Offline-Nutzung. Beide Sprachen eines Abschnitts bleiben zusammen: auf dem Desktop nebeneinander, auf schmalen Bildschirmen zuerst der Ausgangstext, dann der Zieltext. Tabellen, Listen, gemeinsame Bilder und zweisprachige Bildunterschriften behalten ihre semantische Struktur.

Benötigt wird Python 3.11 oder neuer. Für bereits gepaarte Eingaben sind weder zusätzliche Python-Pakete noch eine Übersetzungs-Skill erforderlich.

```sh
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

Führen Sie den Befehl im Verzeichnis dieser Skill aus. Das Ausgabeverzeichnis darf noch nicht existieren; sein übergeordnetes Verzeichnis muss vorhanden sein. Öffnen Sie `page/index.html` und geben Sie das gesamte Verzeichnis weiter.

- [Vollständige Tutorial-Eingabe](examples/tutorial/layout.json) und [erzeugte Seite](examples/tutorial/site/index.html)
- [Format, Gestaltung, Schriften, Bilder und Prüfung](references/rendering.md)
- [Rendering-Schema](schemas/layout.schema.json)
- [Anleitung für den Agenten](SKILL.md)

Version 1 stellt reinen Text und lokale PNG/JPEG-Dateien dar. HTML, Markdown und TeX werden nicht interpretiert. Schriftfamilien lassen sich je Sprache festlegen. Prüfen Sie die tatsächlichen Schriftzeichen, denn ein Schriftname garantiert keine vollständige Zeichenabdeckung. Strukturtests ersetzen weder sprachliche und visuelle Prüfungen noch die Prüfung der Barrierefreiheit.

Für zu übersetzende Ausgangstexte suchen Sie über die Skill-Erkennung des Hosts nach der separat installierten Skill `bilingual-translation`. Geprüfte v1-Textpaare lassen sich mit einem expliziten `--translation-skill`-Pfad importieren. Abhängigkeiten werden nicht automatisch installiert. [Import und Versionsbindung](references/rendering.md#optional-translation-import).

Code, Dokumentation und eigene Beispielmaterialien stehen unter der [MIT-Lizenz](LICENSE).
