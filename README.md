# dateninfrastruktur-dev-stack

Lokale, eigenständige Grundinstallation der Dateninfrastruktur des Kantons
Solothurn. Der Stack baut Jenkins/GRETL, Sodata und Superset aus den fünf neuen
Geschwisterrepos und ergänzt Garage, APISIX, PostgreSQL, Keycloak und
ClickHouse. Alle veröffentlichten Hostports sind ausschliesslich an Loopback
gebunden.

## Voraussetzungen

- macOS oder Linux mit nativer CPU-Architektur (getestet auf macOS arm64)
- Docker Engine/Desktop mit Docker Compose v2 (`docker compose version`)
- Bash, Git, OpenSSL, `curl`, Python 3, `jq` für die Diagnose
- Für lokale Builds: Java 21 (Jenkins/Plugin) und Java 17 (GRETL/Gradle);
  die Skripte finden SDKMAN-Installationen automatisch. Sodata, Superset,
  Keycloak, ClickHouse und PostgreSQL werden vollständig in Containern gebaut.
- Internetzugang beim ersten Build für offizielle Images, Maven/Gradle/npm und
  die im Themenrepo manifestierten INTERLIS-Modelle.

Die fünf Repos müssen als Geschwister im gemeinsamen Arbeitsordner liegen:

```text
dateninfrastruktur/
├── dateninfrastruktur-dev-stack/       # dieser Stack
├── dateninfrastruktur-sodata/
├── dateninfrastruktur-jenkins-dev/
├── dateninfrastruktur-jenkins-gretl-plugin/
└── dateninfrastruktur-themenrepo/
```

## Einmalige lokale Konfiguration

```bash
cd dateninfrastruktur-dev-stack
./scripts/init.sh
```

`init.sh` erzeugt `.env` mit Zufallswerten, `services/garage/garage.toml`
(nicht versioniert) und `keycloak-realm.json` unter `.runtime/`. Vorhandene
Werte werden nie automatisch ersetzt. `.env` und `.runtime/` sind ignoriert und
dürfen nicht in Git oder Berichte gelangen.

Wichtige Portvariablen in `.env`:

| Dienst | Variable | Standard |
|---|---|---|
| Portal/Gateway/Jenkins | `GATEWAY_PORT` | `18081` |
| Garage S3 API | `GARAGE_S3_PORT` | `13900` |
| Keycloak | `KEYCLOAK_PORT` | `18080` |
| Superset | `SUPERSET_PORT` | `18088` |
| ClickHouse HTTP/JDBC | `CLICKHOUSE_HTTP_PORT` | `18123` |
| ClickHouse Native (optional) | `CLICKHOUSE_NATIVE_PORT` | `19000` |
| PostgreSQL | intern | kein Hostport |

Für eine zweite Instanz müssen `COMPOSE_PROJECT_NAME`, `RUNTIME_DIR` und alle
Portvariablen gemeinsam geändert werden. Ein anderer Projektname allein trennt
keine schreibbaren Hostpfade.

## Bauen und starten

Der eine unterstützte Standardweg:

```bash
./scripts/up.sh
```

Das Skript führt aus:

1. lokale Konfiguration prüfen/erzeugen,
2. `dateninfrastruktur-jenkins:local` aus Jenkins-Dev, Plugin und Themenrepo
   bauen (inklusive Offline-GRETL-/Modellbundle),
3. `dateninfrastruktur-sodata:local` mit Dockerfile-Target `jvm-runtime` bauen,
4. `dateninfrastruktur-superset:local` mit ClickHouse- und PostgreSQL-Treiber
   bauen,
5. Garage, PostgreSQL, ClickHouse, Keycloak, Superset, Jenkins, APISIX und
   Sodata starten,
6. den Seedjob ausführen, die lokale Erstpublikation erzeugen und Sodata erst
   danach starten.

Bereits gebaute lokale Images verwenden:

```bash
./scripts/up.sh --skip-build
```

Nur bauen, nicht starten:

```bash
./scripts/up.sh --build-only
```

