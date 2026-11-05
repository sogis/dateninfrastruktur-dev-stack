# Dateninfrastruktur: gemeinsamer lokaler Stack

Ein Docker-Compose-Verbund mit zehn Diensten, einem PostgreSQL16/PostGIS-Server
für Keycloak/Superset/Management und genau einer Instanz je Anwendung. JVM mit
Java25/Boot/Cayenne bleibt Standard. Kein HA und kein separater Managementlauncher.

**Betrieb:** [operations.md](docs/operations.md). **Bestandsübernahme und Rückfall:**
[migration-ma-f.md](docs/migration-ma-f.md). **Aktueller Auftrag/Phasenstand:**
[WORK_QUEUE.md](docs/implementation/compose-consolidation/WORK_QUEUE.md).
Historische Grundinstallations-/MA-A–E-Berichte bleiben unverändert erhalten.

Nach ausdrücklichem Setup oder überprüfter Migration:

```sh
./scripts/up.sh --skip-build
./scripts/status.sh
./scripts/smoke-test.sh
./scripts/stop.sh
./scripts/down.sh  # keine Volumes löschen
```

Portal, Administration und Jenkins: http://localhost:18081/; Anlieferung
`/anlieferung`, Jenkins `/jenkins/`. Keycloak: http://localhost:18080/;
Superset: http://localhost:18088/. Alle URLs sind im aktiven privaten Kontext
konfiguriert. Alte öffentliche S3-/Manifestpfade sind gesperrt; ihre Daten bleiben
aufbewahrt. Normalstart enthält keine Demo-Grants, Seedpublikation oder Reloads.

Eine bestehende Installation wird kontrolliert migriert und niemals durch leere
Daten ersetzt. Die tatsächliche lokale Umschaltung ist gesondert im Phasenstand
angegeben; eine isolierte Codeabnahme allein behauptet keine Nutzerumstellung.
