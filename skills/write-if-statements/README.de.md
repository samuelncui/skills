# Wie man eine if-Anweisung schreibt

[English](README.md) · [简体中文](README.zh-CN.md) · [日本語](README.ja.md) · [Français](README.fr.md) · [Deutsch](README.de.md)

Dieser Skill hilft beim Schreiben neuer Bedingungslogik, beim Prüfen verzweigungsreicher Funktionen und beim Vereinfachen von Code ohne Verhaltensänderung. Ziel sind verständliche Entscheidungen, nicht möglichst wenige `if`-Anweisungen.

## Installation und Verwendung

Nutzen Sie die Skills CLI oder einen vom Host unterstützten Installer:

```sh
npx skills add samuelncui/skills --skill write-if-statements
```

Behalten Sie das vollständige Skill-Verzeichnis samt Lizenz, Referenzen und Beispielen. Zum Lesen der Anleitung sind weder andere Skills noch Python nötig; nur zum Ausführen der Beispiele wird Python 3 benötigt.

Bitten Sie Ihren Programmierassistenten, `$write-if-statements` zu verwenden, oder wählen Sie den Skill im Host aus. Geben Sie den betreffenden Code, seine Aufrufer, das erwartete Verhalten und den verfügbaren Testbefehl an. Mögliche Aufträge:

- „Schreibe die Wiederholungsbedingung für diesen Client: nur bei vorübergehenden Fehlern und verbleibenden Versuchen erneut versuchen. Halte sie einfach und teste die Grenzen.“
- „Prüfe diese Routing-Funktion. Würde eine Zuordnungstabelle die Priorität des ersten Treffers und das Überspringen unnötiger Arbeit erhalten? Noch nichts ändern.“
- „Verringere die Verschachtelung dieses Handlers, ohne Rückgabewerte, Ausnahmen oder Ressourcenfreigabe zu ändern. Ergänze Regressionstests und führe die betroffenen Tests aus.“

Das Ergebnis sollte eine klar eingegrenzte Prüfung oder ein Patch sein, ergänzt um die Begründung der Strukturwahl sowie Testergebnisse und offene Prüfgrenzen. Eine klare, einfache Verzweigung kann unverändert bleiben. Die Behebung eines vermuteten Fehlers ist von einer verhaltenserhaltenden Refaktorierung zu trennen.

## Beispiele ausführen

Lesen Sie die [Implementierung](examples/conditionals.py) zusammen mit den [Tests](examples/test_conditionals.py). Führen Sie im Skill-Verzeichnis Folgendes aus:

```sh
python3 -B -m unittest discover -s examples -p 'test_conditionals.py' -v
```

Sieben Testmethoden prüfen Ergebnisse und Ressourcenfreigabe bei Guard Clauses, die Weitergabe von Ausnahmen, überlappende geordnete Regeln, übersprungene Prädikate, die ausschließliche Ausführung des ausgewählten Handlers und eine einfache, beizubehaltende UND-Bedingung. Sie verwenden nur die Standardbibliothek und prüfen diese Lehrbeispiele, nicht Ihre Anwendung.

## Grenzen und weitere Informationen

Eine geordnete Bedingungskette ist nicht automatisch einem Dictionary gleichwertig. Das Verschieben einer Entscheidung kann Ausführungszeitpunkte, Ausnahmen und den beobachteten Zustand verändern. Lesen Sie dazu die [semantischen Fallstricke und Primärquellen](references/semantic-traps.md). Den Ablauf für den Agenten beschreibt [SKILL.md](SKILL.md).

Die eigenständig verfassten Texte und Beispiele stehen unter der beigefügten [MIT-Lizenz](LICENSE). Verlinkte externe Werke behalten ihre eigenen Rechte.
