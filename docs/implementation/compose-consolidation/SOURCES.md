# Quellen und Evidenzgrenzen

**Geprüft am 4. November 2026.** Repositoryquellen wurden gelesen; Docker-/Migrations-/Anwendungstests wurden bei der Erstellung dieses Pakets **nicht** ausgeführt. Die Laufzeitbedingungen sind vom Coding-Agenten auf dem tatsächlichen lokalen Stand zu prüfen. Frühere Reviewberichte sind als fremde Nachweise gekennzeichnet.

## 1. Konkrete Repositorybasis

- [STACK/compose.yaml](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/465d7c4f7302037cdddd69e20139822e68b8cdfe/compose.yaml): Foundation-Services; PG16.10-alpine; APISIX `network_mode: service:jenkins`; Sodata `manifest`; Keycloak bereits PostgreSQL; separater rclone-HTTP-Browser.
- [STACK/scripts/up.sh](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/465d7c4f7302037cdddd69e20139822e68b8cdfe/scripts/up.sh): bisheriger Start, getrennte Initjobs, öffentlicher Browserkey, Publikationsbootstrap als Portalvoraussetzung.
- [STACK/Postgres-Initialisierung](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/465d7c4f7302037cdddd69e20139822e68b8cdfe/services/postgres/init/initialize.sh): getrennte Foundation-DBs/Rollen und Negativtestobjekt; noch keine Managementdatenbank.
- [STACK/Realmvorlage](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/465d7c4f7302037cdddd69e20139822e68b8cdfe/services/keycloak/realm-template.json): feste Demo-User-UUIDs; keine Aussage über seit Erststart eingetretene Runtimeänderungen.
- [STACK/AGENTS](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/465d7c4f7302037cdddd69e20139822e68b8cdfe/AGENTS.md): aktive und historische Einstiegsvorgaben. Gezielt ergänzen, nicht blind ersetzen.
- [ADMIN/managed_runtime.py](https://github.com/sogis/dateninfrastruktur-admin/blob/7986d67330fd6a304d98d2c4e73aa38d139bde4a/scripts/managed_runtime.py): direkte Dockerorchestrierung, zwei Instanzen, eigener Keycloak ohne explizite PostgreSQL-Anbindung, Garage, Origin, Token-/Pfadvertrag und Operatoraktivierung.
- [ADMIN/management_db.py](https://github.com/sogis/dateninfrastruktur-admin/blob/7986d67330fd6a304d98d2c4e73aa38d139bde4a/scripts/management_db.py): gepinntes PG16/PostGIS, MA-B-Label-/Containerbindung, separate Schema-/Mappingoperationen.
- [ADMIN/setup.py](https://github.com/sogis/dateninfrastruktur-admin/blob/7986d67330fd6a304d98d2c4e73aa38d139bde4a/scripts/setup.py): Schema, Rollen, Audit, Constraints, Mapping und Upgrade; heute noch an eigenen Harness gebunden.
- [ADMIN/schema-lifecycle.md](https://github.com/sogis/dateninfrastruktur-admin/blob/7986d67330fd6a304d98d2c4e73aa38d139bde4a/docs/schema-lifecycle.md): dokumentierte PG16.9/PostGIS3.5.2-Laufzeit, ili2pg5.5.2, tatsächliche Tabellen-/OID-/PK-/Cayenne-/Auditverträge.
- [MA-E-Review](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/465d7c4f7302037cdddd69e20139822e68b8cdfe/docs/implementation/management-and-access/review/MA-E-accepted.md): frühere unabhängige funktionale Prüfung. Keine eigene neue MA-F-Abnahme und kein Beweis einer Compose-Konsolidierung.
- [ADMIN-Lizenzmerge](https://github.com/sogis/dateninfrastruktur-admin/commit/7986d67330fd6a304d98d2c4e73aa38d139bde4a): zusätzliches LICENSE gegenüber der geprüften MA-E-Produktbasis.

Die Folgephase enthält bewusst neue Entscheidungen: ein gemeinsamer PG, eine Instanz je Dienst, eindeutiger Composebetrieb, kontrollierter Cutover. Diese sind kein behaupteter bereits vorhandener Quellzustand.

## 2. PostgreSQL/PostGIS

- [PostGIS aktivieren](https://postgis.net/documentation/getting_started/): PostGIS als DB-Erweiterung. Vorhandene Binaries erlauben normale PostgreSQL-Datenbanken ohne fachliche GIS-Nutzung.
- [PostgreSQL16 CREATE EXTENSION](https://www.postgresql.org/docs/16/sql-createextension.html): Extensionobjekte und Voraussetzungen pro Datenbank.
- [PostgreSQL16 pg_dump](https://www.postgresql.org/docs/16/app-pgdump.html): konsistente Sicherung einer Datenbank; Globalobjekte sind separat zu behandeln.
- [PostgreSQL16 pg_restore](https://www.postgresql.org/docs/16/app-pgrestore.html): Restore von Archiven, Owner/ACL-/Daten-/Sequenzoptionen, Fehlerabbruch. Ein Archiv allein beweist keinen erfolgreichen Restore.
- [PostgreSQL16 ALTER COLLATION](https://www.postgresql.org/docs/16/sql-altercollation.html): Auswirkungen unterschiedlicher Collationversionen. Kein ungeprüfter Datadirwechsel zwischen verschiedenen Imagebasen.

## 3. Identität und Anwendungszustand

- [Keycloak-Datenbankkonfiguration](https://www.keycloak.org/server/db): explizite PostgreSQL-Konfiguration; Standard `dev-file` ist Entwicklungsdatenhaltung.
- [Keycloak-Import/Export](https://www.keycloak.org/server/importExport): konsistenter Export bei gestoppten Nodes, Einschränkungen gegenüber vollständiger Sicherung, existierende Realms werden beim Startupimport übersprungen.
- [Superset-Konfiguration](https://superset.apache.org/admin-docs/configuration/configuring-superset/): SECRET_KEY schützt unter anderem gespeicherte sensitive Verbindungsinformationen; bei Übernahme erhalten oder kontrolliert rotieren.

## 4. Docker Compose

- [Services](https://docs.docker.com/reference/compose-file/services/): deklarative Services, Compose-Labels, Netzwerke, Healthchecks, Profiles.
- [Startup-Reihenfolge](https://docs.docker.com/compose/how-tos/startup-order/): Bedingungen `service_healthy` und `service_completed_successfully`; gestarteter Prozess ist nicht gleich bereit.
- [Compose up](https://docs.docker.com/reference/cli/docker/compose/up/): Neuerstellung bei geändertem Image/Config, Erhalt gemounteter Volumes.
- [Volumes](https://docs.docker.com/reference/compose-file/volumes/): ausdrücklich benannte persistente Volumes und Projektzuordnung.

Keine allgemeine Produktfeaturegarantie ersetzt Tests gegen die tatsächlich eingesetzten Versionen. Insbesondere Image-Digests/Architektur, Keycloak-Benutzerübernahme und Schutzpfade müssen lokal belegt werden.
