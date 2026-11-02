# Nachtrag zu P3 – Korrekturen nach Review c001

## Ausgangslage

Der unabhängige Qwen-Review zu `c001` endete wegen fehlender Kontextmetadaten
und wiederholter API-Abbrüche zunächst mit `BLOCKED` (Bericht
`review/c001/r004/REVIEW.md`). Der vom Nutzer autorisierte
Kimi-K2.6-Ausweichreview `review/c001/r005/REVIEW.md` fand danach zwei echte
Produktbefunde:

1. **G04/G18 – fehlender Gradle-Wrapper-JAR in Sodata.** Der JAR war im
   Quellcommit getrackt, wurde beim Ziel-Import aber wegen der späten
   `*.jar`-Regel in `.gitignore` nicht in den Zielcommit aufgenommen. Ein
   sauberer Checkout konnte deshalb den Sodata-Container nicht bauen.
2. **B2 – hartcodierter ClickHouse-Port im Negativtest.**
   `scripts/test-clickhouse.sh` verwendete `18123` statt
   `CLICKHOUSE_HTTP_PORT`; bei abweichenden Review-Ports schlug der Test
   fälschlich fehl.

## Korrekturen in c002

| Repo | Änderung | Zweck |
|---|---|---|
| `dateninfrastruktur-sodata` | `gradle/wrapper/gradle-wrapper.jar` aufgenommen; `.gitignore`-Reihenfolge korrigiert | Sauberer Checkout und reproduzierbarer Sodata-Build |
| `dateninfrastruktur-dev-stack` | `scripts/test-clickhouse.sh` nutzt `CLICKHOUSE_HTTP_PORT` | Review- und Instanzports funktionieren |
| `dateninfrastruktur-dev-stack` | dieser Nachtrag, Statusaktualisierung | Nachvollziehbare Korrektur und neuer Kandidat |

## Verifikation der Korrektur

- Frischer lokaler Clone von `dateninfrastruktur-sodata` am Commit
  `81ec219028c59ab51af7ac198b8032cda461b561` enthält
  `gradle/wrapper/gradle-wrapper.jar`.
- `docker build --target jvm-runtime` aus diesem Clone war erfolgreich
  (Exitcode 0, Image `dateninfrastruktur-sodata:c002-test`).
- Der neue Kandidat `c002` ersetzt `c001`; das c001-Manifest und die
  c001-Reviewberichte bleiben unverändert.

## Status

Die Korrekturen sind lokal geprüft. Die erneute unabhängige Prüfung von `c002`
ist zum Zeitpunkt dieses Nachtrags **ausstehend** und wird nicht behauptet.