Nur die Infrastruktur starten, ohne Seed/Erstpublikation:

```bash
./scripts/up.sh --infrastructure-only
```

`--registry-only`, der frühere Editor-/Dokumentationsbuild und alte
Datenportal-Images sind bewusst nicht Teil dieses Wegs. `--registry-only`
bricht mit Exitcode 2 und einer erklärenden Meldung ab.

## URLs und lokale Zugänge

| Ziel | Adresse |
|---|---|
| Portal | http://localhost:18081/ |
| Jenkins-Anlieferung | http://localhost:18081/anlieferung |
| Jenkins-Administration | http://localhost:18081/jenkins/ |
| Öffentlicher Bucket | http://localhost:18081/ch.so.daten/ |
| Aktueller Publikationsstand | http://localhost:18081/ch.so.daten/current.json |
| S3 API | http://localhost:13900 |
| Keycloak | http://localhost:18080 |
| Superset | http://localhost:18088 |
| ClickHouse HTTP/JDBC | http://localhost:18123 |

Zugangsdaten stehen ausschliesslich in der ignorierten `.env`. Sie werden
nicht in diesem README, in Berichten oder in Git veröffentlicht. Für lokale
Werkzeuge die Variablen gezielt laden, ohne sie auszugeben:

```bash
set -a
source .env
set +a
```

- Jenkins: Benutzer `admin`, Passwort `JENKINS_ADMIN_PASSWORD`.
- Superset: Benutzer `admin`, Passwort `SUPERSET_ADMIN_PASSWORD`.
- Keycloak-Administration: Benutzer `admin`, Passwort `KEYCLOAK_ADMIN_PASSWORD`.
  Realm `dateninfrastruktur` mit den erfundenen Benutzern `anna`, `ben` und
  `claudia`; gemeinsames Testpasswort `KEYCLOAK_DEMO_PASSWORD`.
- ClickHouse-Administration: `ch_admin` /
  `CLICKHOUSE_ADMIN_PASSWORD`; Bootstrap-Benutzer `default` /
  `CLICKHOUSE_DEFAULT_PASSWORD`.
- ClickHouse-Testleser: `ch_test_reader` /
  `CLICKHOUSE_TEST_READER_PASSWORD`.
- ClickHouse-Superset-Leser: `superset_reader` /
  `CLICKHOUSE_SUPERSET_READER_PASSWORD`.
- PostgreSQL-Anwendungsrollen: `keycloak` / `KEYCLOAK_DB_PASSWORD` und
  `superset` / `SUPERSET_DB_PASSWORD`; der Cluster hat keinen Hostport.

## Status, Logs und Diagnose

```bash
./scripts/status.sh
./scripts/logs.sh              # letzte 200 Zeilen aller Dienste
./scripts/logs.sh clickhouse   # gezielt ein Dienst
docker compose ps
docker compose exec -T clickhouse clickhouse-client \
  --user ch_admin --password "$CLICKHOUSE_ADMIN_PASSWORD" \
  --query 'SELECT count() FROM foundation.smoke_metrics'
```

Der Bootstrap-Zustand liegt unter
`.runtime/dateninfrastruktur-dev-stack/bootstrap.json`; das Publikationslog
unter `.runtime/dateninfrastruktur-dev-stack/publication.log`. Diese Dateien
bleiben lokal und werden nicht versioniert.

## Technische Tests

```bash
./scripts/verify-foundation.sh
```

Dieses Kommando prüft in einem Lauf:

- Loopback-Bindung, PostgreSQL ohne Hostport, lokale Images und
  instanzspezifische Volumes,
- öffentlichen S3-Upload, öffentlichen Leseschlüssel, Schreibverweigerung,
  Range/CORS und Gateway-Sperren,
- Jenkins-Login, aktives GRETL-Plugin, erfolgreichen Seedjob,
  Startformular inklusive CSS/JS,
