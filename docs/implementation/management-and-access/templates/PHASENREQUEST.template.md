# Reviewrequest <MA-Phase>

**Vor dem Produktcommit schreiben; kein eigener head_sha in dieser Datei.**

## Ausgangspunkt
- Repos und vollständige base_sha:
- Phase und konkrete Zielverträge:
- Neue Funktion oder Korrekturlauf:
- Bei Korrektur: früherer Kandidat/Reporthash und Findings:

## Änderungen
- Betroffene Dateien/Klassen/Methoden:
- Fachlich beobachtbare Wirkung:
- Betroffene Abhängigkeiten und Sicherheitsgrenzen:

## Testauswahl
| ID | Neu auszuführen / übertragbarer Beleg | Grund | Kommando, CWD, Ergebnis | Beleg |
|---|---|---|---|---|

## Nicht betroffene Bereiche
Begründung, warum deren Tests nicht erneut laufen müssen.

## Bekannte Grenzen/Blocker
Pflicht-NOT_EXECUTED getrennt von NOT_REQUIRED.

## Übergabe
Nach Commit: vollständigen head_sha je Repo, Hash dieses Requests und aller
verbindlichen Spezifikationsdateien in einem ignorierten handoff.json binden.
Reviewer prüft selbst und erfindet eine eigene passende Gegenprobe.
