# Agent-Skills für zweisprachige PDFs, Lernnotizen und Tests

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Skills für zweisprachige Dokumente, Lernmaterialien und kostenbewusste Softwareprüfung.

- [bilingual-pdf](skills/bilingual-pdf/README.de.md): Richtet Absatzanfänge, Tabellenzeilen und Listeneinträge in festen physischen Spalten aus. Lange Absätze können auf Wunsch über Seitengrenzen hinweg fortgesetzt werden; das nächste Paar wird wieder ausgerichtet. Natives LaTeX und JSON verwenden denselben Renderer mit Sprachprofilen für LTR, RTL und CJK.
- [study-notes](skills/study-notes/README.de.md): Erstellt erklärende Notizen, eine einheitliche Kurzreferenz, ein Stichwortverzeichnis oder einen Entscheidungsbaum. Eine oder mehrere Formen lassen sich auswählen. Native LaTeX-Datensätze verwenden den installierten zweisprachigen Renderer.
- [testing-workflow](skills/testing-workflow/SKILL.md): Entwirft und pflegt automatisierte Tests und Benchmarks mit dem vorhandenen Testsystem des Projekts. Führt Prüfungen gebündelt aus und wählt den Prüfungsumfang passend zu Risiko und Aufwand.

[![Eine zweisprachige Bedienungsanleitung](skills/bilingual-pdf/examples/en-zh-Hans/preview.png)](skills/bilingual-pdf/examples/en-zh-Hans/output.pdf)

Die Beispiele erläutern die Verwendung der Skills und zeigen zugleich deren Ausgabe. Quelldateien, PDFs und Vorschaubilder bleiben zusammen. Benutzeranleitungen, native API-Referenzen, Konfigurationsdokumentation und JSON Schema bleiben eigenständige, lesbare Texte.

## Mit der Aufgabe beginnen

- Liegen Textpaare für einen zweisprachigen Artikel, Bericht oder ein Handout in nebeneinanderstehenden Spalten vor? Verwenden Sie `bilingual-pdf`: [minimales LaTeX und Build-Befehl](skills/bilingual-pdf/references/latex.md#project-and-build-contract) oder [minimales JSON, Vorprüfung und Rendering](skills/bilingual-pdf/references/input.md#minimal-input). Beide liefern bearbeitbare Quellen. Prüfen Sie zuerst die [Schrift- und Sprachanforderungen](skills/bilingual-pdf/references/languages.md).
- Für Erklärungen oder navigierbare Nachschlagewerke aus Lernquellen beginnen Sie mit [study-notes](skills/study-notes/README.de.md) und installieren dessen Rendering-Abhängigkeit ausdrücklich.
- Für einen Software-Testplan, Regressionstests oder Benchmarks beginnen Sie mit [testing-workflow](skills/testing-workflow/SKILL.md).

Der PDF-Weg setzt bereitgestellte Textpaare. OCR, das Extrahieren vorhandener PDF-Inhalte, automatische Übersetzung und die Beibehaltung des ursprünglichen PDF-Seitenlayouts gehören nicht zu seinem Umfang.

## Installation

Mit der [Skills CLI](https://github.com/vercel-labs/skills) oder einem kompatiblen Installationswerkzeug:

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
```

Für gewöhnliche Paralleltext-Dokumente genügt `bilingual-pdf`. `study-notes` benötigt diesen Skill. Alternativ können Sie die vollständigen Verzeichnisse der benötigten Skills an einen vom Host unterstützten Speicherort kopieren. `testing-workflow` ist unabhängig und benötigt keinen der beiden PDF-Skills.

Ermitteln Sie über den Host das tatsächlich installierte Verzeichnis von `bilingual-pdf` und übergeben Sie es beim Erstellen von Lerndokumenten als `BILINGUAL_PDF_SKILL`. Die Skills setzen keine benachbarten Installationsverzeichnisse voraus und laden Abhängigkeiten niemals automatisch herunter. TeX, Schriftarten und optionale Python-Abhängigkeiten für die Qualitätsprüfung sind in den jeweiligen Anleitungen beschrieben.

## Eine Implementierung, klare Zuständigkeiten

`bilingual-pdf` verwaltet `paralleltext.sty`, den strukturierten Import, das Layout und die Rendering-Prüfungen. `study-notes` ergänzt eine schlanke native Schicht für Datensätze und Navigation sowie einen Arbeitsablauf zum Verfassen von Lernmaterial; es enthält keinen zweiten Renderer. Nachgelagerte Dokumentprojekte sollten eine getestete Revision festschreiben und eigene Inhalte und Konfiguration getrennt halten.

Der aufrufende Agent liefert Inhalte und semantische Zuordnungen. Das Layoutwerkzeug steuert deren Position in der Ausgabe. Natives TeX kann Code ausführen; deaktiviertes Shell-Escape ist keine Dateisystem-Sandbox. Veröffentlichung, externe Verarbeitung und Nutzungsrechte an Quellen erfordern jeweils die passende Autorisierung.

Die [Validierungsanleitung](tests/README.md) beschreibt reproduzierbare Tests und unterscheidet historische von aktuellen Ergebnissen. Ausgewählte Beispiel-PDFs werden neben ihren Quellen versioniert; Actions prüft das Repository und dient nicht als Auslieferungskanal für die Beispiele.

Originalcode und Beispielinhalte stehen unter der [MIT-Lizenz](LICENSE). Abhängigkeiten behalten [ihre eigenen Lizenzen](THIRD_PARTY_NOTICES.md). Eine allgemeingültige Zertifizierung für Sprachen, Drucker oder Barrierefreiheit wird nicht beansprucht.
