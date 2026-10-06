# Study Notes

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Erstellen Sie die Lernwerkzeuge, die Leser tatsächlich brauchen. Wählen Sie erklärende Notizen, eine einheitliche Kurzreferenz, ein kompaktes Stichwortverzeichnis oder einen Entscheidungsbaum, einzeln oder gemeinsam. Manuskripte verwenden natives LaTeX; das Rendering übernimmt der installierte Skill `bilingual-pdf`.

## Vier optionale Formen

| Form | Frage der Leser | Ausgabe |
| --- | --- | --- |
| Notizen | „Was bedeutet das, und wie funktioniert es?“ | `notes.pdf` |
| Einheitliche Kurzreferenz | „Ich erinnere mich an einen Begriff oder eine Aufgabe. Welches Konzept passt dazu?“ | `quick-reference.pdf` |
| Stichwortverzeichnis | „Wo finde ich die relevanten Konzepte?“ | `keyword-index.pdf` |
| Entscheidungsbaum | „Was sollte ich mit meinem jetzigen Wissen als Nächstes tun?“ | `decision-tree.pdf` |

Standardmäßig werden Notizen und Kurzreferenz erstellt. Die Kurzreferenz ordnet kanonische Konzepte, Aliasnamen und Stichwortverweise gemeinsam in einer einzigen sortierten Liste von Stichwörtern an. Leser müssen nicht zwischen einem Stichwortteil und einem Konzeptteil wählen. Ein separates Stichwortheft ist optional und keine verpflichtende zweite Suchstelle.

[![Beispiel für einheitliches Nachschlagen](examples/quick-reference-preview.png)](examples/quick-reference.pdf)

[![Entscheidungsbeispiel von der Frage zur Methode](examples/decision-tree-preview.png)](examples/decision-tree.pdf)

## Ein Lernbeispiel zur eigenen Verwendung

Die [ursprüngliche Lehrquelle](examples/source.md) erklärt, wie man diese vier Formen auswählt und erstellt. Die [Quellenzuordnung](examples/source-map.json), nativen Manuskripte, PDFs und Vorschauen bleiben zusammen unter `examples/`:

- [Notizen](examples/notes.pdf): Erklärungen und durchgearbeitete Auswahlbeispiele
- [Einheitliche Kurzreferenz](examples/quick-reference.pdf): ein gemeinsamer Nachschlagebereich mit gemischten Eintragstypen
- [Stichwortverzeichnis](examples/keyword-index.pdf): kompakte, automatisch erzeugte Verweise
- [Entscheidungsbaum](examples/decision-tree.pdf): natürliche Fragen, Alternativen, Klärungsschritte und Methoden

Die Beispiele erläutern den Skill anhand seines eigenen Gegenstands. Die eigenständige Benutzeranleitung, [Autorenhinweise](references/authoring.md), [native API](references/native-api.md), [Build-Anleitung](references/rendering.md) und [Prüfliste](references/review-release.md) bleiben lesbare Markdown-Dokumente.

## Renderer installieren und auffinden

Installieren Sie sowohl `study-notes` als auch `bilingual-pdf` über Ihren Host. Ermitteln Sie die tatsächlichen Installationsverzeichnisse; die Pfade können unabhängig voneinander sein. Setzen Sie keine benachbarte Installation voraus.

```sh
export BILINGUAL_PDF_SKILL="/path/reported/by/host/bilingual-pdf"
export STUDY_NOTES_SKILL="/path/reported/by/host/study-notes"
```

`bilingual-pdf/assets/paralleltext.sty` verwaltet Geometrie, Schriftarten, Absatzausrichtung, Fortsetzungen, Abbildungen, Rollen, Titelseiten und Rendering-Prüfungen. Die Datei `studytools.sty` dieses Skills ergänzt native Datensätze und Navigation. Sie lädt keine Abhängigkeiten herunter und enthält keinen zweiten Renderer.

Die gemeinsamen Layout-APIs sind in den eigenständigen nativen, Sprach- und Konfigurationsreferenzen des zweisprachigen Skills beschrieben. Native Builds benötigen XeLaTeX, latexmk sowie die dokumentierten Schriftarten und Pakete. Python ist für Repository-/PDF-Qualitätsprüfungen optional; dieser Skill bietet keinen JSON-Manuskriptadapter.

## Nur die gewünschten Formen erstellen

Kopieren Sie `examples/` in ein neues Projekt, behalten Sie die ermittelten Skill-Pfade bei und ersetzen Sie die Lehrmanuskripte durch Inhalte, zu deren Nutzung Sie berechtigt sind. Führen Sie im Projekt Folgendes aus:

```sh
make BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
make PRODUCTS='notes quick-reference keyword-index decision-tree' BILINGUAL_PDF_SKILL="$BILINGUAL_PDF_SKILL" STUDY_NOTES_SKILL="$STUDY_NOTES_SKILL"
```

