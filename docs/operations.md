# Gemeinsamer Composebetrieb

Der reguläre Verbund hat zehn Dienste: postgres, keycloak, garage, origin,
gateway, sodata, admin, jenkins, clickhouse und superset. Ein PostgreSQL16.10/
PostGIS3.5.2-Server enthält die getrennten Datenbanken keycloak, superset und
dateninfrastruktur_management. Keine HA- oder zweite Managementinstanz.

Alle Rootskripte und die Managementaliases verwenden `compose_operations.py`:
dieselbe compose.yaml, explizite private ENV-Datei, Projekt-/Instanzkennung und
Runtime. Die aktive Zuordnung steht geschützt unter `.runtime/active-compose.json`;
die Konfiguration selbst unter `.runtime/<project>/runtime.env`. Alte `.env` und
ADMIN/.runtime sind ausschliesslich Migrationsquellen, kein zweiter Normalstart.

## Bestehender Bestand

Kein `init` über eine bestehende Foundation ausführen. Die kontrollierte Übernahme
steht in [migration-ma-f.md](migration-ma-f.md). Ein vorhandenes anderes Projekt
oder unbekannter Runtimebereich wird weder adoptiert noch zurückgesetzt.
Nach erfolgreicher Umschaltung verwenden normale Skripte automatisch den aktiven
Zielkontext; der migrationsbedingt gewählte Projektname darf vom Freshdefault
`dateninfrastruktur-dev-stack` abweichen.

## Frische leere Installation

Docker/Compose und die sechs Geschwistercheckouts sind erforderlich. Die vorhandene
Jenkins-/Plugin-Buildkette bleibt erhalten (`build-jenkins-local.sh`, JDK21/Maven);
der Stack verwendet das bereits lokal gebaute Jenkinsimage über seine Image-ID.
Admin, Sodata, PostgreSQL und die Schema-/Operatorwerkzeuge werden in Docker gebaut;
Host-Java25, Host-pg_dump und Host-rclone sind für den Betrieb nicht erforderlich.

```sh
./scripts/init.sh
./scripts/setup.sh
./scripts/up.sh --skip-build
./scripts/status.sh
./scripts/smoke-test.sh
```

`setup` ist ausdrücklich erforderlich. Der erste Lauf legt nur leere technische
Strukturen an, keine fachlichen Datensätze, Authorities oder Grants. Ein bekannter
Bestand wird ausschliesslich verifiziert; fehlende bekannte Datenbanken/Schemas
werden nicht durch einen leeren Neuaufbau verdeckt. Native Buildoptionen der
Anwendungen bleiben in deren Gradleprojekten bestehen; JVM ist der geprüfte Betrieb.

## Tagesbetrieb

```sh
./scripts/up.sh                 # benötigte kanonische Images bauen, starten
./scripts/up.sh --skip-build    # vorhandene Images verwenden
./scripts/up.sh --build-only    # nur bauen
./scripts/stop.sh               # Container stoppen, alle Daten behalten
./scripts/restart.sh            # geordnet stoppen/starten, kein Seed
./scripts/down.sh               # eigene Container/Netz entfernen; KEINE Volumes
./scripts/logs.sh --tail 100
```

Mit `--env /absoluter/pfad/.runtime/<projekt>/runtime.env` ist dieselbe Bedienung
für einen ausdrücklich gewählten Kontext möglich. Ein falsches Instance-Label
oder eine geänderte bekannte Volumenzuordnung wird vor Start/Stop abgewiesen.
Neue Datenablagen verlangen eine explizite Migration. Keine `--volumes`, kein
`--remove-orphans` und kein Prune in diesen Betriebsbefehlen.

Nach explizitem Setup funktioniert auch das reine Compose-Up mit demselben File:

```sh
docker compose --project-name <projekt> --env-file .runtime/<projekt>/runtime.env --file compose.yaml up -d --wait
```

Standardadressen: Gateway/Portal/Admin/Jenkins `http://localhost:18081/`,
Anlieferung `/anlieferung`, Jenkins `/jenkins/`, Keycloak `http://localhost:18080/`,
Superset `http://localhost:18088/`, ClickHouse HTTP/native 18123/19000.
Admin, Sodata, PostgreSQL, Garage und Origin haben keine direkten Hostports.
Alte öffentliche Manifest-/Bucketpfade sind gesperrt. Im MA-G-Ziel ist
`ch.so.daten` der einzige private Anwendungsbucket. Origin liest ausschliesslich
`downloads/` mit dem Reader; Webdienste erhalten keine Storagecredentials.
Die tatsächliche lokale Umschaltung ist im aktiven WORK_QUEUE ausgewiesen.

## Operatoren und Tests

Neue CSV-Versionen werden ausschliesslich über den gebundenen, validierten
Ingestionabschluss angenommen. Die manuelle Versions-/Dateiaktivierung wurde
entfernt. Der explizite Operator vergibt den ersten `manage_submitters`-Auftrag:

```sh
python3 scripts/compose_operator.py bootstrap-submitters <private-request.json>
```

Scope-/Dateivertrag und aktueller Phasenstand:
[MA-G2 Backend](implementation/storage-and-delivery/MA-G2_BACKEND.md).
Kein Aufruf beim Normalstart und keine automatische Rechtevergabe.

Der frühere Legacy-Metadatenimport ist entfernt. Ein alter Storagebestand wird
nicht durch normales Setup oder Start migriert: diese Befehle verlangen die
geprüfte explizite MA-G1-Umstellung. Normales Setup erzeugt bei frischen Instanzen
den privaten Bucket sowie getrennte Writer-/Readerkeys. Wiederholtes Setup
behält vorhandene Keys, Secrets, Objekte und Fachdaten; unbekannte Zuordnungen
oder fehlende bekannte Ressourcen verursachen einen geschlossenen Fehler.

Normalstart führt keine Schemaänderung, Seeds, Purges oder Portalreloads aus.
Der CSV-Verarbeitungsweg wird erst nach den jeweils unabhängigen MA-G2–G4-
Abnahmen freigeschaltet. Historische Ladebelege bleiben an ihren bisherigen Orten.

`smoke-test.sh` liest nur den gewählten aktiven Kontext. Phasentests entstehen
explizit isoliert über `test-consolidation.sh --phase MA-F1/MA-F2/MA-F3/MA-F4`.
Historische Grundinstallations-/Zweiinstanz-Testlauncher sind retired und melden
keinen irreführenden PASS. Ihre Implementierung/Nachweise bleiben in der Git-
und Dokumentationshistorie; Modelle, Fach-/Auditverträge und Javafachtests bleiben.
