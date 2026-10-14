# Bilingual HTML

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Erstellen Sie aus bereits zugeordneten zweisprachigen Texten ein portables Offline-Dokument. Beide Sprachen jedes Abschnitts bleiben zusammen: auf dem Desktop in zwei Spalten, auf schmalen Bildschirmen zuerst der Ausgangstext, dann der Zieltext. Geeignet für parallel gelesene Artikel, Anleitungen und Handouts im Browser.

Der Aufrufer liefert die zusammengehörigen Texte. Dieser Skill erhält ihren Wortlaut und gestaltet sie; Quellenextraktion, Übersetzung und die Entscheidung über inhaltliche Entsprechungen gehören zum aufrufenden Arbeitsablauf.

## Funktionen

- Richtet die Anfänge zusammengehöriger Überschriften, Absätze und Listeneinträge aus
- Erhält echte Tabellenzeilen und -zellen mit beiden Sprachen in jeder Zelle; breite Tabellen lassen sich per Tastatur horizontal scrollen
- Zeigt pro Abbildung ein gemeinsames Bild mit zweisprachigen Beschriftungen und Alternativbeschreibungen
- Trennt die LTR-/RTL-Richtung jeder Sprache von der physischen Spaltenreihenfolge auf dem Desktop
- Bietet konfigurierbare Breiten, Abstände, Farben und sprachabhängige Schriftfamilien
- Erzeugt HTML, CSS und lokale Dateien ohne JavaScript, externe Schriftarten oder Laufzeitserver

## Vollständiges Beispiel und Vorschau

Das originale englisch-französische Tutorial erklärt diesen Skill und zeigt dabei Überschriften, Fließtext, nummerierte und unnummerierte Listen, eine Tabelle und eine Abbildung:

- [Bearbeitbares Layout-JSON](examples/tutorial/layout.json)
- [Vollständig erzeugte HTML-Seite](examples/tutorial/site/index.html), nach dem Herunterladen des gesamten Verzeichnisses `site/` im Browser nutzbar
- [Originalabbildung](examples/tutorial/images/pairs.png) und [Beispielmanifest](examples/MANIFEST.json)

Führen Sie im Installationsverzeichnis dieses Skills Folgendes aus:

```sh
set -eu
python3 --version
python3 scripts/bilingual_html.py render examples/tutorial/layout.json --output page
```

Verwenden Sie Python 3.11 oder neuer. Das Ausgabeverzeichnis `page` muss neu sein; sein übergeordnetes Verzeichnis muss existieren. Öffnen Sie `page/index.html` direkt im Browser. Zum Betrachten sind weder Server noch Build-Werkzeug nötig. Die Repository-Website zeigt möglicherweise den HTML-Quelltext statt der gerenderten Seite an.

## Strukturiertes JSON: bereitgestellte Textpaare

