# AGENTS.md – dateninfrastruktur-dev-stack

## Vor Beginn lesen

Lies ausdrücklich `../AGENTS.md` sowie den aktuellen Gesamtauftrag unter `docs/implementation/management-and-access/EXECUTION_PLAN.md`, die dort referenzierten SPEC-Dateien, TEST_PLAN und den rollenbezogenen Start-/Reviewprompt. Die nachfolgenden Grundinstallationsregeln und Nachweise sind historisch auf ihren damaligen Auftrag begrenzt; sie verbieten den ausdrücklich beauftragten Ausbau MA-0 bis MA-E nicht. Weitere betroffene Schwesterrepos haben eigene AGENTS-Dateien.

Diese Regeln gelten für Implementierung **und** Review. Ein Reviewauftrag erlaubt keine Änderungen an Produktdateien, Tests, Anforderungen oder AGENTS-Dateien; Befunde melden, nicht selbst reparieren. Builds/Tests nur mit eigenen Laufzeitdaten. Quellrepos, fremde Änderungen und laufende fremde Instanzen erhalten; keine Secrets in Git oder Berichten.

## Verantwortung

Dieses Repo führt Compose, Start-/Testskripte, Gateway, Initialisierung und Integration der Grundinstallation. Der zentrale Auftrag und alle repoübergreifenden Belege liegen hier. Die Anwendungs- und Pluginquellen bleiben in ihren Schwesterrepos.

## Besondere Regeln

- Baue eigene Jenkins-/Sodata-Images aus den neuen Geschwisterrepos. Keine Rückfälle auf alte Datenportal-Images oder ein veröffentlichtes altes HPI.
- Neue Dienste: ClickHouse, Keycloak, PostgreSQL und Superset; feste geprüfte Releases, native Plattform und aufgezeichnete Image-/Treiberversionen.
- Folge der bestehenden Gateway-/Jenkins-Netzwerktopologie; interne Adressen, externe Loopback-Ports und Manifest-URLs konsistent anpassen. Keine unnötige Netzneugestaltung.
- Eigene Compose-Projektnamen, Volumes, Ports **und schreibbare Hostpfade** pro Instanz. Keine gemeinsamen Secrets mit einem anderen Stack.
- Editor und separate Dokumentationswebsite aus allen aktiven Abhängigkeiten entfernen; vorhandenen Portal-/GRETL-Bootstrap erhalten.
- Root-README beschreibt den Betrieb. Die Paket-README bleibt in `docs/implementation/grundinstallation/`. Keine verwechselten oder überschriebenen README-Dateien.

## Nachweise

Integrationstests müssen Seedjob, Veröffentlichung, Sodata-Readiness, JDBC, Superset-Treiber, Rechte-Negativtests, privaten S3-Zugriff und Wiederanlauf tatsächlich prüfen. Konfigurationsvalidierung allein genügt nicht. Konkrete unterstützte Start-/Testkommandos im Root-README dokumentieren; nicht vorhandene Skripte nicht als bereits existent ausgeben.

Phasenberichte unter `docs/implementation/grundinstallation/reports/`, Kandidaten unter `candidates/<candidate-id>/`, Reviewberichte unter `review/<candidate-id>/<run-id>/` innerhalb desselben Dokumentationsordners. Die Trennung von Produktstand und Nachweisartefakten folgt Abschnitt 8.1 des Auftrags.

## Aktuelle Management-/Access-Etappe

Aktive Phasen und Berichte liegen unter `docs/implementation/management-and-access/`. Historische Nachweise nicht ändern. Reviewer benötigen isolierte Geschwistercheckouts, Ports, Volumes und schreibbare Hostpfade sowie den unveränderlichen Workspace-AGENTS-Inhalt/Hash. Vorhandene Reviewerwerkzeuge wiederverwenden; Benutzer-Secrets nicht kopieren.

## Aktiver Folgeauftrag MA-F0–MA-F4

Vor Arbeit den vollständigen Auftrag unter
`../dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/CODEX_STARTPROMPT.md`
und alle dort referenzierten Spezifikationen lesen. Workspace-AGENTS ist bindend.
Die früheren Betriebs-/Grundinstallationsgrenzen oben sind historische Regeln,
keine Verbote dieser ausdrücklich beauftragten Konsolidierung. Fachliche MA-A–E-
Verträge bleiben erhalten. MA-F erlaubt genau einen Compose-Verbund, einen PG16/
PostGIS-Server und eine Instanz pro Dauer-Service. Kein HA, keine parallele
Managementorchestrierung. APISIX wird aus Jenkins' Netzwerkraum gelöst.

Bestehende identifizierte eigene Daten/Volumes/Identitäten/Secrets kontrolliert
übernehmen, nicht durch leere Seeds ersetzen. Retire erst nach geprüftem Backup
auch der Container-Schreibschichten. Keine fremden Ressourcen ändern. Phasen
strikt nacheinander, unabhängige OpenCode2-/DeepSeek-Flash1017-Abnahme je Phase.
Berichte unter compose-consolidation/, Rohbelege unter STACK/.runtime/compose-review/.
