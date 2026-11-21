# Lokaler Betrieb der Dateninfrastruktur

## Admin-Webentwicklung: vom Checkout zur ersten Änderung

### Ersteinrichtung auf macOS

Klone den [Workspace](https://github.com/sogis/dateninfrastruktur-workspace)
und führe dort `./workspace clone` aus. Wechsle dann in
`dateninfrastruktur-dev-stack`. Der Admin-Checkout liegt daneben.

Verwende Bash, Docker Desktop mit Compose ab 2.24.4, Python ab 3.9 und
Java 25. Prüfe den lokalen Docker-Kontext mit `docker context ls` und
`docker info`. Bei einer neuen Instanz müssen die Standardports
`8080`, `15432`, `18080`, `18081`, `18088`, `18090`, `18123` und
`19000` frei sein. Auf macOS kannst du etwa den Admin-Port mit
`lsof -nP -iTCP:8080 -sTCP:LISTEN` prüfen.

Die folgenden Befehle erzeugen eine eigene Instanz, laden die
Infrastruktur-Images und importieren synthetische Beispieldaten in die
leere Management-Datenbank. `bootstrap-dev` bindet den Principal für Anna
und das GRETL-Servicekonto an den lokalen Keycloak-Realm. Behalte den Pfad
zu dieser privaten `runtime.env` für spätere Sitzungen.

```bash
export DOCKER_CONTEXT=desktop-linux
runtime_env=$(python3 scripts/compose_runtime.py init meine-dev-instanz --host-admin)
runtime_dir=$(dirname "$runtime_env")
host_compose=(docker compose --env-file "$runtime_env" -f compose-test.yaml -f compose.yaml)

"${host_compose[@]}" config --quiet
"${host_compose[@]}" --profile setup pull
python3 scripts/setup_instance.py --env "$runtime_env"
"${host_compose[@]}" up -d --wait --wait-timeout 180 --no-build --pull never keycloak

install -m 600 ../dateninfrastruktur-admin/tests/fixtures/management-bootstrap.xtf "$runtime_dir/bootstrap.xtf"
python3 scripts/compose_operator.py bootstrap-dev "$runtime_dir/bootstrap.xtf" --env "$runtime_env"
admin_config=$(python3 scripts/compose_runtime.py admin-host-config --env "$runtime_env")
"${host_compose[@]}" up -d --wait --wait-timeout 300 --no-build --pull never
```

Starte Admin im benachbarten Checkout mit Java 25. Der Befehl läuft im
Vordergrund. In der IDE verwendest du dieselben zwei Umgebungsvariablen
und den Admin-Checkout als Arbeitsverzeichnis.

```bash
(
  cd ../dateninfrastruktur-admin
  SPRING_PROFILES_ACTIVE=host-dev SPRING_CONFIG_ADDITIONAL_LOCATION="file:$admin_config" ./gradlew bootRun
)
```

Sobald Admin gestartet ist, öffne das [Management am Gateway](http://localhost:18081/management)
und melde dich als `anna` an. Verwende `localhost` und den
`GATEWAY_PORT` aus deiner Instanz, standardmässig `18081`. Das
zufällige Passwort steht in
`KEYCLOAK_DEMO_PASSWORD` in deiner privaten `runtime.env`. Unter macOS
kannst du es für die Anmeldung direkt in die Zwischenablage kopieren.

```bash
sed -n 's/^KEYCLOAK_DEMO_PASSWORD="\([0-9a-f]*\)"$/\1/p' "$runtime_env" | tr -d '\n' | pbcopy
```

### Erste Änderung und passender Test

Suche nach `test-open`, öffne **Synthetisch open** und wähle
**Metadaten bearbeiten**. Ändere den Titel und trage im Pflichtfeld
**E-Mail des Kontakts** eine synthetische Adresse wie
`kontakt@example.invalid` ein. Die Vorlage lässt dieses Feld leer.
Wähle **Metadaten speichern** und lade die Detailseite neu. Der neue
Titel soll weiterhin sichtbar sein.

Die Route `/management` führt im Admin-Checkout zu `DatasetController`
im Java-Paket `ch.so.agi.dateninfrastruktur.admin.web`. Er lädt die
Datensatzliste und gibt die JTE-Vorlage `dataset/list` zurück. Ändere
vorübergehend den Einführungstext in `src/main/jte/dataset/list.jte`,
lade `/management` neu und prüfe den geänderten Text. Nimm deine Änderung
danach zurück. Die Styles liegen in
`src/main/resources/static/assets/management.css`.

Führe im Admin-Checkout mit Java 25 `./gradlew test` für die schnellen
Tests aus. Für Änderungen an der Oberfläche läuft `ManagementBrowserIT`
mit Playwright und Chromium. Beim ersten Lauf kann Playwright Chromium
herunterladen. Die Klasse läuft mit einer eigenen Web-Fixture unabhängig
vom Compose-Stack.

```sh
./gradlew integrationTest --tests '*ManagementBrowserIT'
```

Im Dev-Stack prüft `python3 scripts/test_host_development.py` das
Compose-Modell für den Host-Modus. Für Änderungen am Zusammenspiel von
Gateway, Keycloak-Login und Admin startet
`python3 scripts/test_stack_management.py` eine eigene Instanz mit
[lokal gebauten Images](#images-bereitstellen).

### Täglicher Ablauf

Setze `runtime_env` in einer neuen Shell auf die Datei der eingerichteten
Instanz und definiere dort das Array `host_compose` wie oben. Starte im
Stack-Checkout die Infrastruktur und in einem eigenen Terminal den Admin.

```bash
"${host_compose[@]}" up -d --wait --wait-timeout 300 --no-build --pull never
admin_config="$(dirname "$runtime_env")/admin-host.properties"
(
  cd ../dateninfrastruktur-admin
  SPRING_PROFILES_ACTIVE=host-dev SPRING_CONFIG_ADDITIONAL_LOCATION="file:$admin_config" ./gradlew bootRun
)
```

In der IDE verwendest du Java 25, den Admin-Checkout als Arbeitsverzeichnis,
die Spring-Boot-Hauptklasse und dieselben zwei Umgebungsvariablen.
Starte mit dem Debugger, wenn du Breakpoints brauchst. Kompiliere
geänderte Java-Dateien in der IDE, damit DevTools den Spring-Kontext
neu startet. Bei Gradle kannst du in einem zweiten Terminal im Admin-Repo
`./gradlew compileJava` ausführen. Speichere JTE unter `src/main/jte` und CSS
unter `src/main/resources/static/assets` und lade die Seite im Browser neu.

Öffne [Management im Gateway](http://localhost:18081/management).
APISIX und Jenkins erreichen Admin auf Docker Desktop als `admin:8080`.
Admin bindet sich am Mac an `127.0.0.1:8080` und verwendet
PostgreSQL auf `127.0.0.1:15432`, Keycloak auf `localhost:18080` und
Origin auf `127.0.0.1:18090`. Falls du diese Infrastrukturports in
`runtime.env` änderst, erzeuge die private Admin-Konfiguration erneut.
Die Keycloak- und Gateway-Ports gehören zur ursprünglichen Instanzkonfiguration.

Beende Admin mit der IDE oder mit Ctrl-C und stoppe die Infrastruktur.

```bash
"${host_compose[@]}" stop
# Container und Netzwerk entfernen, Named Volumes behalten
"${host_compose[@]}" down --timeout 60
```

Beim Wechsel von Container-Admin auf Host-Admin entferne den Container
einmal gezielt im bisherigen Projekt. Die `runtime.env` bleibt dieselbe.

```bash
docker compose --env-file "$runtime_env" -f compose-test.yaml rm -s -f admin
```

## GRETL-Job entwickeln

Mit benachbartem Jenkins-Checkout im Stack-Verzeichnis ausführen.

```bash
export GRETL_JOB_DIR=$(cd ../dateninfrastruktur-jenkins-dev/jobs/csv-delivery && pwd)
gretl_compose=("${host_compose[@]}" -f compose.gretl-dev.yaml)
"${gretl_compose[@]}" up -d --wait --wait-timeout 300 --no-build --pull never
```

Compose übernimmt den schreibgeschützten Mount, wenn du das Overlay
aktivierst. Bearbeite anschliessend `job.groovy` oder `append.sql` im
Checkout. GRETL liest die Dateien bei der nächsten Ausführung erneut.
Verwende beim Start weiterhin dasselbe Overlay, solange du lokale
Jobquellen brauchst.

Erzeuge eine Beispiel-CSV und lade sie unter
[Anlieferung im Gateway](http://localhost:18081/anlieferung) als Anna für
die angebotene Beispielausgabe im Modus **Ersetzen** hoch.

```bash
printf 'zone,code\nA,1\n' > "$runtime_dir/example.csv"
"${gretl_compose[@]}" logs --tail 100 jenkins 2>&1 |
  python3 scripts/compose_runtime.py redact --env "$runtime_env"
```

Die Lieferseite zeigt den Status und den Validierungsbericht. Nach der
Annahme zeigt [die Management-Lieferübersicht](http://localhost:18081/management/delivery)
die Submission. Der resultierende CSV-Snapshot liegt im privaten
Garage-Bucket und die Tabelle `default.snapshot_<Submission-ID ohne Bindestriche>`
in ClickHouse.

## Images für den Host-Modus

Die Image-Versionen für den Host-Modus stehen in `compose.yaml`.
Explizite Image-Variablen in deiner privaten `runtime.env` haben Vorrang.
Zeige die gewählten Images einschliesslich Setup-Werkzeugen und optionalem
Container-Admin mit Compose an.

```bash
"${host_compose[@]}" --profile setup --profile container-admin config --images | sort -u
```

## Container-Admin und Integrationstests

Der Stack verbindet Admin, Sodata und Jenkins aus Schwestercheckouts mit
PostgreSQL/PostGIS, Garage, ClickHouse, Keycloak, Superset und APISIX.
Instanzdateien und Secrets liegen privat unter `.runtime/`.
Hostports sind an die Loopback-Adresse gebunden.

### Lokale Integrationsinstanz anlegen

Benötigt werden Docker mit Compose und Buildx sowie Python ab 3.9.
Arbeite im Stack-Checkout mit dem gewünschten lokalen Docker-Kontext. Eine
saubere Shell hält geerbte Compose-Overrides aus der Instanzkonfiguration fern.

```bash
env -i HOME="$HOME" PATH="$PATH" DOCKER_CONTEXT=desktop-linux bash --noprofile --norc
runtime_env=$(python3 scripts/compose_runtime.py init meine-dev-instanz)
runtime_dir=$(dirname "$runtime_env")
project=$(basename "$runtime_dir")
```

`init` ergänzt den Präfix um einen Zufallssuffix. Verwende für diese Instanz
bei späteren Sitzungen dieselbe `runtime.env`. Führe Setup getrennt vom
regulären Start aus.

Compose leitet die Volume-Namen vom Projektnamen ab. PostgreSQL
verwendet beispielsweise `<projekt>_postgres-data` statt des bisherigen
`<projekt>_postgres`. Öffne frühere Projekte mit ihrem bisherigen Checkout und
ihrer bisherigen `runtime.env`. Verwende für den aktuellen Stack ein Projekt mit projektbezogenen Volumes.
Setup und Startprüfung weisen Konfigurationen mit den alten Volume-Variablen
ab. Bestehende Volumes bleiben erhalten. Eine Datenübernahme erfordert einen
eigenen Auftrag.

### Images bereitstellen

Für lokale Builds müssen Admin und Sodata neben dem Stack ausgecheckt sein.
Der separate Jenkins-Build benötigt zusätzlich die Jenkins- und
Plugin-Checkouts, Java 21 und Maven. Admin und Sodata werden im Container
mit Java 25 gebaut.

```bash
docker compose -f compose-test.yaml --env-file "$runtime_env" --profile build-tools build postgres admin sodata superset management-tool-build
docker compose -f compose-test.yaml --env-file "$runtime_env" pull --policy missing garage clickhouse keycloak origin gateway
build_dir=$(mktemp -d "$runtime_dir/jenkins-build.XXXXXXXX")
JAVA21_HOME=/pfad/zu/java-21 IMAGE_NAME="dateninfrastruktur-jenkins:$project" \
  ../dateninfrastruktur-jenkins-dev/bin/build-image.sh "$build_dir/context"
```

Für Registry-Images setze `ADMIN_IMAGE`, `JENKINS_IMAGE`, `POSTGRES_IMAGE`,
`SUPERSET_IMAGE`, `TOOL_IMAGE` und `SODATA_IMAGE` in der privaten
`runtime.env`. Die veröffentlichten Standardreferenzen findest du im
[Entwickler-Overlay](../compose.yaml). Das Jenkins-Image muss
GRETL `6.0.0-SNAPSHOT` tragen.

```bash
docker compose -f compose-test.yaml --env-file "$runtime_env" --profile setup pull --policy missing
```

### Setup und Start

```bash
python3 scripts/setup_instance.py --env "$runtime_env"
```

Setup richtet PostgreSQL, Garage und ClickHouse ein. Mit derselben privaten
Konfiguration kann es erneut ausgeführt werden. Vorhandene Garage- und
ClickHouse-Zugangsdaten bleiben erhalten.

Nach erfolgreichem Setup startet der Stack mit derselben Datei. Die
Startprüfung startet bei Bedarf PostgreSQL, liest den Schemazustand und
bindet Jenkins an die geprüfte Image-ID. Bei einem inkompatiblen Schema bleibt
der Zustand der laufenden Anwendungen erhalten.

```bash
jenkins_id=$(python3 scripts/compose_runtime.py preflight --env "$runtime_env") &&
  JENKINS_IMAGE="$jenkins_id" docker compose -f compose-test.yaml --env-file "$runtime_env" up -d --wait --wait-timeout 300 --no-build --pull never
```

### Status, Logs und Stopp

```bash
docker compose -f compose-test.yaml --env-file "$runtime_env" ps
set -o pipefail
docker compose -f compose-test.yaml --env-file "$runtime_env" logs --tail 100 -f admin 2>&1 |
  python3 scripts/compose_runtime.py redact --env "$runtime_env"
docker compose -f compose-test.yaml --env-file "$runtime_env" down --timeout 60
```

Mit `stop` bleiben auch die Container erhalten. `down` behält die
Compose-Volumes für den nächsten Start. Behandle auch redigierte Logs
vertraulich. Prüfe das Compose-Modell mit `config --quiet`.

### Instanz bewusst zurücksetzen

Der folgende Befehl löscht die Daten in allen Compose-Volumes der ausgewählten
Instanz. Vergewissere dich vorher, dass die private Datei zur gewünschten
Instanz gehört. Beginne danach mit einem neuen `init`, neuen Zugangsdaten und
explizitem Setup. Die bisherige private Konfiguration enthält weiterhin ihre
Garage-Bindung.

```bash
docker compose -f compose-test.yaml --env-file "$runtime_env" --profile '*' down --volumes --remove-orphans
```

## Katalog und Lieferung

Das explizite Management-Setup legt das Schema aus den vier
INTERLIS-Modellen im Admin-Repo an. Das lokale Tooling-Image enthält
ili2pg 5.5.2 und ilivalidator 1.15.1. Beim Tooling-Build liefert der
Stack-Kontext die PostgreSQL- und Garage-Setup-Skripte.
Die erste fachliche Belegung kommt aus einem geprüften
[XTF-Transfer](https://github.com/sogis/dateninfrastruktur-admin/blob/main/docs/schema-lifecycle.md).
Dort werden auch die ersten Principals und deren Rechte angelegt.

Unter `/management` werden Datensätze, Ausgaben und ihre Publikation
verwaltet. Unter `/management/delivery` werden CSV-Schema,
Lieferkonfiguration, Lieferrechte und Submissions verwaltet.
Sodata liest die veröffentlichten Katalogdaten direkt aus PostgreSQL.
APISIX prüft jede Dateianfrage beim Admin und liefert freigegebene
Dateien aus dem privaten Bucket.

Das Jenkins-Plugin registriert Submissions bei Admin unter
`/internal/deliveries`. GRETL startet und beendet die Submission über
dieselbe interne API. Der Stack prüft die Bereitschaft des Jenkins-Diensts.
Der öffentliche Einstieg für CSV-Lieferungen ist `/anlieferung`.

Die [Integrationstests](../README.md) erzeugen eigene Compose-Projekte und
räumen deren Container, Netzwerke und Volumes per Compose auf. Der
Jenkins-Image-Build verwendet den Gradle-Resolver
für `ch.so.agi.gretl:gretl-dist:6.0.0-SNAPSHOT:bin@zip` aus
`https://jars.interlis.guru/snapshots`. Das Image enthält das lokale
Jenkins-Plugin und den festen Job, den Jenkins mit der GRETL-CLI ausführt.

## CSV-Anlieferung mit GRETL 6

Der lokale Lieferweg über `/anlieferung` nutzt Gateway, Jenkins,
Keycloak, Admin, PostgreSQL, Garage, Origin und ClickHouse.
Sodata zeigt die publizierte Version. Verwende eine isolierte lokale
Instanz mit separaten Ports.
Der Integrationstest `scripts/test_delivery_domain.py` zeigt, wie
`ComposeContext` diese Instanz einrichtet und die vier Modelle per
`management-setup` initialisiert. Er importiert das synthetische
`tests/fixtures/management-bootstrap.xtf` aus dem Admin-Repo mit
`python3 scripts/compose_operator.py import /pfad/zur/fixture.xtf --env /pfad/runtime.env`.
Der Test führt den Ablauf bis zur Annahme mit eigenen Testzugängen aus.

Für eine Lieferung müssen die Person und der technische Principal mit den
`iss`- und `sub`-Werten der Keycloak-Instanz in Admin registriert sein.
Die Clients `jenkins-delivery` und `gretl-delivery` verwenden die Audience
`management-api`. Die technische Identität erhält ihren Token per
Client Credentials. Das ClickHouse-Setup berechtigt `ch_delivery` für
`default.snapshot_*`.

Öffne `/anlieferung` am Gateway und lade nach der Keycloak-Anmeldung eine
CSV für eine berechtigte Ausgabe hoch. Jenkins startet den festen Job.
Admin erzeugt das INTERLIS-Modell aus der gebundenen Schemafassung. GRETL
bezieht mit `OAuth2ClientCredentials` einen technischen Token und lädt
das Modell per `Curl`. Bei Append lädt GRETL zusätzlich die letzte CSV aus
Garage. Für `reject` und `complete` bezieht GRETL jeweils einen frischen
Token. Admin akzeptiert nur
einen Stand mit weiterhin gültigen Fachrechten, Schema und Basisversion.
Die angenommene CSV ist unter `/downloads/<distribution-id>/snapshot.csv`
verfügbar. Die ClickHouse-Tabelle heisst
`default.snapshot_<submission-uuid-ohne-bindestriche>`. Die Submission-ID
steht als `versionKey` an der fachlichen Version.

Für die Jenkins-Lieferprüfung das lokale Jenkins-Image bauen und angeben:

```sh
python3 scripts/test_delivery_domain.py --jenkins-image dateninfrastruktur-jenkins:mein-kandidat
```

Der Test verwendet eine eigene Compose-Instanz und prüft Replace, Append,
CSV mit ausschliesslich Kopfzeile, Validierungsablehnung, typisierte
ClickHouse-Werte, Prozessabbruch und ClickHouse-Ausfall. Jenkins speichert
den originalen Validierungsbericht bis 64 MiB unverändert und privat beim
zugehörigen Build. Der ursprüngliche Einreicher kann ihn nach der
Admin-Statusprüfung von der Statusseite herunterladen. Der Bericht kann
konkrete CSV-Werte enthalten. Jenkins wertet die einzelnen Meldungen nicht
aus. Mit dem Build wird auch der Bericht gelöscht.

Jenkins entfernt die privaten Laufzeitdateien nach dem Lauf. Bei einer
Cleanup-Warnung entfernt der Betreiber nach Ende des Laufs das Verzeichnis
unter `$JENKINS_HOME/data-infrastructure/uploads`, das zur Lieferkennung im
Joblog gehört. Es kann noch CSV-Daten, das Validierungslog und
Laufzeit-Credentials enthalten und soll zeitnah entfernt werden.

Wird eine Queue-Position vor dem Start administrativ abgebrochen, entfernt
Jenkins die private Upload-Datei. Die Submission kann in Admin `pending`
bleiben. Ein erneuter Upload erzeugt eine eigene Submission.

Für die manuelle Bereinigung koordiniert der Betreiber mit der einreichenden
Person eine autorisierte Betriebssitzung. Die interne Admin-API ist am
Gateway gesperrt. Aus dem Stack-Checkout erreicht der folgende Befehl
die API über den Jenkins-Container des gebundenen Compose-Kontexts. Setze
`runtime_env` auf dessen `runtime.env` und `submission_id` auf die
Lieferkennung der abgebrochenen Queue-Position. Die einreichende Person
gibt ihr gültiges Benutzer-JWT für die Audience `management-api` direkt
in die verdeckte Abfrage ein. Admin prüft ihre Identität und `pending`.

```sh
python3 - "$runtime_env" "$submission_id" <<'PYTHON'
from getpass import getpass
import json
import re
import sys
from uuid import UUID

sys.path.insert(0, "scripts")
from compose_runtime import ComposeContext

context = ComposeContext(sys.argv[1])
submission = UUID(sys.argv[2])
jwt = getpass("Benutzer-JWT der einreichenden Person: ")
if not re.fullmatch(r"[A-Za-z0-9_-]+(?:\.[A-Za-z0-9_-]+){2}", jwt):
    raise SystemExit("Ungültiges JWT-Format.")
result = context.command(
    ["exec", "-T", "jenkins", "curl", "-fsS", "--config", "-", "--request", "POST",
     f"http://admin:8080/internal/deliveries/{submission}/cancel"],
    input=f'header = "Authorization: Bearer {jwt}"\n',
)
print(json.loads(result.stdout)["status"])
PYTHON
```

Bei Erfolg meldet Admin `cancelled`.

Bei Prozessabbruch, Timeout oder technischem Fehler meldet Jenkins den Fehler an
Admin. Bleibt die Submission bei einem Ausfall in `processing`, kann der
registrierte Service-Principal sie über `POST /internal/deliveries/{id}/fail`
mit einer technischen Begründung abschliessen, sobald feststeht, dass der Lauf
beendet ist. Admin führt diesen Übergang nur aus `processing` aus.

Bei einem Import-, Upload- oder Abschlussfehler kann eine ClickHouse-Tabelle
zurückbleiben. Vor einer administrativen Löschung den endgültigen Admin-Status
und die Zuordnung über Submission-ID und `versionKey` prüfen. Nur die eindeutig
zugehörige Tabelle eines beendeten, nachweislich nicht angenommenen Laufs
entfernen.