Erstellen Sie ein Layout mit eingebetteten Textpaaren anhand des [ausführbaren Minimalbeispiels](references/rendering.md#minimal-structured-example), des [Feldvertrags](references/rendering.md#embedded-pair-layout) und des [JSON Schema](schemas/layout.schema.json). So passen Sie das vollständige Tutorial an und erhalten das mitgelieferte Original:

```sh
set -eu
mkdir html-work
cp examples/tutorial/layout.json html-work/layout.json
cp -R examples/tutorial/images html-work/images
python3 scripts/bilingual_html.py render html-work/layout.json --output html-work/page
```

Bearbeiten Sie die kopierte `layout.json`. Jede Überschrift, jeder Absatz und Listeneintrag, jede Tabellenzelle, Beschriftung und Alternativtext-Paarung braucht eine eindeutige ID. Behalten Sie Quell- und Zielrollen bei und setzen Sie Sprachkennungen und Schreibrichtungen ausdrücklich. Bildpfade beziehen sich auf das Verzeichnis der JSON-Datei.

`render` prüft Dokument und Dateien vor dem Schreiben von `index.html`, `style.css`, `LICENSE` und benötigten Bildern. Die Eingabe bleibt unverändert. Verwenden Sie nach Änderungen ein weiteres neues Verzeichnis, etwa `html-work/page-v2`. Es gibt weder einen inkrementellen `build`- noch einen separaten `preflight`-Befehl. Siehe [CLI und Ausgabeablauf](references/rendering.md#commands-and-output-lifecycle).

## Natives HTML: vertrauenswürdige manuelle Bearbeitung

Die erzeugte Seite besteht aus gewöhnlichem, bearbeitbarem HTML. Das vollständige Beispiel lässt sich ohne Python übernehmen:

```sh
set -eu
test ! -e native-page && cp -R examples/tutorial/site native-page
```

Bearbeiten Sie `native-page/index.html` und `native-page/style.css` und öffnen Sie die Seite erneut. Die [minimale native Seite und DOM-Regeln](references/rendering.md#native-html-authoring) zeigen, wie ein `.pair`-Container Quell- und Zielkinder mit Sprachkennungen zusammenhält. Verwenden Sie das mitgelieferte Stylesheet, echte Tabellenstrukturen und zweisprachige Bildbeschreibungen weiter.

Dieser HTML-/CSS-Weg erfordert manuelle Prüfung. Der JSON-Renderer importiert kein HTML, prüft keine manuellen Änderungen und kann reichhaltiges Markup nicht verlustfrei in JSON zurückführen. Wählen Sie entweder JSON oder die bearbeitete native Seite als redaktionelle Quelle. Prüfen Sie zusätzliche Auszeichnungen, Links, Dateien und Funktionen gesondert; nicht vertrauenswürdiges HTML kann Code ausführen oder auf das Netzwerk zugreifen.

## Von der Übersetzung zum Layout

Ermitteln Sie für zu übersetzende Quellen zunächst den separat installierten Skill `bilingual-translation` über den Host und folgen Sie dessen Übersetzungs- und Prüfablauf. Setzen Sie `TRANSLATION_SKILL` auf das bestätigte Installationsverzeichnis. Mit einer aktuellen, geprüften `master.jsonl`:

```sh
set -eu
python3 "$TRANSLATION_SKILL/scripts/workflow.py" export master.jsonl --output reviewed.json
python3 scripts/bilingual_html.py import-pairs reviewed.json \
  --translation-skill "$TRANSLATION_SKILL" --output imported
python3 scripts/bilingual_html.py render imported/layout.json --output translated-page
```

Passen Sie Eingabepfade an das Projekt an und wählen Sie neue Ausgabeziele. Der erste Befehl exportiert das Übersetzungsaustauschformat; der zweite überführt es in HTMLs eigenständiges Layoutformat. HTML liest JSONL nicht direkt ein. Bei bereits geprüftem Austausch-JSON können Sie mit `import-pairs` beginnen.

Der Import ruft den gewählten Übersetzungsvalidator auf, weist unfertige oder veraltete Zieltexte zurück und erhält Zeichenfolgen, IDs und Reihenfolge. Er erzeugt `layout.json`, kopierte unterstützte Bilder und `import-record.json`. Bewahren Sie JSONL-Manuskript und Austauschdatei für die Übersetzungshistorie auf; Layout-JSON ist eine abgeleitete Darstellungsdatei. Der Export verbindet aufgeteilte Abschnitte wieder zu ihren übergeordneten Paaren. HTML erhält daher weder die Ausrichtung einzelner Teilstücke noch deren Prüfprotokolle. Siehe [Dateivorbereitung, Versions-/Hashbindung und Übergabegrenzen](references/rendering.md#optional-translation-import). Vorhandene Layout-Textpaare benötigen keinen Übersetzungs-Skill. Fehlende Abhängigkeiten werden nie automatisch installiert.

## Konfiguration und Prüfung

Die Standardwerte funktionieren ohne zusätzliche Einrichtung. Das optionale Objekt `config` enthält `browser_title`, `desktop_order` und gezielte Überschreibungen unter `styles`. Beispiel:

```json
{"desktop_order":"target-first","styles":{"column_gap":"2rem","source_weight":1,"target_weight":1.25,"source_font":["Noto Sans","sans-serif"],"target_font":["Noto Naskh Arabic","serif"]}}
```

Setzen Sie dieses Objekt unter `config` ein und passen Sie die Schriften an die angegebenen Sprachen an. [Alle Schlüssel, Einheiten und Standardwerte](references/rendering.md#styling) stehen in einer gemeinsamen Referenz. Die Spaltenreihenfolge ändert nur die Desktop-Darstellung per CSS; DOM und mobile Ansicht behalten Quelle vor Ziel bei. Der Umschaltpunkt liegt bei 48rem. Schriften müssen auf dem Anzeigegerät vorhanden sein; der Skill lädt sie weder herunter noch bettet er sie ein.

Gehen Sie vor der Übergabe die [Prüfliste](references/rendering.md#review-boundaries) durch:

1. Lesen Sie beide Sprachen im Vergleich zu den bereitgestellten Unterlagen auf Vollständigkeit und Bedeutung.
2. Öffnen Sie die tatsächliche Seite offline bei Desktop- und schmalen Breiten, auch mit umgekehrter Spaltenfolge und relevanten RTL-/CJK-Texten. Prüfen Sie Glyphen, Schriftformung, Umbrüche, lange Zellen, Zahlen und Browserzoom.
3. Fokussieren und scrollen Sie breite Tabellen per Tastatur. Prüfen Sie Bilder, Beschriftungen und beide Alternativbeschreibungen sowie Kontrast und benötigte assistive Technik für die Zielgruppe.
4. Berichten Sie Strukturtests, sprachliche sowie visuelle/Barrierefreiheitsprüfung getrennt, einschließlich Fehlern und nicht durchgeführten Prüfungen. Erfolgreiches Rendering ist weder Übersetzungsfreigabe noch Barrierefreiheitszertifizierung.

## Unabhängige Installation, Abhängigkeiten und Übergabe

Installieren Sie das gesamte Verzeichnis `bilingual-html` über den Installationsablauf Ihres Hosts. Erhalten Sie `SKILL.md`, Skripte, Assets, Schemas, Referenzen, Beispiele und `LICENSE`. Der Skill funktioniert ohne Repository-Checkout, Wartungswerkzeuge, `bilingual-pdf` oder `bilingual-translation`. Nutzen Sie außerhalb des Installationsverzeichnisses den ermittelten Skriptpfad. Bei schreibgeschützter Installation arbeiten Sie in einem beschreibbaren Projektverzeichnis.

Rendering und Import benötigen Python 3.11+ mit Standardbibliothek. Zum Betrachten oder manuellen Bearbeiten vorhandener nativer Dateien genügen Browser/Texteditor und passende lokale Schriften. Nur der Übersetzungsimport erfordert zusätzlich einen ausdrücklich ermittelten kompatiblen Übersetzungs-Skill.

Geben Sie das vollständige Ausgabeverzeichnis mit unveränderten relativen Pfaden und gegebenenfalls bearbeitbarem JSON oder nativen Quellen weiter. Bewahren Sie Importnachweis und Übersetzungsmanuskript im Projekt auf, wenn sie verwendet wurden. Liefern Sie nicht nur `index.html`, wenn CSS oder Bilder dazugehören.

## Grenzen und Sicherheit

Das Layoutformat akzeptiert wörtlichen Unicode-Text und lokale PNG-/JPEG-Abbildungen. HTML, Markdown und TeX werden als Text angezeigt; JSON bietet keine Syntax für formatierten Text, Gleichungen, Hyperlinks oder Skripte. Der Skill ist weder OCR-Werkzeug noch Übersetzer oder Extraktor bestehender Seitenlayouts. Druck-CSS unterstützt einfaches Drucken im Browser, aber keine kontrollierte PDF-Paginierung.

Bildpfade, Größen und Strukturen sind begrenzt; entfernte URLs, Verzeichnistraversierung, symbolische Links und SVG-Eingaben werden abgewiesen. Siehe [Dateibeschränkungen](references/rendering.md#assets-and-output) und [originalgetreue Rasterableitungen vertrauenswürdiger SVGs](references/rendering.md#faithful-derivatives-of-trusted-svg-originals). Headerprüfungen dekodieren Bilder nicht vollständig. Prüfen Sie die tatsächliche Browserausgabe; wenige Sprachbeispiele belegen keine universelle Sprachunterstützung oder Barrierefreiheitskonformität.

Der [Agentenablauf](SKILL.md) fasst die Schritte zusammen. Code, Dokumentation und originale Beispielmaterialien stehen unter der [MIT-Lizenz](LICENSE). Erhalten Sie die Lizenzen ergänzter Dateien und nehmen Sie keine privaten Inhalte in öffentliche Beispiele auf.
