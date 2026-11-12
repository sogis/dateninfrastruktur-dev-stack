# Dateninfrastruktur – lokaler Stack

Der Stack verbindet PostgreSQL/PostGIS, Garage, ClickHouse, Keycloak, Superset,
Admin, Sodata, Origin, APISIX und Jenkins in einem Compose-Projekt. Der private
Bucket `ch.so.daten` dient den gebundenen CSV-Lieferungen und Downloads. Der
Managementkatalog und die Fachrechte liegen in PostgreSQL.

[Lokaler Betrieb](docs/operations.md) beschreibt Erstaufbau, Normalstart,
Anlieferung, Betrieb und Testgrenzen. Für integrierte Prüfungen die
Schwesterrepositories im selben Workspace bereitstellen. Für CSS, JTE
und Java im laufenden Stack siehe [Admin aus lokalen Quellen entwickeln](docs/operations.md#admin-aus-lokalen-quellen-entwickeln).

- `python3 scripts/test_submission_backend.py` prüft Lieferrechte, Ausführung
  und die HTTP-Sicherheitsgrenze in einem eigenen PostgreSQL-Kontext.
- `python3 scripts/test_single_bucket_storage.py` prüft Reader-/Writer-Grenzen
  und wiederholbares Storage-Setup im isolierten Garage-Kontext.
- `python3 scripts/test_csv_delivery.py` prüft den Lieferweg mit dem
  gebundenen lokalen GRETL-Bundle.
- `python3 scripts/test_public_catalog.py` baut eine isolierte Rancher-Desktop-Instanz
  auf und prüft die öffentlichen ili2pg-Sichten, die Leserolle `di_public`,
  Sodata und geschützte Downloads über APISIX und den privaten Garage-Bucket.
