# Lokaler Betrieb der Dateninfrastruktur

Die sechs Schwesterrepositories liegen im selben Arbeitsverzeichnis. Der
Compose-Stack führt PostgreSQL 16/PostGIS, Garage, ClickHouse, Keycloak,
Superset, Admin, Sodata, Origin, APISIX und Jenkins je einmal aus. Die
PostgreSQL-Datenbanken und der private Bucket `ch.so.daten` werden durch
explizites Setup eingerichtet. Normalstart und Recreate verwenden die
bestehenden Volumes. Der aktive Kontext und alle Secrets liegen privat unter
`.runtime/`. Ports für Gateway, Keycloak, Superset und ClickHouse sind nur
an Loopback gebunden. Admin, PostgreSQL, Jenkins, Sodata und Origin haben
keinen eigenen Hostport.

## Frische Installation und Normalstart

Für den Betrieb werden Docker mit Compose/Buildx und Python 3.10 oder neuer
benötigt. Der erste Start aus der Registry verwendet die Versionstags aus
`compose.yaml`:

```sh
./scripts/init.sh
./scripts/setup.sh --skip-build
./scripts/up.sh --skip-build
./scripts/status.sh
```

`./scripts/up.sh` baut die eigenen Images aus den Schwestercheckouts und
verwendet beim Standardprojekt `:local`. Benannte Instanzen und Tests
verwenden den Projektnamen als Tag. Für diesen Build werden zusätzlich
Java 21 und Maven für das Jenkins-HPI benötigt. Admin und Sodata bauen mit
Java 25 im Container. Jenkins verwendet das lokal vorhandene, im Jenkins-Toolchain-Lock
gebundene GRETL-Image und nimmt das geprüfte Offline-Bundle ins Image auf. `./scripts/build.sh` baut
dieselben lokalen Images. `restart.sh` verwendet den zuletzt erfolgreich
gestarteten Modus.

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
beim ersten Start seine Abhängigkeiten. Die lokalen Quellen werden
schreibgeschützt eingebunden. Gradle-Cache und Buildausgaben liegen unter
`.runtime/<instanz>/admin-dev/`. Änderungen am Gradle-Build oder an
seinen Vertragsressourcen werden nach erneutem `off` und `on` geladen.

`status.sh`, `logs.sh`, `stop.sh` und `down.sh` funktionieren auch
im Entwicklungsmodus. Vor `up.sh`, `restart.sh` oder `setup.sh` mit
`dev.sh admin off` zum bisherigen Admin-Image zurückkehren. Nach
`stop.sh` stellt `off` den normalen Admin-Container im gestoppten
Zustand bereit. `down.sh` beendet den Entwicklungsmodus. Beim normalen
Wechsel prüft der Stack die Bereitschaft von Admin und stellt bei einem
Fehlstart die vorherige Variante wieder her.

## Katalog und Lieferung

Das explizite Management-Setup legt die vier INTERLIS-Modelle an.
Die erste fachliche Belegung kommt aus einem geprüften
[XTF-Transfer](../../dateninfrastruktur-admin/docs/schema-lifecycle.md).
Dort werden auch die ersten Principals und deren Rechte angelegt.

Unter `/management` werden Datensätze, Ausgaben und ihre Publikation
verwaltet. Unter `/management/delivery` werden CSV-Schema,
Lieferkonfiguration, Lieferrechte und Submissions verwaltet.
Sodata liest die veröffentlichten Katalogdaten direkt aus PostgreSQL.
APISIX prüft jede Dateianfrage beim Admin und liefert freigegebene
Dateien aus dem privaten Bucket.

Die GRETL-/Jenkins-Anlieferung benötigt die Portierung auf
`/internal/deliveries`. Der laufende Jenkins-Dienst wird auf
Bereitschaft geprüft. Die alten öffentlichen Uploadpfade sind gesperrt.

Der Stack-Browsercheck nutzt ein eigenes Compose-Projekt.
Für eine Veröffentlichung muss auf jedem Plattform-Runner das Image
mit der im Jenkins-Checkout gebundenen Toolchain-ID und der
passenden Architektur bereits vorliegen. Der Build veröffentlicht
erst nach erfolgreicher Qualifikation der Plattformimages.