Der erste Befehl wählt Notizen und Kurzreferenz aus. Erstellen Sie ausgewählte begleitende Notizen vor den Dokumenten, die darauf verweisen. Nicht ausgewählte Begleitdokumente dürfen keine ungültigen externen Links hinterlassen. Halten Sie PDFs zusammen, wenn sie relative dokumentübergreifende Links verwenden; die Unterstützung dafür unterscheidet sich zwischen PDF-Anzeigeprogrammen.

Für eine portable native Übergabe fügen Sie die benötigten Dateien `paralleltext.sty`, `studytools.sty`, `study-tree.tex`, `study-graph-components.tex`, Manuskript- und Konfigurationsdateien sowie Lizenzen bei. Eine Auslieferungskopie ist etwas anderes als die Pflege eines weiteren installierten Renderers. Die [Build-Anleitung](references/rendering.md) enthält direkte latexmk-Befehle und Abhängigkeitsprüfungen.

## Ein gemeinsames Nachschlageregister

Deklarieren Sie kanonische Konzepte einschließlich sinnvoller Untereinträge nur einmal. Erinnerte Wörter, Aliasnamen und Abkürzungen sollen direkt zum genauen Konzept oder Untereintrag führen. Erzeugte Verweise enthalten den passenden Titel oder Kontext und die tatsächliche Zielseite; soweit verfügbar auch die Kennung des Begleitdokuments sowie Abschnitt und Seite.

Die Identität eines Nachschlageeintrags wird ausdrücklich festgelegt und bleibt vom Sortierschlüssel getrennt. Datensätze, die bewusst dieselbe Stichwortgruppe teilen, erscheinen gemeinsam; allein die Normalisierung von Satzzeichen darf keine unterschiedlichen Bedeutungen zusammenführen. Eine Glossardefinition ohne gleichwertige kanonische Erklärung bleibt ein inhaltlicher Eintrag und darf nicht zugunsten eines bloßen „verwandten“ Links entfallen.

Dasselbe native Register erzeugt die einheitliche Kurzreferenz oder ein kompaktes Verzeichnis. Die [nativen Deklarationen](references/native-api.md) erläutern Gruppierung, Aliasnamen, Verweise auf mehrere Ziele, Untereinträge, kurze Kolumnentitel und Navigations-Hooks.

## Fragen, die zu Methoden führen

Eine Entscheidungsfrage bietet natürliche A/B/C-Alternativen und einen ausdrücklichen Pfad für „unbekannt/zu wenig Informationen“. Die Auswahl führt zu sichtbaren IDs und automatisch ermittelten Seitenzahlen. Blätter enthalten ausführbare Methoden, Prüfungen oder Schritte zur Informationsbeschaffung, damit der Baum auch eigenständig nützlich ist.

Normale Entscheidungspfade müssen enden. Bedingte Rücksprünge nach einer Klärung erhalten einen anderen Typ als vorwärtsführende Auswahlmöglichkeiten; eine erforderliche Fortsetzung darf nicht stillschweigend als Endblatt behandelt werden. Fehlende Ziele, versehentliche Zyklen und leere Pfade sind Fehler.

## Lange Absätze und wiederverwendbare Darstellung

Verwenden Sie `ParallelSetup{paragraph-flow=breakable}` mit `ParallelParagraph` und überschreiben Sie die Einstellung bei Bedarf für einzelne Absätze mit `[flow=keep]`. Schließen Sie fortlaufenden Text nicht in eine eigene unteilbare Box ein. Der maßgebliche Renderer unterstützt Fortsetzungen in zweisprachigen und ausgewählten einsprachigen Ausgaben und stellt vor der nächsten Einheit die Ausrichtung wieder her. Ein zu großer zusammenzuhaltender Block führt zu einem Fehler, ohne Inhalt abzuschneiden oder zu verkleinern.

Nachgelagerte Projekte sollten eine getestete Skill-Revision festschreiben und private Inhalte, Metadaten und schlanke Kompatibilitätsadapter im eigenen Projekt behalten. Ergänzen Sie fehlende allgemeine Funktionen im gemeinsamen Renderer, statt einen privaten Layout-Fork zu pflegen.

## Prüfung und Übergabe

Prüfen Sie Quellenabdeckung, Erklärungsqualität, realistische Nachschlagewege, Entscheidungspfade, Links und tatsächliche PDF-Seiten getrennt. Behaupten Sie ohne Belege weder Vollständigkeit noch eine unabhängige Prüfung. Übergeben Sie die ausgewählten PDFs, die Quellenzuordnung und das portable bearbeitbare Projekt; berichten Sie bestandene, fehlgeschlagene und nicht ausgeführte Prüfungen.

Natives TeX und latexmk-Konfigurationen führen Code aus. Deaktiviertes Shell-Escape isoliert den Dateizugriff nicht. Halten Sie private Quellen, Namen, Kennungen und Herkunftsangaben aus öffentlichen Beispielen heraus und holen Sie vor externer Verarbeitung oder Veröffentlichung die erforderliche Autorisierung ein. Originalcode und Inhalte stehen unter der [MIT-Lizenz](LICENSE); Abhängigkeiten behalten ihre eigenen Lizenzen.
