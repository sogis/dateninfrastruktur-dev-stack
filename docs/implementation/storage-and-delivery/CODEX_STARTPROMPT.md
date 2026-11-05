# Codex-Startauftrag – MA-G Storage und CSV-Anlieferung

Du bist **Codex, der Implementierungsagent**. Implementiere den Gesamtauftrag MA-G0 bis MA-G5 in den vorhandenen sechs `dateninfrastruktur-*`-Geschwisterrepos. Liefere Code, wirksame Konfiguration, sichere lokale Umstellung, echte Tests und autonome unabhängige Reviews. Ein weiterer Plan allein erfüllt diesen Auftrag nicht.

## 1. Arbeitsbereich und Einstieg

Codex-Projekt ist der gemeinsame **Mutterordner**, nicht nur der Dev-Stack. Kein übergeordnetes Git-Repository anlegen. Lies zuerst die dortige `AGENTS.md`, dann alle betroffenen Repo-AGENTS. Der neue Auftrag liegt unter:

```text
dateninfrastruktur-dev-stack/docs/implementation/storage-and-delivery/
```

Lies vollständig README, EXECUTION_PLAN, alle sechs SPEC-Kapitel, TEST_PLAN, OPENCODE_REVIEW_PROMPT, AGENTS_ERGAENZUNG und SOURCES. Referenzierte Dateien sind Leseaufträge; ein Link ist kein Nachweis, dass du den Inhalt kennst. Nutze die vorhandenen MA-A–F-Quellen gezielt, aber überschreibe keine historischen Reviewurteile.

## 2. Unverhandelbarer Zielzustand

- Ein regulärer Compose-Verbund, zehn Dauer-Services, ein PG16/PostGIS, kein HA.
- Ein privater Datenbucket `ch.so.daten`; dessen alter **lokaler Entwicklungsinhalt** ist ausdrücklich zum Löschen freigegeben. Keine Cloud-/Fremdressourcen.
- Noch referenzierte private Objekte und bestehende PG-/Audit-/Identitätsdaten erhalten; `di-managed-private` nach belegter Übernahme entfernen.
- Neue INTERLIS-Zielmodelle, Cayenne/Fingerprint/Audit konsistent. Kein Framework-/ORMwechsel.
- PG verwaltet `submit_data`, `manage_submitters`, Aufträge und gültige Publikation.
- Jenkins über Keycloak, genau ein generischer CSVjob, kein Job/Build für normale Lieferanten.
- Ein echter GRETL-CsvValidator-Ablauf für replace/append, CH-Snapshots und CSV/XLSX/Parquet.
- Kein active compatibility code: keine Teams-YAML, Organisationsgeneratoren, Manifestreloads, alten APIparameter oder Storagekey-Fallbacks.

## 3. Phasenfolge und Reviews

MA-G0 → G1 → G2 → G3 → G4 → G5 strikt nacheinander. Jede Phase implementieren, risikogerecht testen, lokal committen und **autonom** durch eine frische OpenCode-2.x-Sitzung mit **DeepSeek Flash 1017** über den vorhandenen DeepSeek-Zugang prüfen lassen. Erst `ABGENOMMEN` am konkreten aktuellen SHA-Satz erlaubt die nächste Phase.

Verwende den vorhandenen Runner `STACK/scripts/management/review-phase.py` und das vorhandene `review_gate.py`. Erweitere deren zentrale Phasentabelle und Spec-/Repoauflösung für MA-G. Kein neues paralleles Reviewerprogramm. Der bisherige Code routet MA-F gesondert; MA-G darf nicht versehentlich auf die Management-/Access-Spezifikation zurückfallen. Neue JSON-Verträge und die aktuelle Workspace-AGENTS-Vorlage müssen im Handoff gehasht werden.

OpenCode-Desktop 2.x und seine bestehende Anmeldung verwenden. Keine OpenCode-1.x-CLI als scheinbare 2.x-Prüfung, keine nötige globale Neuinstallation, keine neuen APIkeys verlangen, keine fremden Providerdateien ersetzen. Tatsächliche CLIversion, Provider-/Modell-ID und Sessionbindung nachweisen. Bekannt ist `deepseek/deepseek-flash`; vor Verwendung den tatsächlichen vorhandenen Zugriff prüfen. Kein stiller Modellwechsel.

