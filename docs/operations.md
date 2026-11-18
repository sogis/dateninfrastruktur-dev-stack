# Lokaler Betrieb der Dateninfrastruktur

Admin, Sodata, Jenkins-Image und Jenkins-Plugin liegen in
Schwestercheckouts. Der Compose-Stack führt PostgreSQL 16/PostGIS, Garage, ClickHouse, Keycloak,
Superset, Admin, Sodata, Origin, APISIX und Jenkins je einmal aus. Die
PostgreSQL-Datenbanken und der private Bucket `ch.so.daten` werden durch
explizites Setup eingerichtet. Normalstart und Recreate verwenden die
bestehenden Volumes. Die Konfiguration jeder Instanz und ihre Secrets liegen privat unter
`.runtime/`. Ports für Gateway, Keycloak, Superset und ClickHouse sind nur
an Loopback gebunden. Admin, PostgreSQL, Jenkins, Sodata und Origin haben
keinen eigenen Hostport.

## Frische Installation und Normalstart

Benötigt werden Docker mit Compose und Buildx sowie Python ab 3.9.
Öffne im Stack-Checkout eine saubere Bash mit dem gewünschten Kontext aus
`docker context ls`. Verwende dieselbe Shell für alle Befehle der Instanz.

```bash
env -i HOME="$HOME" PATH="$PATH" DOCKER_CONTEXT=desktop-linux bash --noprofile --norc
```

Die leere Umgebung verhindert, dass exportierte Projekt-, Volume- oder
Image-Variablen die Datei überschreiben. Falls der benannte Kontext SSH oder
eine eigene Docker-Konfiguration braucht, übergib zusätzlich
`SSH_AUTH_SOCK="$SSH_AUTH_SOCK"` bzw. `DOCKER_CONFIG="/pfad/zur/docker-config"`
an `env`. Hinterlege den Docker-Endpunkt im benannten Kontext. Behalte
die Shell für diese Instanz frei von exportierten Stack-Variablen.

Wähle die private Datei der vorhandenen Instanz. Bei einer frischen
Instanz lege sie zuerst mit `init` an. Die Datei enthält auch Ports,
Volume-Namen, Image-Referenzen und Credentials.

```bash
python3 scripts/compose_runtime.py init dateninfrastruktur-dev-stack  # nur frisch
runtime_env=.runtime/dateninfrastruktur-dev-stack/runtime.env
```

### Images bereitstellen

Eine neue Instanz erhält projektspezifische lokale Tags für
`POSTGRES_IMAGE`, `ADMIN_IMAGE`, `SODATA_IMAGE`, `SUPERSET_IMAGE`,
`TOOL_IMAGE` und `JENKINS_IMAGE`. Die regulären Images baut Compose. Der separate
Jenkins-Build braucht den Jenkins- und Plugin-Checkout, Java 21 und Maven.
Admin und Sodata werden im Container mit Java 25 gebaut.

```bash
docker compose --file compose.yaml --env-file "$runtime_env" --profile build-tools build postgres admin sodata superset management-tool-build
docker compose --file compose.yaml --env-file "$runtime_env" pull --policy missing garage clickhouse keycloak origin gateway
build_dir=$(mktemp -d "$(dirname "$runtime_env")/jenkins-build.XXXXXXXX")
JAVA21_HOME=/pfad/zu/java-21 \
  IMAGE_NAME=dateninfrastruktur-jenkins:dateninfrastruktur-dev-stack \
  ../dateninfrastruktur-jenkins-dev/bin/build-image.sh "$build_dir/context"
```

Der Wert von `IMAGE_NAME` muss dem ausgewählten `JENKINS_IMAGE` entsprechen.
Für einen Registry-Start trage die veröffentlichten, versionierten Referenzen
in dieselben sechs Zeilen der privaten Datei ein. Ein auf amd64 und arm64
verfügbarer Satz ist `ghcr.io/sogis/dateninfrastruktur-{admin,jenkins,postgres,superset,tools}:0.2.22`
mit `ghcr.io/sogis/dateninfrastruktur-sodata-jvm:0.1.8` für Sodata. Setze
jeden Wert separat ein. Das Jenkins-Image muss GRETL `6.0.0-SNAPSHOT` tragen.

```bash
docker compose --file compose.yaml --env-file "$runtime_env" --profile setup pull --policy missing
```

Bei wiederholten Starts bleibt die Image-Auswahl in der privaten Datei.

### Setup und Start

Das explizite Setup richtet PostgreSQL-Datenbanken, Management-Schema,
Rollen, den privaten Garage-Bucket mit Reader/Writer und ClickHouse ein.
Zum Abschluss legt das Setup die Jenkins- und Superset-Volumes mit den
Compose-Eigentumslabels des Projekts an und bindet sie. Dadurch kann es
schon vor dem Build dieser beiden Images abgeschlossen werden. Ein vorhandenes Management-Schema wird geprüft.
Fehlt eine bekannte Managementdatenbank, bricht das Setup ab. Demo-Daten
sind dem Testmodus vorbehalten.

```bash
python3 scripts/setup_instance.py --env "$runtime_env"
```

Führe den Startblock aus, sobald die Images bereitstehen. Nach der
Eigentums- und Volumeprüfung startet Compose PostgreSQL. Das vorhandene
Management-Werkzeug prüft die Datenbank und das Schema lesend, bevor
Compose den übrigen Stack startet. Jenkins erhält die geprüfte lokale
Image-ID.

