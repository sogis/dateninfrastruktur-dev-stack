# Lokaler Betrieb der Dateninfrastruktur

Der Stack verbindet Admin, Sodata und Jenkins aus Schwestercheckouts mit
PostgreSQL/PostGIS, Garage, ClickHouse, Keycloak, Superset und APISIX.
Instanzdateien und Secrets liegen privat unter `.runtime/`.
Hostports sind an die Loopback-Adresse gebunden.

## Lokale Instanz anlegen

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
bei späteren Sitzungen dieselbe `runtime.env`. Führe Setup und
Admin-Umschaltungen einzeln aus.

Seit B2.3 leitet Compose die Volume-Namen vom Projektnamen ab. PostgreSQL
verwendet beispielsweise `<projekt>_postgres-data` statt des bisherigen
`<projekt>_postgres`. Öffne frühere Projekte mit ihrem bisherigen Checkout und
ihrer bisherigen `runtime.env`. Lege für B2.3 ein frisches Projekt an.
Setup und Startprüfung weisen Konfigurationen mit den alten Volume-Variablen
ab. Bestehende Volumes bleiben erhalten. Eine Datenübernahme erfordert einen
eigenen Auftrag.

### Images bereitstellen

Für lokale Builds müssen Admin und Sodata neben dem Stack ausgecheckt sein.
Der separate Jenkins-Build benötigt zusätzlich die Jenkins- und
Plugin-Checkouts, Java 21 und Maven. Admin und Sodata werden im Container
mit Java 25 gebaut.

```bash
docker compose -f compose.yaml --env-file "$runtime_env" --profile build-tools build postgres admin sodata superset management-tool-build
docker compose -f compose.yaml --env-file "$runtime_env" pull --policy missing garage clickhouse keycloak origin gateway
build_dir=$(mktemp -d "$runtime_dir/jenkins-build.XXXXXXXX")
JAVA21_HOME=/pfad/zu/java-21 IMAGE_NAME="dateninfrastruktur-jenkins:$project" \
  ../dateninfrastruktur-jenkins-dev/bin/build-image.sh "$build_dir/context"
```

Für Registry-Images setze `ADMIN_IMAGE`, `JENKINS_IMAGE`, `POSTGRES_IMAGE`,
`SUPERSET_IMAGE` und `TOOL_IMAGE` auf die jeweilige Referenz
`ghcr.io/sogis/dateninfrastruktur-<name>:0.2.22`.
Setze `SODATA_IMAGE=ghcr.io/sogis/dateninfrastruktur-sodata-jvm:0.1.8`.
Das Jenkins-Image muss GRETL `6.0.0-SNAPSHOT` tragen.

```bash
docker compose -f compose.yaml --env-file "$runtime_env" --profile setup pull --policy missing
```

### Setup und Start

```bash
python3 scripts/setup_instance.py --env "$runtime_env"
jenkins_id=$(python3 scripts/compose_runtime.py preflight --env "$runtime_env") &&
  JENKINS_IMAGE="$jenkins_id" docker compose -f compose.yaml --env-file "$runtime_env" up -d --wait --wait-timeout 300 --no-build --pull never
```

Setup richtet PostgreSQL, Garage und ClickHouse ein. Mit derselben privaten
Konfiguration kann es zur Prüfung und Initialisierung erneut ausgeführt werden.
Die Startprüfung startet bei Bedarf PostgreSQL, liest den Schemazustand und
bindet Jenkins an die geprüfte Image-ID. Bei einem inkompatiblen Schema bleibt
der Zustand der laufenden Anwendungen erhalten.

### Status, Logs und Stopp

```bash
docker compose -f compose.yaml --env-file "$runtime_env" ps
set -o pipefail
docker compose -f compose.yaml --env-file "$runtime_env" logs --tail 100 -f admin 2>&1 |
  python3 scripts/compose_runtime.py redact --env "$runtime_env"
docker compose -f compose.yaml --env-file "$runtime_env" down --timeout 60
```

Mit `stop` bleiben auch die Container erhalten. `down` behält die
Compose-Volumes für den nächsten Start. Behandle auch redigierte Logs
vertraulich. Prüfe das Compose-Modell mit `config --quiet`.

### Instanz bewusst zurücksetzen

Der folgende Befehl löscht die Daten in allen Compose-Volumes der ausgewählten
B2.3-Instanz. Vergewissere dich vorher, dass die private Datei zur gewünschten
Instanz gehört. Beginne danach mit einem neuen `init`, neuen Zugangsdaten und
explizitem Setup. Die bisherige private Konfiguration enthält weiterhin ihre
Garage-Bindung.

```bash
docker compose -f compose.yaml --env-file "$runtime_env" --profile '*' down --volumes --remove-orphans
```

## Admin aus lokalen Quellen entwickeln

Schalte Admin im laufenden Stack um und vor regulären Stack-Änderungen
wieder zurück.

```bash
python3 scripts/admin_development.py on --env "$runtime_env"
python3 scripts/admin_development.py off --env "$runtime_env"
```

Admin bleibt am Gateway unter `/management` erreichbar. CSS und JTE
werden beim Neuladen sichtbar. Erfolgreich kompilierte Java-Änderungen
starten den Spring-Kontext neu. Cache und Buildausgaben liegen unter
`.runtime/<instanz>/admin-dev/`, die Quellen sind schreibgeschützt.
Änderungen am Gradle-Build werden nach `off` und `on` geladen.

Bei einem Fehlstart versucht das Werkzeug, die vorherige Image-ID
wiederherzustellen. Bei fehlgeschlagenem Rollback kann `off` erneut
aufgerufen werden. Nach einem vollständigen Compose-Down räumt `off`
den Development-Zustand auf.

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
