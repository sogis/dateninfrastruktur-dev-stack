# Phasenbericht P<0–4> – <Titel>

> Vorlage, kein ausgeführter Nachweis. Unter `../reports/P0.md` bis `P4.md` verwenden. Platzhalter erst durch tatsächlich beobachtete Werte ersetzen.

## Einordnung

- Phase / Zeitpunkt: <...>
- Status: <IN_ARBEIT | LOKAL_GEPRUEFT | BLOCKIERT>
- OpenCode-Version / tatsächlicher Provider und Modell / Sitzung: <...>
- WORKSPACE_ROOT: <...>
- Gelesene Auftrags-, Prompt- und AGENTS-Dateien: <Pfade; bei Handoff im Manifest gehasht>
- Umfang / angestrebtes Ergebnis dieser Phase: <...>

## Änderungen und Herkunft

| Zielrepo | Ausgangsstand / Quelle | Geänderte Dateien | Zweck / Abweichung |
|---|---|---|---|
| <Repo> | <Commit oder vollständiger Snapshot> | <Pfade> | <Begründung> |

Bei P0: Kopierplan, vorhandene Nutzerarbeit, auszuschliessende Runtime-/Secret-Pfade und Umgang mit bereits abgelegten Ziel-AGENTS dokumentieren. Keine Secretinhalte wiedergeben.

## Tatsächlich ausgeführte Prüfungen

| G-ID / Prüffrage | Arbeitsverzeichnis | Kommando ohne Secrets | Exitcode | Ergebnis | Belegpfad |
|---|---|---|---|---|---|
| <...> | <...> | <...> | <tatsächlicher Code> | <PASS / FAIL / NOT RUN + Grund> | <...> |

Nur tatsächlich ausgeführte Prüfungen als bestanden markieren. Nicht ausgeführte und blockierte Prüfungen separat erklären.

## Offene Punkte und nächste Schritte

<Fehler, Blocker, Annahmen, verbleibende Arbeiten und beeinflusste Repos.>

## Übergabe

<Kandidatenkennung/Manifestpfad, sobald vorhanden. Nicht den Hash eines noch nicht erzeugten Manifests erfinden und nicht eine Selbstreferenz erzwingen.>

Unabhängige Abnahme: **ausstehend**, sofern kein tatsächlicher separater Reviewbericht vorliegt. Bereits festgeschriebene Berichte nicht rückwirkend auf spätere Kandidaten umschreiben.
