# Dateninfrastruktur – lokaler Stack

Ein Docker-Compose-Projekt für PostgreSQL/PostGIS, den privaten Garage-Bucket,
ClickHouse, Superset, Keycloak, Jenkins mit CSV-Anlieferung, Admin, Sodata
und das Gateway. Der Stack verwendet die sechs bestehenden
Dateninfrastruktur-Repositories als Geschwister.

[Installation und Betrieb](docs/operations.md) beschreibt explizites Setup,
Normalstart, Lieferrechte und CSV-Anlieferung. Der
[MA-G-Arbeitsstand](docs/implementation/storage-and-delivery/WORK_QUEUE.md)
trennt unabhängige Codeabnahme und lokale Umstellung. Die separate
ClickHouse-Ladeimplementierung bleibt in ihrem bestehenden Projektpfad.

Frühere Grundinstallations-, Lade- und Konsolidierungsberichte sind unter
`docs/implementation/` abgelegt.
