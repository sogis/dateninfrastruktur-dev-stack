# Dateninfrastruktur – lokaler Stack

Der Stack verbindet PostgreSQL/PostGIS, Garage, ClickHouse, Keycloak, Superset,
Admin, Sodata, Origin, APISIX und Jenkins in einem Compose-Projekt. Der private
Bucket `ch.so.daten` dient den gebundenen CSV-Lieferungen und Downloads. Der
Managementkatalog und die Fachrechte liegen in PostgreSQL.

[Lokaler Betrieb](docs/operations.md) beschreibt Erstaufbau, Normalstart,
Anlieferung, Betrieb und Testgrenzen. Für integrierte Prüfungen die
Schwesterrepositories im selben Workspace bereitstellen. Für CSS, JTE
und Java im laufenden Stack siehe [Admin aus lokalen Quellen entwickeln](docs/operations.md#admin-aus-lokalen-quellen-entwickeln).

- `python3 scripts/test_delivery_domain.py` prüft Lieferrechte, Submission
  und konkurrierende Abschlüsse auf PostgreSQL.
- `python3 scripts/test_single_bucket_storage.py` prüft Reader-/Writer-Grenzen
  und wiederholbares Storage-Setup im isolierten Garage-Kontext.
- `python3 scripts/test_public_catalog.py` prüft ili2pg-Sichten, die
  Leserolle `di_public`, Sodata und geschützte Downloads über APISIX.
- `python3 scripts/test_stack_management.py` prüft die zehn Compose-Dienste,
  die Admin- und Sodata-Formulare in Chromium sowie den XTF-Export.
  Lokal mit `DOCKER_CONTEXT=rancher-desktop`, Java 25, Java 21 und
  dem im Jenkins-Toolchain-Lock gebundenen lokalen Image ausführen.
