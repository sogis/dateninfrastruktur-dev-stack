# Dateninfrastruktur – lokaler Stack

Der Stack verbindet PostgreSQL/PostGIS, Garage, ClickHouse, Keycloak, Superset,
Admin, Sodata, Origin, APISIX und Jenkins in einem Compose-Projekt. Der private
Bucket `ch.so.daten` dient den gebundenen CSV-Lieferungen und Downloads. Der
Managementkatalog und die Fachrechte liegen in PostgreSQL.

Docker Compose übernimmt Build, Pull, Start, Status, Stopp und Down.
[Lokaler Betrieb](docs/operations.md) zeigt, wie eine private `runtime.env`
erzeugt, eine frische Instanz eingerichtet und ein bestehender Stack
nach der Management-Schemaprüfung gestartet wird. Für integrierte Prüfungen die
jeweils benötigten Schwesterrepositories im selben Workspace bereitstellen.
Der [Einstieg in die Admin-Webentwicklung](docs/operations.md#admin-webentwicklung-vom-checkout-zur-ersten-änderung)
führt vom Checkout über die lokale Anmeldung zur ersten Änderung im Browser.
Auf macOS läuft Admin mit Java 25 auf dem Host, die Infrastruktur verwendet
veröffentlichte Images. Für Änderungen am GRETL-Job gibt es ein
[Compose-Overlay](docs/operations.md#gretl-job-entwickeln).

- `python3 scripts/test_host_development.py` prüft Host- und GRETL-Overlays mit Docker Compose.
- `python3 scripts/test_management_bootstrap.py` prüft Schema, Rollen und XTF-Import/-Export.
- `python3 scripts/test_cayenne_mapping.py` prüft Mapping-Generierung und echte Cayenne-Schreibvorgänge.
- `python3 scripts/test_delivery_domain.py` prüft Lieferrechte, Modellabruf,
  Dateimetadaten, konkurrierende Abschlüsse und den direkten Garage-Lieferweg.
  Mit `--jenkins-image` qualifiziert der Test stattdessen die Lieferkette mit
  Jenkins, GRETL 6, Garage und ClickHouse.
- `python3 scripts/test_single_bucket_storage.py` prüft Reader-/Writer-Grenzen
  und wiederholbares Storage-Setup im isolierten Garage-Kontext.
- `python3 scripts/test_public_catalog.py` prüft ili2pg-Sichten, die
  Leserolle `di_public`, Sodata und geschützte Downloads über APISIX.
- `python3 scripts/test_stack_management.py` prüft die zehn Compose-Dienste,
  die Admin- und Sodata-Formulare in Chromium, die HTTP-Sicherheit des Admin
  mit Keycloak und APISIX sowie den XTF-Export.
  Lokal mit Java 25 und Java 21 ausführen. Die Tests verwenden den
  aktiven Docker-Kontext oder ein explizit gesetztes `DOCKER_CONTEXT`.
  Der Test baut das Jenkins-Image aus den benachbarten Jenkins- und Plugin-Quellen.
