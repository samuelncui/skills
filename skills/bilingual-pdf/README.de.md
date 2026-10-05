# Bilingual PDF

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Platzieren Sie zusammengehörige Inhalte so, dass sie sich gut vergleichen lassen: mit ausgerichteten Absatzanfängen, Listeneinträgen und Tabellenzeilen sowie einer stabilen Trennlinie zwischen den physischen Spalten. Lange Absätze können zusammenbleiben oder über Seiten hinweg weiterlaufen. Natives LaTeX und JSON verwenden dasselbe maßgebliche Layoutpaket.

Der aufrufende Agent liefert die zugeordneten Inhalte. Dieser Skill rendert sie; er wählt keine Übersetzungen aus, schreibt keine Texte um und entscheidet nicht, welche Aussagen einander entsprechen.

## Funktionen

- Richtet jedes Absatzpaar, jeden Listeneintrag und jede Tabellenzeile unabhängig von der Übersetzungslänge aus
- Lässt Absätze über Seitengrenzen weiterlaufen und richtet das folgende Paar erneut aus
- Behandelt die physische Links-/Rechts-Reihenfolge getrennt von der LTR-/RTL-Schreibrichtung
- Rendert ein gemeinsames Bild über die volle Breite mit zweisprachigen Bildunterschriften oder zwei sprachlich angepasste Bilder
- Nutzt gemeinsame Gleichungs- und Abbildungszähler und erzeugt dokumentinterne Seitenverweise
- Unterstützt zweisprachige Ausgaben sowie Ausgaben nur der linken oder rechten Sprache und bietet konfigurierbare Papier- und Bindungsmaße, Titelseiten, Seitenzahlen, semantische Stile und Navigation

[![Absatzausrichtung in der englisch-chinesischen Anleitung](examples/en-zh-Hans/preview.png)](examples/en-zh-Hans/output.pdf)

[![Englisch-hebräisches Beispiel](examples/en-he/preview.png)](examples/en-he/output.pdf)

Dies sind Vorschauen der tatsächlichen Ausgabe. Öffnen Sie die PDFs, um alle Seiten zu sehen. Ein Bild der ersten Seite hilft beim Durchsehen, belegt aber keine vollständige Sichtprüfung.

## Beispiele zum eigenen Gebrauch des Skills

Jede Ausgabe verwendet dieselbe Anleitung, um Absätze, eine Tabelle, Abbildungen, Verweise und eine kurze Formel zu zeigen. Wiederkehrende englische und chinesische Passagen sind in allen Ausgaben jeweils identisch.

| Sprachen | PDF | Strukturierte Quelle | Natives Projekt |
| --- | --- | --- | --- |
| Englisch / Französisch | [output.pdf](examples/en-fr/output.pdf) | [source.json](examples/en-fr/source.json) | [main.tex](examples/en-fr/main.tex) |
| Englisch / Chinesisch | [output.pdf](examples/en-zh-Hans/output.pdf) | [source.json](examples/en-zh-Hans/source.json) | [main.tex](examples/en-zh-Hans/main.tex) |
| Englisch / Arabisch | [output.pdf](examples/en-ar/output.pdf) | [source.json](examples/en-ar/source.json) | [main.tex](examples/en-ar/main.tex) |
| Englisch / Hebräisch | [output.pdf](examples/en-he/output.pdf) | [source.json](examples/en-he/source.json) | [main.tex](examples/en-he/main.tex) |
| Chinesisch / Japanisch | [output.pdf](examples/zh-Hans-ja/output.pdf) | [source.json](examples/zh-Hans-ja/source.json) | [main.tex](examples/zh-Hans-ja/main.tex) |

Nur für Beispiele bestimmte Abbildungen liegen einmalig in `examples/shared/`. Das Laufzeitverzeichnis `assets/` enthält das wiederverwendbare Paket und optionale Profile. Zum Kompilieren der nativen Beispiele werden weder Python noch Repository-Wartungswerkzeuge benötigt.

## Natives LaTeX

Führen Sie diese Befehle aus dem Installationsverzeichnis dieses Skills aus:

```sh
cd examples/en-fr
latexmk -xelatex -interaction=nonstopmode -halt-on-error -latexoption=-no-shell-escape -jobname=output main.tex
```

Kopieren Sie für eigene Dokumente ein vollständiges Beispiel in ein neues Verzeichnis. Behalten Sie die Pfadbeziehungen zu Paket und Bildern bei oder nehmen Sie die benötigten Dateien in ein portables Projekt auf. Bearbeiten Sie `content.tex` und `languages.tex`. Die [vollständige native API-Referenz](references/latex.md) beschreibt alle öffentlichen Befehle, Argumente, Standardwerte und Fehlergrenzen und enthält ein minimales Dokument.

Legen Sie in der Präambel eine globale Absatzregel fest und überschreiben Sie sie bei Bedarf für einzelne Absätze:

