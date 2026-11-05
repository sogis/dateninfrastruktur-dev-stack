# Reviewrequest MA-G0 – Bestand, Grenzen, OIDC-/Validator-Risikoproben

- STACK base: `8ee609cff186f80472f54356ec5e493661670d93`
- ADMIN base: `6009fb04063f16fcdb2ea6b3d9153e9553c9e4f1`
- PUBLIC base: `b1f20075be43eb4d0edf771ee1440ea0e30e1801`
- PLUGIN base: `579f3fd54432a977122afb186469fbb40d95322f`
- JENKINS base: `08931fa8254d096e2addcd3aee97bc1b753f087d`
- TOPICS base: `6b0b635f066dc8de5000e3e549b983fb772dfb33`

## Änderung und Risiko

G0 ändert Arbeitsanweisungen, Bestands-/Zielzuordnung, zentralen Reviewrunner und
ausschliesslich isolierte Testspikes. Kein aktiver Storage-/Modell-/Job-/Webpfad
wurde umgestellt. Es gibt noch keinen neuen Ingestionproduktendpunkt. Keine
Nutzerdatei/kein Bucket/kein Grant wurde verändert. Alles G00–G04 frisch prüfen;
keine Übernahme alter Abnahmen.

| Änderung | Gefährdete Verträge | Frische Prüfung |
|---|---|---|
| MA-G-Routing/Phasentabelle/JSON-/Workspacehashes/alle sechs Repos | G01, falscher historischer Specpfad/Modell/SHA | Gate- und Routingtests, Handoff unabhängig prüfen |
| Test-only OIDC-Spike | G02 Token-API/Subject/Audience/PKCE | Echte Keycloak/Jenkinsbrowserprobe und ADMIN-Decoder |
| Test-only CsvValidator | G03 tatsächliche Validierung, fehlende Eingaben, Binärpins | Echter gültiger/ungültiger CSVlauf |
| BASELINE/MODEL_CHANGE/RETIREMENT_MATRIX/aktuelle AGENTS | G00/G04 Bestand/Lösch- und Datenerhaltungsgrenzen | Diffs/Code/Zuordnung, eigene Gegenprobe |

## Tatsächlich vorhandene Ausführung

Aus isoliertem STACK:

```sh
DI_GATE_TEST_PHASE=MA-G0 python3 scripts/management/test_review_gate.py
python3 scripts/management/test_review_g0.py
python3 scripts/test_ingestion_csv_g0.py
docker build -f tests/ingestion/Dockerfile.oidc-probe -t dateninfrastruktur-g0-oidc:probe tests/ingestion
python3 scripts/test_ingestion_oidc_g0.py
```

OIDC-Treiber startet ausschliesslich seine eigenen synthetischen
PG-/Keycloak-/Jenkinsressourcen, erzeugt eigene Zufallsports/Volumes/Credentials,
führt ADMIN `integrationTest --tests '*IngestionOidcSpikeIT'` mit Java25 aus und
entfernt anschliessend nur sein Projekt. Java25 aus vorhandenem SDKMAN;
Playwright-Chromium ist vorhanden. Kein Passwordgrant. Access-Token wird nur
im Speicher Jenkins→test-only ADMIN-Decoderreceiver übertragen; 200 positiv,
401 falsche Audience, 403 Subjectabweichung. Testreceiver ist kein Produktdienst.

Die G0-Spikes sind ausdrücklich kleine Risikoproben, keine zweite Applikations-
orchestrierung oder neue Laufzeit. Keine Nutzer-ENV/Dumps/Objekte übernehmen.
Testimage erweitert die tatsächliche geprüfte MA-F-Jenkinsbasis ausschliesslich
um gepinntes OIDC; G3 wird das Produkt-HPI aus dem Kandidaten neu bauen. Die
bestehende Basis ist im neuen JSONvertrag per Image-ID und 105 JAR-SHA256 gebunden.
CSV arbeitet nur mit synthetischen Bytes und vorhandenem gepinnten Pilotmodell.
Keine Implementiererlogs als eigenen Test ausgeben.

G00: sechs Kandidaten-HEADs/saubere Trees und unveränderliche Workspacevorlage
prüfen; BASELINE nennt die vor G0 vorhandene ungetrackte Nutzerhistorie, die nicht
in diesen Kandidaten gehört. Lokale Bucket-/DB-/Jobinventur ist lesend durchgeführt
und bereinigt dokumentiert. Reviewer greifen niemals auf den Nutzerbestand zu.
G04: konkrete Modell-/Retirement-/Sodatafeaturematrix gegen die echten Pfade und
Aufrufer lesen. G1 darf nur alte eindeutig lokale ch.so.daten-Bytes löschen und
muss alle privaten Referenzen erhalten; unbekannte Sourceobjekte bleiben geschützt.

## Ergebnisziel

G0 soll beweisen, dass die benötigten APIs/Validatorfunktionen wirklich verfügbar
sind und die nächste Phase prüfbar isoliert ist. Kein G1–G5-PASS vorwegnehmen.
Mindestens eine eigene risikogerechte Gegenprobe ausführen. Der Reviewrequest
enthält keine selbstreferenzielle Head-ID; der Runner bindet echte Commits danach.
