# Agent-Skills für zweisprachige PDFs, Lernnotizen und Tests

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Skills für zweisprachige Dokumente, Lernmaterialien und kostenbewusste Softwareprüfung.

- [bilingual-pdf](skills/bilingual-pdf/README.de.md): Erstellt zweisprachige Artikel, Berichte und Handouts in parallelen Spalten aus zugeordneten Textpaaren.
- [study-notes](skills/study-notes/README.de.md): Verwandelt Lernquellen in erklärende Notizen, Kurzreferenzen, Stichwortverzeichnisse oder Entscheidungsbäume.
- [testing-workflow](skills/testing-workflow/SKILL.md): Entwirft und führt automatisierte Tests und Benchmarks passend zu Kosten und Risiken von Softwareänderungen aus.
- [write-if-statements](skills/write-if-statements/README.de.md): Lesbare if-Anweisungen schreiben und prüfen sowie Bedingungslogik ohne Verhaltensänderung refaktorieren.

## Installation

Mit der [Skills CLI](https://github.com/vercel-labs/skills) oder einem kompatiblen Installationswerkzeug:

```sh
npx skills add samuelncui/skills --skill bilingual-pdf
npx skills add samuelncui/skills --skill study-notes
npx skills add samuelncui/skills --skill testing-workflow
npx skills add samuelncui/skills --skill write-if-statements
```

Installieren Sie die vollständigen Verzeichnisse der benötigten Skills mit den obigen Befehlen oder einer vom Host unterstützten Methode. `study-notes` benötigt zusätzlich `bilingual-pdf`; `testing-workflow` ist unabhängig. Einrichtung, Verwendung und Beispiele finden Sie in den oben verlinkten Anleitungen der einzelnen Skills.

## Repository-Konventionen

Jeder Skill verwaltet seine Implementierung und Dokumentation. Benutzeranleitungen stehen in den jeweiligen README-Dateien, Agent-Arbeitsabläufe in SKILL.md. Jede gemeinsam genutzte Implementierung hat genau einen Eigentümer. Installierte Abhängigkeiten werden über den Host gefunden; benachbarte Verzeichnisse werden nicht vorausgesetzt. Nutzende Projekte sollten eine getestete Revision festschreiben.

Die [Validierungsanleitung](tests/README.md) beschreibt reproduzierbare Repository-Prüfungen und unterscheidet historische von aktuellen Ergebnissen. Ausgewählte Beispiele bleiben beim zuständigen Skill. Private Inhalte gehören nicht in dieses öffentliche Repository; externe Verarbeitung und Veröffentlichung erfordern die jeweils nötige Autorisierung.

Originalcode und Beispielinhalte stehen unter der [MIT-Lizenz](LICENSE). Abhängigkeiten behalten [ihre eigenen Lizenzen](THIRD_PARTY_NOTICES.md).
