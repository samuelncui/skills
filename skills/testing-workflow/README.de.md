# Test-Workflow

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Dieser Skill hilft, Tests für Codeänderungen auszuwählen und zu pflegen, Regressionen zu untersuchen oder langsame Prüfabläufe zu verbessern. Er bevorzugt das vorhandene Testframework und einen dem Risiko angemessenen Prüfumfang. Verbindliche Freigabeprüfungen bleiben erhalten.

## Verwendung

Installieren Sie `testing-workflow` mit dem Skill-Installer Ihrer Umgebung oder kopieren Sie das vollständige Verzeichnis. Der Skill benötigt keine PDF-Skills. Beispielanfragen:

- „Teste diese Parser-Korrektur mit testing-workflow. Ergänze einen Regressionstest und prüfe betroffene Aufrufer.“
- „Untersuche, warum diese Testsuite langsam ist, und schlage günstigere Prüfungen vor, ohne wichtige Abdeckung zu verlieren.“

Geben Sie die Änderung oder das Repository, bekannte Fehler, Pflichtprüfungen sowie ausgeschlossene Dienste oder Kostengrenzen an. Sie erhalten einen kurzen Prüfumfang, bei Bedarf gepflegte ausführbare Tests und einen Bericht, der bestandene, fehlgeschlagene, übersprungene, blockierte und nicht ausgeführte Prüfungen unterscheidet. Der [Agenten-Workflow](SKILL.md) und die [Referenz zu Kosten und Leistung](references/cost-and-performance.md) erläutern das Vorgehen.

Innerhalb einer Iteration gelten frühere Prüfergebnisse nur weiter, solange die relevanten Eingaben und Annahmen übereinstimmen. Wiederholen Sie nach Änderungen oder Unterbrechungen nur betroffene Prüfungen oder fehlgeschlagene Schritte, statt alles neu zu starten. Behalten Sie verbindliche Abschlussprüfungen bei, vermeiden Sie unbegründete Doppelprüfungen lokal und in CI und benennen Sie vor weiteren Leistungsmessungen die offene Frage und das Abbruchkriterium. Einzelheiten stehen in der Referenz zu Kosten und Leistung.

## Beispiel ausführen

Lesen Sie die [Tag-Normalisierung](examples/tags.py) und ihre [Tests](examples/test_tags.py). Führen Sie im Verzeichnis des installierten Skills mit Python 3.11 oder neuer folgenden Befehl aus. Zusätzliche Pakete sind nicht erforderlich.

```sh
python3 -B -m unittest discover -s examples -p 'test_tags.py' -v
```

Drei Testmethoden prüfen normale Eingaben, Idempotenz, Unicode-Case-Folding und abgelehnte Eingaben. unittest führt die Assertions aus und liefert bei Fehlern einen Fehlerstatus. Diese Lehrbeispiele prüfen nicht Ihr Produkt; passen Sie das Muster an dessen vorhandenes Testframework an.

Automatisierte Ergebnisse belegen keine sachliche, sprachliche, visuelle oder barrierefreie Korrektheit. Für externe Dienste, kostenpflichtige Läufe, Veröffentlichungen und ausdrücklich ausgeschlossene Auswertungen gelten weiterhin die jeweiligen Genehmigungen. [MIT-Lizenz](LICENSE).
