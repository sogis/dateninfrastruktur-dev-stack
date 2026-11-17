# Lokaler Betrieb der Dateninfrastruktur

Admin, Sodata, Jenkins-Image und Jenkins-Plugin liegen in
Schwestercheckouts. Der Compose-Stack führt PostgreSQL 16/PostGIS, Garage, ClickHouse, Keycloak,
Superset, Admin, Sodata, Origin, APISIX und Jenkins je einmal aus. Die
PostgreSQL-Datenbanken und der private Bucket `ch.so.daten` werden durch
explizites Setup eingerichtet. Normalstart und Recreate verwenden die
bestehenden Volumes. Der aktive Kontext und alle Secrets liegen privat unter
`.runtime/`. Ports für Gateway, Keycloak, Superset und ClickHouse sind nur
an Loopback gebunden. Admin, PostgreSQL, Jenkins, Sodata und Origin haben
keinen eigenen Hostport.

## Frische Installation und Normalstart

Für den Betrieb werden Docker mit Compose/Buildx und Python 3.9 oder neuer
benötigt. Für den GRETL-6-Lieferweg die eigenen Images aus den
Schwestercheckouts bauen. Die Befehle und Integrationstests verwenden
den aktiven Docker-Kontext. Mit `DOCKER_CONTEXT=<name>` lässt sich der
Kontext für einen einzelnen Aufruf wählen.

```sh
./scripts/init.sh
./scripts/setup.sh
./scripts/up.sh
./scripts/status.sh
```

`./scripts/up.sh` baut die eigenen Images aus den Schwestercheckouts und
verwendet beim Standardprojekt `:local`. Benannte Instanzen und Tests
verwenden den Projektnamen als Tag. Für diesen Build werden zusätzlich
Java 21 und Maven für das Jenkins-HPI benötigt. Admin und Sodata bauen mit
Java 25 im Container. Beim Jenkins-Image-Build löst Gradle die veröffentlichte
GRETL-6-Distribution aus Maven auf. `./scripts/build.sh` baut dieselben lokalen
Images. Der Start löst das ausgewählte Jenkins-Tag in eine lokale Image-ID
auf und übergibt diese an Compose. `restart.sh` verwendet den zuletzt
erfolgreich gestarteten Modus.

Das Setup legt nur technische Rollen, SQL-Sichten, den Bucket mit separatem
Reader/Writer und leere Anwendungsschemas an. Es erstellt keine Personen,
Datensätze, Grants oder Demodateien. Für bestehende Daten mit abweichendem
Schema stoppt es. Die Bedienbefehle
`up.sh --skip-build`, `stop.sh`, `restart.sh`, `down.sh`, `status.sh` und
`logs.sh` verwenden denselben gebundenen Kontext. `down.sh` erhält Volumes.
Für einen bewusst separaten Kontext dienen `--project` und `--env`;
keine Dateien zwischen Instanzen kopieren.

## Admin aus lokalen Quellen entwickeln

Im laufenden und eingerichteten Stack den Admin-Dienst umschalten:

```sh
./scripts/dev.sh admin on
./scripts/logs.sh --follow admin
./scripts/dev.sh admin off
```

Bei einer benannten Instanz jedem Befehl `--project <name>` oder
`--env <runtime.env>` mitgeben. Admin bleibt über das Gateway unter
`http://localhost:<Gateway-Port>/management` erreichbar. Für eine
Farbänderung `src/main/resources/static/assets/management.css` im
Admin-Checkout bearbeiten, speichern und die Seite neu laden. Dasselbe
gilt für Templates unter `src/main/jte`. Java-Änderungen werden
automatisch kompiliert. Nach erfolgreicher Kompilierung startet Spring
den Anwendungskontext neu. Bei einem Kompilierfehler die Admin-Logs
prüfen und die korrigierte Datei erneut speichern.

Der erste Wechsel baut ein Werkzeugimage mit JDK und Python. Gradle lädt
beim ersten Start seine Abhängigkeiten. Der Admin-Checkout wird schreibgeschützt eingebunden. Gradle-Cache und Buildausgaben liegen unter
`.runtime/<instanz>/admin-dev/`. Änderungen am Gradle-Build werden nach erneutem `off` und `on` geladen.

`status.sh`, `logs.sh`, `stop.sh` und `down.sh` funktionieren auch
im Entwicklungsmodus. Vor `up.sh`, `restart.sh` oder `setup.sh` mit
`dev.sh admin off` zum bisherigen Admin-Image zurückkehren. Nach
`stop.sh` stellt `off` den normalen Admin-Container im gestoppten
Zustand bereit. `down.sh` beendet den Entwicklungsmodus. Beim normalen
Wechsel prüft der Stack die Bereitschaft von Admin und stellt bei einem
Fehlstart die vorherige Variante wieder her.

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
