# MA-F: Compose-Konsolidierung

Ein Folgeauftrag, fünf blockierende Phasen: **MA-F0 bis MA-F4**. Ziel ist der gemeinsame lokale Betrieb der vorhandenen Anwendungen, nicht deren Neuentwicklung.

## Ablage

In `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/` ablegen. Das ZIP ist dafür vorbereitet. Nicht das gesamte Repo ersetzen. Der gemeinsame Elternordner bleibt der Codex-Arbeitsbereich; kein neues Git-Repo darin.

## Verbindliche Dokumente

- [EXECUTION_PLAN.md](EXECUTION_PLAN.md): Zielbetrieb, Services, Codeverantwortlichkeiten und Phasen.
- [SPEC_MIGRATION.md](SPEC_MIGRATION.md): nichtdestruktive Übernahme, Identitäten, Storage und Rückfall.
- [TEST_PLAN.md](TEST_PLAN.md): F01–F20 und risikobasierte Regression.
- [CODEX_STARTPROMPT.md](CODEX_STARTPROMPT.md): eigentlicher Implementierungsauftrag.
- [OPENCODE_REVIEW_PROMPT.md](OPENCODE_REVIEW_PROMPT.md): autonome unabhängige Prüfung.
- [AGENTS_ERGAENZUNG.md](AGENTS_ERGAENZUNG.md): aktive Anweisungen minimal fortschreiben.
- [SOURCES.md](SOURCES.md): geprüfte Quellstände und Produktdokumentation.

## Festlegungen

Ein normaler Compose-Stack mit zehn dauerhaft laufenden Services. Genau ein PG16/PostGIS für drei getrennte Datenbanken. Ein Keycloak auf PostgreSQL; ein Gateway, Portal, Admin, Garage und Datei-Origin. Kein HA und keine zweite Managementorchestrierung. ClickHouse, Jenkins und Superset bleiben integriert.

Vorhandene Daten/Secrets/IDs erhalten. Tests benutzen isolierte Instanzen derselben deklarativen Topologie; diese werden wieder entfernt. Kein als normaler Betrieb getarnter Testharness.

## Start in Codex

Öffne den gemeinsamen Elternordner und sende:

```text
Implementiere die Folgephase MA-F zur Konsolidierung unserer Dateninfrastruktur.

Lies die Workspace-/Repo-AGENTS und danach vollständig:
dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/CODEX_STARTPROMPT.md
sowie alle darin referenzierten Spezifikationen.

Ziel: ein gemeinsamer Docker-Compose-Stack, ein PostgreSQL16/PostGIS-Container
für alle drei Anwendungsdatenbanken, keine doppelten Dauercontainer, kein HA.
Bestehende Daten, Identitäten, Secrets und Berechtigungen sicher übernehmen.

Beginne mit MA-F0. Jede Phase gezielt testen und autonom durch OpenCode 2.x
mit DeepSeek Flash 1017 unabhängig prüfen lassen, erst dann weitergehen.
Nach Korrekturen nur betroffene Verträge und sinnvolle Regressionen neu testen.

Liefere echte Implementierung und den kontrollierten lokalen Cutover,
soweit die Quellen eindeutig sind. Keine neue parallele Laufzeit erzeugen
und keine vorhandenen Volumes ungeprüft löschen.
```

Die Beispiel-JSONs sind Platzhalter, keine fertigen Abnahmen. Reale technische Kommandos der neuen Konsolidierung müssen erst implementiert werden. Den vorhandenen unabhängigen Reviewrunner wiederverwenden.

Dieses Paket wurde auf interne Dateiverweise und Vorlagen geprüft; die Konsolidierung selbst ist noch nicht ausgeführt.
