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

Benötigt werden Docker mit Compose/Buildx, Python 3, Java 21 und Maven. Der
Jenkinsbuild verwendet das lokal vorhandene, in
[MA-G0 gebundene Toolchain-Image](implementation/storage-and-delivery/contracts/g0-toolchain.json).
Ohne dessen exakten Image- und JAR-Nachweis bricht der Build ab. Aus
`dateninfrastruktur-dev-stack`:

```sh
./scripts/init.sh
IMAGE_NAME=dateninfrastruktur-jenkins:local ./scripts/build-jenkins-local.sh "$PWD/.runtime/jenkins-build-first"
python3 scripts/bind_jenkins_image.py dateninfrastruktur-jenkins:local
./scripts/setup.sh
./scripts/up.sh --skip-build
python3 scripts/provision_ingestion_oidc.py --register-pg
./scripts/status.sh
```

Das Setup legt nur technische Rollen, SQL-Sichten, den Bucket mit separatem
Reader/Writer und leere Anwendungsschemas an. Es erstellt keine Personen,
Datensätze, Grants oder Demodateien. Für bestehende Daten mit abweichendem
Schema stoppt es. [Lokaler Cutover](implementation/storage-and-delivery/LOCAL_CUTOVER.md)
dokumentiert die gesonderte, einmalige Übernahme. Die Bedienbefehle
`up.sh --skip-build`, `stop.sh`, `restart.sh`, `down.sh`, `status.sh` und
`logs.sh` verwenden denselben gebundenen Kontext. `down.sh` erhält Volumes.
Für einen bewusst separaten Kontext dienen `--project` und `--env`;
keine Dateien zwischen Instanzen kopieren.

## Einen Datensatz für CSV-Anlieferung öffnen

1. Die berechtigte Person in Keycloak eindeutig anhand Issuer und Subject
   zuordnen. Mit dem Betreiberkommando
   `python3 scripts/compose_operator.py bootstrap-submitters <private-anfrage.json>`
   die erste Verwaltung von Lieferrechten auf den vorgesehenen Datensatz
   oder das vorgesehene Amt beschränken. Die Datei gehört in den ausgewählten
   Runtimeordner und muss Modus 0600 haben. Das genaue Format steht in
   [MA-G2 Backend](implementation/storage-and-delivery/MA-G2_BACKEND.md).
2. Im Admin einen publizierten Datensatz und seine Ausgabe wählen. Unter
   `/management/delivery` einen genehmigten CSV-Vertrag aus dem Themenrepo
   auswählen, zulässige Liefermodi festlegen und automatische Veröffentlichung
   bewusst bestätigen. Ein neuer Vertrag benötigt ein fest gepinntes
   INTERLIS-Modell, die validierte Definition samt Schema/Hashes, einen
   Runnerbuild sowie Testdaten. Die Vorgaben stehen in
   [CSV-Verarbeitung](implementation/storage-and-delivery/MA-G4_PROCESSING.md).
3. Auf derselben Verwaltungsseite der geprüften Identität ein Lieferrecht
   erteilen. Der Dateizugang für geschützte Daten wird separat unter
   `/management/datasets/<uuid>/grants` vergeben und entzogen.

## Liefern, prüfen, erneut versuchen

Über das Gateway `/anlieferung` öffnen und sich mit Keycloak anmelden.
Datensatz, Ausgabe und erlaubten Modus wählen, Kommentar eingeben und CSV
hochladen. Die Anlieferungsseite zeigt Status, Laufhistorie und eine bereinigte
Prüfmeldung. Erneut versuchen steht nur bei einem behebbaren Fehler und
wirksamem Lieferrecht zur Verfügung. Eine ungültige Datei korrigieren und neu
einreichen. Der technische Jenkinsjob wird über die Anlieferung ausgelöst.

Nach erfolgreichem Abschluss zeigt Sodata den neuen Stand unter `/datasets`.
Historische Downloads bleiben auf ihren eigenen URLs; APISIX prüft jede
Dateianfrage über Admin. Zwischen Fachcommit und sichtbarer SQL-Projektion
kann der Status kurz «Angenommen» anzeigen. Bei Störungen
`./scripts/status.sh` und `./scripts/logs.sh --tail 100 <dienst>` prüfen.
Bei anhaltender Störung des Projektors zuerst dessen ClickHouse-Berechtigung
und Verfügbarkeit prüfen; die Wiederholung geschieht auf dem gebundenen
Ziel. Keine Dateien/Versuche manuell in einen neuen Stand umschreiben.

Die Bedienwege und Abnahmen stehen im
[MA-G-Arbeitsstand](implementation/storage-and-delivery/WORK_QUEUE.md).
