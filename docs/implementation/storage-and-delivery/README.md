# MA-G – Ein privater Speicher und eine autorisierte CSV-Anlieferung

**Gesamtspezifikation für Codex · 5. November 2026 · Revision 1.0**  
Implementierung: **Codex**. Unabhängige Prüfung nach **jeder** Phase: **OpenCode 2.x / DeepSeek Flash 1017**, vorhandener direkter DeepSeek-Zugang. Diese Dateien sind der Auftrag, nicht ein Nachweis einer bereits implementierten Lösung.

## Einstieg und Lesereihenfolge

1. [EXECUTION_PLAN.md](EXECUTION_PLAN.md): Zielzustand, verbindliche Entscheidungen, Phasen, Repositorygrenzen.
2. [SPEC_STORAGE.md](SPEC_STORAGE.md): ein privater Bucket, technische Schlüssel, sichere einmalige Umstellung.
3. [SPEC_MODELS_ACCESS.md](SPEC_MODELS_ACCESS.md): INTERLIS, Schemaevolution, Lieferrechte und fachliche Auditierung.
4. [SPEC_INGESTION_API.md](SPEC_INGESTION_API.md): Auftrag, Identität, Zustände, HTTP-Verträge, Wiederanlauf.
5. [SPEC_JENKINS_PLUGIN.md](SPEC_JENKINS_PLUGIN.md): neues Plugin, OIDC, Upload, Dispatch und genau ein CSV-Job.
6. [SPEC_CSV_PIPELINE.md](SPEC_CSV_PIPELINE.md): CsvValidator, replace/append, unveränderliche Stände, ClickHouse und Dateioutputs.
7. [SPEC_CLEANUP_CUTOVER.md](SPEC_CLEANUP_CUTOVER.md): konkrete Entfernungsliste, Liveumstellung und Schlussinventur.
8. [TEST_PLAN.md](TEST_PLAN.md): prüfbare Verträge, Phasentests und Delta-Regeln.
9. Rollenbezogen [CODEX_STARTPROMPT.md](CODEX_STARTPROMPT.md) oder [OPENCODE_REVIEW_PROMPT.md](OPENCODE_REVIEW_PROMPT.md).
10. [AGENTS_ERGAENZUNG.md](AGENTS_ERGAENZUNG.md) und [SOURCES.md](SOURCES.md).

Alle Kapitel bilden **einen** Auftrag. Die Aufteilung dient der Lesbarkeit, nicht der Auswahl optionaler Anforderungen. Bei Widersprüchen ist der engere Sicherheits-/Datenerhaltungsvertrag massgeblich; eine fachliche Änderung nicht eigenmächtig als „Implementierungsdetail“ deklarieren.

## Was am Ende funktionieren muss

Eine über Keycloak angemeldete Fachperson wählt im Jenkins-Anlieferungsformular einen **für sie lieferberechtigten** Datensatz und lädt CSV hoch. Ein zentral in PostgreSQL gespeicherter Auftrag bindet Person, Dataset, Ausgabe, Datei und Verarbeitungsvertrag. Genau ein parametrisierbarer Jenkins-/GRETL-CSV-Ablauf validiert, bildet einen vollständigen neuen Datenstand, schreibt private Dateien und ClickHouse-Daten und bestätigt die Veröffentlichung. Sodata liest PostgreSQL. Downloads bleiben APISIX → Java-Authorization-API → interner Origin → privates S3.

`ch.so.daten` ist der einzige aktive Datenbucket dieser Anwendung. Sein alter Entwicklungsinhalt darf gezielt gelöscht werden. Referenzierte Dateien aus `di-managed-private` werden vor dessen Entfernung erhalten. Keine Public-ACLs, keine parallele Teams-YAML, kein Manifestkatalog, kein alter Publikationsmodus, keine Legacy-API-Aliase.

## Nicht in dieser Etappe

Keine Spezialjob-Engine, kein Hop-Ausbau, kein HA/OpenShift, kein Agentic BI, keine persönliche ClickHouse-Rechteprojektion, keine produktive AIO-Anbindung, keine Backupautomatisierung und keine neue CI-Plattform. Bestehende fachliche Rechte, Auditdaten, Identitäten und nicht zur Löschung freigegebene Nutzerdaten bleiben geschützt.

## Umsetzung und Abnahme

MA-G0 → MA-G1 → MA-G2 → MA-G3 → MA-G4 → MA-G5. Kein Übergang ohne gezielte Tests und unabhängiges `ABGENOMMEN`. Bei Korrekturen werden der reproduzierende Fehler und tatsächlich gefährdete Verträge neu geprüft, nicht blind alle früheren Suiten.

Die maschinenlesbare Phasenzuordnung steht in [contracts/phase-checks.json](contracts/phase-checks.json). Sie wird in den vorhandenen Reviewrunner übernommen; kein neues Reviewframework. Historische MA-F-Abnahmen bleiben historisch und legitimieren keine neuen Berechtigungs- oder Datenpfade.