Reviewer arbeitet in eigenen Geschwistercheckouts mit eigenem Composeprojekt/Ports/Volumes/beschreibbaren Pfaden und synthetischen Credentials. Benutzer-`.env`, echte Dumps und private Objekte nicht kopieren. Originalrepo und Reviewer-Produktbaum bleiben beim Review unverändert. Ein `AGENTS.md`-Verbot ist kein technischer Schreibschutz, daher Integritätsnachweis.

Du startest und begleitest den Review selbst bis zu Report und echtem Urteil. Ein gestarteter Prozess ist kein abgeschlossenes Review. Keine Aufforderung an den Benutzer, den zweiten Agenten manuell zu starten. Bei echtem Tool-/Zugriffsblocker geschlossen bleiben und genau melden; nicht mit Selbstreview weitermachen.

## 4. Korrekturen ohne unnötige Gesamttests

Nach Findings: kleinster korrekter Fix, reproduzierender Test und nur potentiell betroffene Nachbarverträge. Begründete Delta-Auswahl in den Reviewrequest. Früher erfolgreich ausgeführte unabhängige Einzelbelege dürfen mit SHA-/Reporthash übernommen werden, wenn der Reviewer die Nichtbetroffenheit bestätigt. Keine pauschale Wiederholung aller MA-A–F- oder MA-G-Suiten und kein pauschales „war vorher grün“.

Bei Modell-/Identity-/Autoritäts-/Commit-/Fencingänderung den tatsächlich breiteren Risikobereich prüfen. Tests nicht abschwächen oder löschen, um ein Gate zu öffnen. Entfallene Altverträge ausdrücklich durch die neuen Tests ersetzen. UItexte oder Reportformatkorrekturen erzwingen keine vollständige Datenmigration.

## 5. Schutz vorhandener Arbeit

Lesende Inventur vor Mutation. Uncommittierte Nutzerarbeit und andere Branches nicht zurücksetzen. Kein `rsync --delete` auf Repos, keine globale Ersetzung von `datenportal`, kein `docker system prune`, kein `down -v`. Keine Remote-Pushes, PRs, Releases oder Änderungen externer echter Buckets im Auftrag.

Die gezielte lokale Entwicklungsumstellung ist nach unabhängiger Code-/Migrationabnahme Teil des Auftrags. Der Nutzer hat das Löschen alter Objekte in seinem lokalen `ch.so.daten` erlaubt; nichts darüber hinaus raten. Fremder Endpoint, unbekannte Sourceobjekte oder unklare Identitätsbindung sind enge reale Blocker. Übrige Implementierung autonom abschliessen; nichts still übergehen.

Keine Tokens/Passwörter/CSVinhalte in Prompts, Reporten, Git oder Shellargumenten. Secrets nur über private Dateien/Programme verarbeiten. Eigene temporäre Belege bereinigen. Produktive PGdaten und Auditgeschichte nicht durch synthetische Testdaten ersetzen.

## 6. Explizite Technikentscheidungen

Behalte die geprüfte Framework-/Toolchainbasis. G0 beweist den tatsächlichen OIDC-Tokenweg aus Jenkins und die echte CsvValidator-/Modellfunktion. Keine Spezifikations-Methodensignatur als bereits verfügbare Drittbibliotheks-API ausgeben. Notwendige Änderungen eng dokumentieren, nicht Architektur heimlich vereinfachen.

Kein HA, keine Backupautomatisierung, kein CI-Neubau, keine Spezialjobplattform, keine persönliche ClickHouse-Rechteprojektion. Neue Daten sind nicht automatisch für Foundationreader/Superset lesbar. API-Breaks sind erwünscht, aber kein Ersatz für korrektes Beibehalten von Daten und Audit.

## 7. Handoff und Abschluss

Pro Phase einen Request mit Base-SHAs und Tests erstellen. Produktcode/Tests/Request lokal in den konkreten Repos committen. Danach tatsächliche Head-SHAs in den **ignorierten** Handoff schreiben; keine selbstreferenzielle Commit-ID in denselben Commit einbacken. Rohbelege unter `STACK/.runtime/ingestion-review/<phase>/<run>/`, bereinigte Reports im neuen Auftragsordner.

Zum Abschluss getrennt berichten: implementierter aktueller SHA-Satz, unabhängig bestandene Gates, tatsächlich ausgeführte lokale Umstellung, entfernte Altpfade und eventuell verbleibende echte Blocker. Ein Test-Compose ist kein Nachweis des Nutzerzustands. Ein erfolgreicher HTTP200 ist kein Ersatz für validierte Datei-/CH-/PGdaten.

**Beginne jetzt mit vollständigem Lesen und MA-G0.**