```tex
\ParallelSetup{paragraph-flow=breakable}
\ParallelParagraph{explanation}{Left paragraph.}{Right paragraph.}
\ParallelParagraph[flow=keep]{short}{Keep this pair together.}{Keep this pair together.}
```

`ParallelText` bleibt stets eine unteilbare Einheit; `ParallelProse` erlaubt ausdrücklich eine Fortsetzung über Seiten. Eine zu große zusammenzuhaltende Einheit führt zu einem klaren Fehler. Der Renderer verkleinert oder kürzt ihren Inhalt nicht.

## Strukturiertes JSON

Führen Sie diese Befehle aus dem Installationsverzeichnis dieses Skills aus:

```sh
python3 scripts/bilingual_pdf.py export examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-project
python3 scripts/bilingual_pdf.py render examples/en-fr/source.json --asset-root examples/shared --output /path/to/new-build
```

`export` erzeugt portables, bearbeitbares LaTeX. `render` kompiliert und prüft es zusätzlich. Bereits vorhandene Ausgabeverzeichnisse werden abgewiesen. Ergänzen Sie `--mode left` oder `--mode right` für eine Ausgabe in der ausgewählten Sprache.

Verwenden Sie das eigenständige [JSON Schema](schemas/document.schema.json) und die [Feldreferenz](references/input.md). `layout.paragraph_flow` legt `keep` oder `breakable` fest; das Feld `flow` eines Absatzes überschreibt diese Einstellung. `atomic` bleibt als Kompatibilitätsalias für `keep` erhalten. Laufzeitprüfungen für IDs, Abmessungen, Verweise, Schriftarten und Asset-Pfade ergänzen die Schemavalidierung.

Bildpfade müssen innerhalb des Eingabeverzeichnisses oder des ausdrücklich angegebenen `--asset-root` aufgelöst werden. Absolute Pfade, Verzeichnistraversierung und das Verlassen des Bereichs über symbolische Links werden abgewiesen. Der Adapter lädt weder Assets noch Abhängigkeiten herunter.

## Konfigurieren, ohne das Layout abzuspalten

Die [Konfigurationsreferenz](references/configuration.md) behandelt Geometrie, Bindung, Trennlinien, Seitenzahlen, Abstände, Stile, semantische Rollen, Titelseiten und Navigation. Die Standardwerte funktionieren ohne zusätzliche Einrichtung. Überschreiben Sie nur benötigte Einstellungen oder verwenden Sie dokumentierte native Hooks. Halten Sie Inhalt, Sprach-/Schriftzuordnung und Darstellung getrennt.

Die JSON-Tabelle richtet Zeilen aus, hält aber die gesamte Tabelle samt Beschriftung zusammen. Native Zeilenpaare können außerhalb von `ParallelKeep` stehen, damit Seitenumbrüche zwischen den Zeilen möglich sind. Einzelne Zeilen bleiben unteilbar. Automatisches Aufteilen einer Zeile und wiederholte Tabellenköpfe wie bei longtable werden nicht angeboten.

## Abhängigkeiten, Prüfungen und Übergabe

Verwenden Sie XeLaTeX, latexmk und die dokumentierten TeX-Pakete und Schriftarten. Die [Spracheinstellungen](references/languages.md) erläutern französische Silbentrennung, arabischen/hebräischen bidirektionalen Satz, CJK-Schriften und gemischte Schriftsysteme. Der strukturierte Import und optionale PDF-Prüfungen verwenden `requirements.txt`, Fontconfig und `kpsewhich`.

Folgen Sie den [Abnahmekriterien für das Rendering](references/acceptance.md): Prüfen Sie die tatsächlichen Seiten auf Ausrichtung, Fortsetzungen, Glyphen, RTL-Schriftformung, abgeschnittene Inhalte, Bilder, Verweise und Druckgeometrie. Mechanische Prüfungen belegen keine semantische Richtigkeit. Berichten Sie bestandene, fehlgeschlagene und nicht ausgeführte Prüfungen getrennt.

Übergeben Sie das PDF, das portable native Quellprojekt und gegebenenfalls das verwendete JSON. Fügen Sie die benötigten Assets und Lizenzen bei. Natives TeX und latexmk-Konfigurationen führen Code aus; `-no-shell-escape` ist keine Sandbox. Verwenden Sie vertrauenswürdige Quellen oder eine geeignete Isolation. Vertikaler Satz, beliebige Gleitobjekte beziehungsweise Verbatim-Inhalte in Makroargumenten, native Windows-Schrifterkennung und PDF/UA gehören nicht zum getesteten Funktionsumfang.

Originalcode, Tutorialtexte und Diagramme stehen unter der [MIT-Lizenz](LICENSE). Abhängigkeiten Dritter behalten ihre eigenen Lizenzen. Private Dokumentinhalte gehören nicht in diese öffentlichen Beispiele.
