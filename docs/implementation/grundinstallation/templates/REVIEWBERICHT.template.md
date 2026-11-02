# Review <candidate-id> / <run-id>

> Vorlage, kein Reviewnachweis. Nach `../review/<candidate-id>/<run-id>/REVIEW.md` kopieren und ausschliesslich tatsächlich beobachtete Ergebnisse eintragen.

## Identität und Prüfgegenstand

- Reviewart: <Abschlussreview | Phasenreview mit benanntem Umfang>
- Gesamtstatus: **NICHT BEWERTET**; nach tatsächlicher Prüfung PASS, FAIL oder BLOCKED gemäss Auftrag setzen.
- Tatsächliches Datum / OpenCode-Version / Provider-Modell / Sitzung: <...>
- Lokaler WORKSPACE_ROOT und gegebenenfalls Pfadzuordnung: <...>
- Manifestpfad / SHA256: <...>
- Anforderungsdatei / SHA256: <...>
- Tatsächlich gelesene und gegen das Manifest geprüfte Prompt-/AGENTS-Dateien: <...>
- Geprüfte Repo-Commits beziehungsweise Datei-Manifeste: <...>
- Eigener Compose-Projektname, Ports und Runtimepfad (ohne Secrets): <...>

## Abnahmekriterien

| ID | Status | Eigener Prüfschritt / Beobachtung | Belegpfad |
|---|---|---|---|
| G01 | NOT RUN | — | — |
| G02 | NOT RUN | — | — |
| G03 | NOT RUN | — | — |
| G04 | NOT RUN | — | — |
| G05 | NOT RUN | — | — |
| G06 | NOT RUN | — | — |
| G07 | NOT RUN | — | — |
| G08 | NOT RUN | — | — |
| G09 | NOT RUN | — | — |
| G10 | NOT RUN | — | — |
| G11 | NOT RUN | — | — |
| G12 | NOT RUN | — | — |
| G13 | NOT RUN | — | — |
| G14 | NOT RUN | — | — |
| G15 | NOT RUN | — | — |
| G16 | NOT RUN | — | — |
| G17 | NOT RUN | — | — |
| G18 | NOT RUN | — | — |
| G19 | NOT RUN | — | — |
| G20 | NOT RUN | — | — |
| G21 | NOT RUN | — | — |
| G22 | NOT RUN | — | — |
| G23 | NOT RUN | — | — |
| G24 | NOT RUN | — | — |

Bei Übernahme eines älteren Belegs: früheren Kandidaten, Beleg, unveränderten Gegenstand und relevante Abhängigkeiten ausdrücklich benennen. Sonst erneut prüfen.

## Ausgeführte Kommandos

| Arbeitsverzeichnis | Kommando ohne Secrets | Exitcode | Beobachtung / bereinigter Beleg |
|---|---|---|---|
| <...> | <...> | <...> | <...> |

## Befunde

Je Befund: ID, Schwere, betroffene G-Anforderung, Datei/Funktion, Reproduktion, beobachtetes und erwartetes Verhalten. Keine Produktkorrektur durch den Reviewer.

## Fehlende Nachweise / Grenzen

<Was wurde nicht geprüft? Welche konkrete Voraussetzung fehlt? Keine unerbrachten Nachweise als PASS darstellen.>

## Integrität und Abschluss

- Manifest-SHA256 vor/nach Review identisch: <Ergebnis und Beleg>
- Produktdateien einschliesslich Tests/AGENTS/Anforderungen vor/nach unverändert: <Ergebnis und Vergleichsmethode>
- Neu geschriebene Reviewbelege gegenüber dem Produktstand abgegrenzt: <Pfade>
- Verbliebene beziehungsweise bereinigte eigene Testressourcen: <...>
- Gesamtentscheidung und Begründung: <...>

Dieser Bericht gehört zu genau dem oben genannten Kandidatenmanifest. Ein späterer reiner Nachweiscommit ändert dessen geprüfte Quellstände nicht.
