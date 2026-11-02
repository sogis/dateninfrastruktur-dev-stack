# AGENTS.md – dateninfrastruktur-dev-stack

## Vor Beginn lesen

Lies ausdrücklich `../AGENTS.md` und `docs/implementation/grundinstallation/AUFTRAG_GRUNDINSTALLATION.md` sowie den zur aktuellen Rolle gehörenden Startprompt im selben Dokumentationsordner. Fehlt `../AGENTS.md`, lies ersatzweise `docs/implementation/grundinstallation/templates/AGENTS.workspace.md`. Verlasse dich nicht auf automatische Vererbung über Git-Grenzen. Weitere betroffene Schwesterrepos haben eigene AGENTS-Dateien.

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
