# Codex – ausführbarer Auftrag MA-F: Compose-Konsolidierung

Du bist **Codex, der Implementierungsagent**. Setze die bereits funktional vorhandenen Management-/Access-Komponenten in den **einen** bestehenden Docker-Compose-Stack um. Liefere Implementierung, Datenübernahme, Tests und autonome unabhängige Phasenreviews – nicht nur einen weiteren Plan.

## 1. Einstieg

Arbeite im gemeinsamen Elternordner der sechs `dateninfrastruktur-*`-Repositories. Kein übergeordnetes Git-Repo anlegen. Lies die Workspace-/betroffenen Repo-AGENTS und danach vollständig:

- `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/EXECUTION_PLAN.md`
- `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/SPEC_MIGRATION.md`
- `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/TEST_PLAN.md`
- `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/OPENCODE_REVIEW_PROMPT.md`
- `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/AGENTS_ERGAENZUNG.md`

Historische MA-A–E-Spezifikationen/Reviews gezielt als Fachvertrags- und Codebasis lesen. Deren damalige Zweifach-Topologie ist **nicht** das neue Betriebsziel. Keine Historie umschreiben. Kein Rückbau funktionaler Autorisierung/Auditierung.

## 2. Unverhandelbares Ziel

- Eine `compose.yaml` im Dev-Stack als aktive Standardtopologie.
- Genau ein PostgreSQL16/PostGIS-Container für Keycloak-, Superset- und Managementdatenbanken, jeweils eigene Konten.
- Genau eine Instanz je Gateway, Admin, Sodata, Keycloak, Garage und Origin; vorhandene Jenkins-, ClickHouse- und Superset-Instanzen integriert.
- Kein HA, kein dauerhafter paralleler Managementstack, kein verstecktes `docker run` im Standardstart.
- Stabile URLs, Images statt nur Host-JAR-Mounts, persistente benannte Volumes, sicherer Recreate.
- Bestehende Fach-/Auditdaten, Benutzerbezüge, Secrets und Dateiinhalte bleiben erhalten. Keine neue leere Installation als Ersatz für Migration.

## 3. Arbeitsfolge

Bearbeite MA-F0, MA-F1, MA-F2, MA-F3 und MA-F4 strikt nacheinander. Vor jeder nächsten Phase: eigene passende Tests, lokale Commits, unabhängiges **ABGENOMMEN** für genau den aktuellen Kandidaten.

Verwende den vorhandenen OpenCode-Reviewrunner. Startmodell: **OpenCode 2.x / DeepSeek Flash 1017 über den bestehenden DeepSeek-Provider**. Exakte verfügbare Modell-ID und CLI-Version zu Beginn nachweisen, nicht aus einem vermeintlichen Alias erraten. Keine globalen Accounts/Keys/Permissions überschreiben. Kein stiller Modellwechsel oder Selbstreview.

Du startest und begleitest die Reviews selbst in einer frischen OpenCode-Sitzung mit isolierten Geschwistercheckouts. Prüfer darf lesen, bauen, testen und eigene Gegenproben anlegen, aber nicht Produktdateien reparieren. Bei Findings korrigierst du, committest neu und startest ein gezieltes Delta-Review. Nach Review keine ungeprüften Produktänderungen als abgenommen melden.

## 4. Schutz vorhandener Zustände

Vor Mutation tatsächliche Repos, Container, Volumes und Runtimeverzeichnisse inventarisieren. Fremde Änderungen erhalten. Keine `.env`/Realmvorlage pauschal neu erzeugen, keine Benutzer aus Namen raten. Kein `down -v`, kein globales Prune, keine Entfernung alter MAcontainer ohne gesicherten Zustand aus ihren Volumes **und** Schreibschichten.

Die gezielte Migration der identifizierten eigenen lokalen Dateninfrastrukturinstanz ist Teil des Auftrags. Nutze deren Secrets ausschliesslich programmatisch, nicht als Modell-/Berichtsinhalt. Reviewer erhalten niemals Nutzerdumps/Secrets; ihre Testdaten entstehen getrennt.

Bestehende PG16.10-Foundation nicht ungeprüft auf den älteren MA-PG16.9-Digest umstellen. Ein kompatibles PG16/PostGIS-Image mit ausreichendem Patchstand/Architektur wählen und testen. Kein Majorupgrade.

Mehrere widersprüchliche befüllte Quellen oder unklare Identitätszuordnungen sind echte enge Migrationsblocker. Nicht raten oder löschen; übrige Implementierung/Tests fertigstellen und genau benennen, was für den Livecutover offen ist. Gewöhnliche technische Fehler dagegen selbständig lösen.

## 5. Schlanke Tests, echte Abnahme

Nach Fixes **nur betroffene Verträge und plausible Regressionen** neu prüfen. Eine kurze Änderungs-/Risikotabelle genügt. Keine neue allgemeine Evidenzplattform und keine pauschale Wiederholung aller MA-A–E-Suites.

Final muss die normale Composeumgebung den Fachpfad und Recreate bestehen. Ein grüner Legacy-Testharness, Compose-Labeltrick oder Container-Healthstatus allein ist unzureichend. Im Abschluss getrennt berichten: akzeptierter Code, wirklich durchgeführter lokaler Cutover und eventuell offene Retireaufgaben.

## 6. Nachweise und nächste Aktion

Eine `WORK_QUEUE.md` im Auftragsordner; pro Phase ein kurzer Reviewrequest mit `base_sha`, Scope, Tests und Risiken. Produkt/Tests/Request lokal committen. **Erst danach** vollständigen `head_sha` in ignoriertem Handoff festhalten, niemals selbstreferenziell im gleichen Commit. Isolierte Rohbelege unter `STACK/.runtime/compose-review/<phase>/<run>/`, bereinigte Reviews im Auftragsordner.

Beginne jetzt mit dem Lesen der Dateien und MA-F0. Prüfe insbesondere `compose.yaml`, Root-Startskripte, `ADMIN/scripts/managed_runtime.py`, `management_db.py`, `setup.py` und die tatsächlichen lokalen Quellen. Richte nicht vorsorglich einen weiteren Dauerstack ein.