- gültiges `current.json`, echte DuckDB und Portal-Readiness,
- getrennte PostgreSQL-Rollen und verweigerte Fremdzugriffe,
- Keycloak-Realm, drei stabile Benutzer-IDs, Discovery und JWKS,
- ClickHouse-Testtabellen, erlaubte Leser und verweigerte Zugriffe auf
  `restricted_metrics`, INSERT, DDL, GRANT und anonyme Anmeldung,
- JDBC-Zugang über den veröffentlichten Port mit dem dokumentierten Treiber,
- Superset-Metadaten in PostgreSQL, Superset-Treiberabfrage mit
  eingeschränktem Konto und Login,
- berechtigten Zugriff auf das private Testobjekt und die drei verbotenen
  öffentlichen Wege.

Einzelprüfungen:

```bash
./scripts/smoke-test.sh
./scripts/test-postgres.sh
./scripts/test-keycloak.sh
./scripts/test-clickhouse.sh
./scripts/test-jdbc.sh
./scripts/test-superset.sh
./scripts/test-private-storage.sh
./scripts/test-isolation-config.sh
./scripts/test-isolation-run.sh
./scripts/test-restart.sh
```

`test-restart.sh` stoppt den Stack ohne Volume-Löschung, startet ihn mit
`--skip-build --no-bootstrap` neu und vergleicht Secrets, Release-ID,
Keycloak-Benutzer-IDs, Superset-Verbindung, Jenkins-Jobs und eine nach der
Initialisierung ergänzte ClickHouse-Zeile. Nur das Ergebnis wird protokolliert,
niemals ein Secret oder dessen Hash.

`test-isolation-run.sh` startet einen zweiten, vollständig getrennten
Teilstapel (`dateninfrastruktur-review-r001`) mit eigenen Ports, eigenem
Runtime-Verzeichnis, eigenen Secrets und eigenen Volumes. Nach den Prüfungen
werden ausschliesslich diese temporären Reviewressourcen mit `down -v`
bereinigt.

## JDBC und DBeaver

Getesteter Treiber: `com.clickhouse:clickhouse-jdbc:0.9.0:all`
(SHA256 wird von `scripts/test-jdbc.sh` ausgegeben).

| Feld | Wert |
|---|---|
| Host | `127.0.0.1` |
| Port | `18123` (HTTP) |
| Datenbank | `foundation` |
| JDBC-URL | `jdbc:clickhouse://127.0.0.1:18123/foundation` |
| Benutzer | `ch_test_reader` |
| Passwort | Variable `CLICKHOUSE_TEST_READER_PASSWORD` in `.env` |
| Treiberklasse | `com.clickhouse.jdbc.ClickHouseDriver` |

Der automatisierte Nachweis läuft über den veröffentlichten Hostport, nicht
nur innerhalb des Containers:

```bash
./scripts/test-jdbc.sh
```

Eine zusätzliche DBeaver-UI-Prüfung ist möglich, aber nicht Voraussetzung.
Der technische JDBC-Test und die dokumentierte URL sind der abgenommene Pfad.
Der Leser darf `foundation.smoke_metrics` lesen; `restricted_metrics`, INSERT,
DDL und GRANT werden aus dem Berechtigungsgrund verweigert. Der native Port
`19000` ist optional und nicht der Standardweg.

## Stoppen, Wiederanlauf und Bereinigung

```bash
./scripts/down.sh
```

Ein reguläres Stoppen löscht keine Volumes. Jenkins-Jobs, Publikationsstand,
Keycloak-Identitäten, Superset-Metadaten und ClickHouse-Daten bleiben erhalten.
Ein erneuter Start mit `./scripts/up.sh --skip-build` prüft den vorhandenen
Publikationsstand und erzeugt keinen neuen Erststand.

Nur für einen ausdrücklich eigenen temporären Reviewstack darf gezielt
gelöscht werden, beispielsweise:

```bash
docker compose -p dateninfrastruktur-review-r001 \
  --env-file .runtime/dateninfrastruktur-review-r001/review.env \
  down -v --remove-orphans
```

Kein `docker system prune`, kein `down -v` gegen die Arbeitsinstanz und keine
Bereinigung fremder Container oder Volumes.