```bash
jenkins_id=$(python3 scripts/compose_runtime.py check --start --env "$runtime_env") &&
  docker compose --file compose.yaml --env-file "$runtime_env" up -d --wait --wait-timeout 240 --no-build --pull never postgres &&
  docker compose --file compose.yaml --env-file "$runtime_env" --profile setup run --rm --no-deps --pull never management-setup verify &&
  JENKINS_IMAGE=$jenkins_id docker compose --file compose.yaml --env-file "$runtime_env" up -d --wait --wait-timeout 300 --no-build --pull never
```

Compose führt die Eigentumsprüfung bei einem direkten Aufruf nicht aus.
Verwende den vollständigen Startblock und vor Stop oder Down den
Eigentumscheck unten. Führe Änderungen an einer Instanz nacheinander aus.
Ändere zwischen Prüfung und Compose-Aufruf weder die private Datei noch
Docker-Kontext oder Projektressourcen.

```bash
docker compose --file compose.yaml --env-file "$runtime_env" ps
set -o pipefail
docker compose --file compose.yaml --env-file "$runtime_env" logs --tail 100 -f admin 2>&1 |
  python3 scripts/compose_runtime.py redact --env "$runtime_env"

python3 scripts/compose_runtime.py check --env "$runtime_env" &&
  docker compose --file compose.yaml --env-file "$runtime_env" stop --timeout 60

python3 scripts/compose_runtime.py check --env "$runtime_env" &&
  docker compose --file compose.yaml --env-file "$runtime_env" down --timeout 60
```

`down` erhält die Volumes. Verzichte für normale Betriebsabläufe auf
`--volumes`. Der Startblock übernimmt Konfigurationsänderungen mit
`up`. `restart` startet vorhandene Container mit ihrer bisherigen
Konfiguration. Führe den Startblock nach einem Stopp oder Down erneut aus.

Verwende für Prüfungen des Compose-Modells `config --quiet`. Eine vollständige
interpolierte Konfiguration enthält Zugangsdaten. Die Logpipeline filtert
konfigurierte Secrets aus `runtime.env`. Behandle verbleibende Logs
weiterhin als vertraulich.

### Bestehende Instanz

Verwende dieselbe `runtime.env` im ursprünglichen Checkout und führe den
Startblock aus. Erhalte die vorhandenen Image-Referenzen, Volumes,
`setup-complete.json` und die gerenderten privaten Dateien. Bei einem
fehlenden Volume, einer fehlenden Setup-Bindung oder einem unbekannten
Management-Schema halte an und kläre den Zustand anhand der Sicherung.

## Admin aus lokalen Quellen entwickeln

Im laufenden und eingerichteten Stack den Admin-Dienst umschalten:

```bash
python3 scripts/admin_development.py on --env "$runtime_env"
docker compose --file compose.yaml --env-file "$runtime_env" logs --tail 100 -f admin 2>&1 |
  python3 scripts/compose_runtime.py redact --env "$runtime_env"
python3 scripts/admin_development.py off --env "$runtime_env"
```

Schalte den Entwicklungsoverlay vor regulären Änderungen am Stack aus.
Admin bleibt über das Gateway unter
`http://localhost:<Gateway-Port>/management` erreichbar. Für eine
Farbänderung `src/main/resources/static/assets/management.css` im
Admin-Checkout bearbeiten, speichern und die Seite neu laden. Dasselbe
gilt für Templates unter `src/main/jte`. Java-Änderungen werden
automatisch kompiliert. Nach erfolgreicher Kompilierung startet Spring
den Anwendungskontext neu. Bei einem Kompilierfehler die Admin-Logs
prüfen und die korrigierte Datei erneut speichern.

Compose baut beim Wechsel das Werkzeugimage mit JDK und Python und verwendet
dabei den Build-Cache. Der erste Gradle-Start lädt die Distribution und die
Abhängigkeiten vor dem Bereitschaftscheck. Der Admin-Checkout wird
schreibgeschützt eingebunden. Gradle-Cache und Buildausgaben liegen unter
`.runtime/<instanz>/admin-dev/`. Änderungen am Gradle-Build werden nach erneutem `off` und `on` geladen.

Status und Logs sind im Entwicklungsmodus verfügbar. Bei einem Fehlstart
stellt das Werkzeug die vorherige Variante anhand ihrer tatsächlichen
Image-ID wieder her. Wenn auch das fehlschlägt,
bleibt der Zustand für einen erneuten Aufruf von `off` erhalten. Wurde das
gesamte Projekt bereits per Compose-Down entfernt, räumt `off` den Marker
der geprüften Instanz auf. Danach gilt der Startblock oben.

## Katalog und Lieferung

Das explizite Management-Setup legt das Schema aus den vier
INTERLIS-Modellen im Admin-Repo an. Das lokale Tooling-Image enthält
ili2pg 5.5.2 und ilivalidator 1.15.1. Beim Tooling-Build liefert der
Stack-Kontext die PostgreSQL- und Garage-Setup-Skripte.
Die erste fachliche Belegung kommt aus einem geprüften
[XTF-Transfer](../../dateninfrastruktur-admin/docs/schema-lifecycle.md).
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

Der Stack-Browsercheck nutzt ein eigenes Compose-Projekt. Die
Testbereinigung entfernt nach dem Compose-Down die geprüften
projektspezifischen Volumes und lokalen Image-Tags. Der Jenkins-Image-Build verwendet den Gradle-Resolver
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
