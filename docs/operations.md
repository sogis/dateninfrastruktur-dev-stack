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
python3 scripts/provision_ingestion_oidc.py --register-pg
./scripts/status.sh
```

`./scripts/up.sh` baut die eigenen Images aus den Schwestercheckouts und
verwendet beim Standardprojekt `:local`. Benannte Instanzen und Tests
verwenden den Projektnamen als Tag. Für diesen Build werden zusätzlich
Java 21 und Maven für das Jenkins-HPI benötigt. Admin und Sodata bauen mit
Java 25 im Container. Jenkins bezieht das aktuelle GRETL-5-Snapshot und
nimmt das geprüfte Offline-Bundle ins Image auf. `./scripts/build.sh` baut
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

## Einen Datensatz für CSV-Anlieferung öffnen

1. Die berechtigte Person in Keycloak eindeutig anhand Issuer und Subject
   zuordnen. Mit dem Betreiberkommando
   `python3 scripts/compose_operator.py bootstrap-submitters <private-anfrage.json>`
   die erste Verwaltung von Lieferrechten auf den vorgesehenen Datensatz
   oder das vorgesehene Amt beschränken. Die Datei gehört in den ausgewählten Runtimeordner und muss Modus 0600
   haben. Die [Verwaltung der Lieferrechte](../../dateninfrastruktur-admin/docs/delivery-authorization.md)
   beschreibt Format und Vorbedingungen.
2. Im Admin einen publizierten Datensatz und seine Ausgabe wählen. Unter
   `/management/delivery` einen genehmigten CSV-Vertrag aus dem Themenrepo
   auswählen, zulässige Liefermodi festlegen und automatische Veröffentlichung
   bewusst bestätigen. Ein neuer Vertrag benötigt ein fest gepinntes
   INTERLIS-Modell, die validierte Definition samt Schema/Hashes, einen
   Runnerbuild sowie Testdaten. Die Vorgaben stehen in
   [Themenrepo](../../dateninfrastruktur-themenrepo/README.md).
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