## Architektur und Grenzen

- Garage hält den öffentlichen Bucket `ch.so.daten` und den privaten Bucket
  `ch.so.dateninfrastruktur.private`. Der öffentliche Browser/rclone liest nur
  `ch.so.daten`; der private Bucket hat keine Websitefreigabe und keine
  Gateway-Route.
- APISIX läuft im Netzwerk-Namespace des Jenkins-Containers. Der Gateway-Port
  wird deshalb am Jenkins-Container veröffentlicht. Interne Manifest-URLs
  verwenden `http://jenkins:<GATEWAY_PORT>/...`, Browser-URLs
  `http://localhost:<GATEWAY_PORT>/...`.
- Jenkins läuft im lokalen `dev`-Modus mit eigenem JCasC. Git-Writeback ist
  aus; E-Mail-Benachrichtigungen sind deaktiviert. Die technische Plugin-ID
  ist `jenkins-gretl-dateninfrastruktur-plugin`; der JCasC-Schlüssel
  `gretlDatenportalJobs`, der Schritt `prepareDatenportalWorkspace` und der
  Seedjob `gretl-datenportal-seed` bleiben als Kompatibilitätsverträge erhalten.
- Sodata verwendet den Gradle-/App-Namen `dateninfrastruktur-sodata` und das
  Dockerfile-Target `jvm-runtime`. Explore ist über
  `DATENINFRASTRUKTUR_EXPLORE_ENABLED=false` deaktiviert.
- Keycloak ist vorbereitet, aber noch nicht als OIDC-Login in Portal, Jenkins
  oder Superset integriert. Ein Keycloak-Benutzer erzeugt keine Superset- oder
  ClickHouse-Rechte.
- Superset verwendet einen lokalen Administrator und ein eingeschränktes
  technisches ClickHouse-Konto. Es gibt kein Redis, keinen Celery-Worker und
  keine öffentlichen Dashboards.
- PostgreSQL enthält getrennte Datenbanken und Rollen für Keycloak und
  Superset. Die Rollen sind keine Superuser und dürfen fremde
  Anwendungsdatenbanken nicht lesen.
- Nicht Teil dieser Etappe: Portal-Freigabeprozess, SSO-Ausbau, LDAP-/AIO-
  Import, fachliche CSV-Pipeline nach ClickHouse, Historisierung, Dashboards
  und Agentic BI.

## Troubleshooting

- **Jenkins-Plugin wird nicht geladen:** `./scripts/logs.sh jenkins` prüfen;
  das Plugin muss als `/var/jenkins_home/plugins/jenkins-gretl-dateninfrastruktur-plugin.jpi`
  mit dem im Image gebauten HPI übereinstimmen. `./scripts/up.sh --skip-build`
  synchronisiert das Image-Plugin erneut.
- **Seedjob schlägt fehl:** Jenkins-Build-Log und
  `.runtime/.../publication.log` prüfen. Der Seed liest das Themenrepo unter
  `/workspace/themenrepo`; fehlende Modelle werden über
  `shared/gradle/publication-models.json` mit SHA256-Prüfung geladen.
- **Sodata startet nicht:** Sodata benötigt ein vorhandenes `current.json`.
  Zuerst `./scripts/bootstrap.sh` ausführen. Bei einem vorhandenen
  Publikationsstand startet Sodata auch ohne neuen Seed.
- **Superset bleibt unhealthy:** `./scripts/logs.sh superset` prüfen. Die
  Metadatenbank muss migriert sein; die gespeicherte ClickHouse-Verbindung
  heißt `clickhouse_foundation`.
- **Port belegt:** In `.env` alle Portvariablen gemeinsam ändern und den Stack
  neu erstellen. `GATEWAY_PORT=8080` ist ungültig, weil Jenkins intern 8080
  verwendet.
- **Keycloak-Realm nach Neustart:** Der Import verwendet
  `IGNORE_EXISTING`; ein vorhandener Realm und seine Benutzer werden nicht
  zurückgesetzt. Die stabilen IDs stehen im Realm-Template.
