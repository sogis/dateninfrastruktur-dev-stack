# Reviewrequest MA-G1 – privater Einbucketbetrieb und bekannte Bestandsübernahme

- STACK base: `67ffd5801d40a98a0b5f8bc0706288cb4970bb62`
- ADMIN base: `b4a8c2726da16373ee9e0fd02ecb715fba482612`
- PUBLIC base: `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS base: `f32e40253cdd03a9327b66582aa2050557301239`
- PLUGIN base: `5535624776f3c1958192f45782f8724c08b31dd7`
- TOPICS base: `7c83135d69ada644e6e9a0352c3eb1308f798861`

## Kandidat und Grenzen

G1 ersetzt Garage-Fresh-/Importzweige durch gebundenen `GarageProvisioner`,
dedizierte Reader-/Writerkeys, kanonische Origin-/Operatorpfade und geschlossene
Normalstart-/Setupgrenzen. Keine Defaultkeyinitialisierung im Garage-Dauerprozess.
Storageverifikation ist lesend; wiederholtes explizites Setup darf falsche Rechte
korrigieren, erzeugt aber keine neuen Schlüssel oder Seeds.

Catalog/Access `20261105` wurden mit unverändertem ili2pg5.5.2 wirklich erzeugt.
Stock cdbimport/cgen gegen die gehärtete reale Referenz ist byteidempotent.
Mapping, ILI-Metadaten, Auditpolicy, Cayenne und Fingerprint sind gemeinsam
umgestellt. Die bekannten alten Modelle liegen nur in Upgrade-Testressourcen;
alte V001–V009 und Herkunftsdaten bleiben als Schema-/Datengeschichte erhalten.
V010 entfernt die zwei alten Storagefelder, macht objectKey alleine eindeutig
und benennt bekannte Basket-Topics um. Ein unbekannter Vorgänger wird vor DDL
abgelehnt. Upgrade schützt Fachdaten und historische Auditzeilen innerhalb
derselben Transaktion durch Locks und Vorher-/Nachherhashes.

Der abgelöste Legacyimport wurde aus aktiver Java-/Gradle-/Operator-API entfernt.
Die vorhandene geprüfte Download-/forward-auth-Kette bleibt erhalten. G2-Rechte,
G3-Jenkinsjob und G4-Verarbeitung werden noch nicht behauptet oder implementiert.

## Echte Tests selbst frisch ausführen

Aus isoliertem STACK:

```sh
python3 scripts/test_ingestion_storage_unit.py
python3 scripts/test_ingestion_storage_g1.py
python3 scripts/test_ingestion_schema_g1.py
python3 scripts/test_ingestion_cutover_g1.py
python3 scripts/test_ingestion_cutover_g1.py --operator
```

Aus isoliertem ADMIN:

```sh
python3 scripts/test_models.py
./gradlew test
```

Java25 aus vorhandenem SDKMAN verwenden, wenn nicht bereits Standard. Docker und
Playwright-Chromium sind vorhanden. Kein Nutzer-ENV/Dump, kein fremder Port,
keine Originaldaten. Jeder Treiber verwendet zufälligen Projektnamen, Ports,
Volumes und synthetische Credentials und bereinigt ausschliesslich eigene
nachgeprüfte Ressourcen. Logs liegen privat im jeweiligen `.runtime/mag-g1-*`.
Die Modell-/Schemaänderung braucht die breitere gezielte G16-Prüfung;
keine pauschale Wiederholung von MA-A–F oder G0 erforderlich.

| Verträge | Ausführung / Bedeutung |
|---|---|
| G10–G13/G18 | echtes Garage: Reader GET positiv, PUT/DELETE negativ; Writer PUT/GET/DELETE positiv, CreateBucket negativ; Ownerfalse/Websitefalse aus tatsächlicher Policy; anonymer GET auf existentes Objekt negativ; zweites Setup bytegleich |
| G14/G15/G19 | echte private Bytes samt Content-Metadaten und allen PG-Referenzen; unbekannte Sourceobjekte, fremder Endpoint, falsche Bucketbindung verweigert; Kopierunterbrechung fortgesetzt; fehlende Runtimeabnahme verhindert Switch; verlorenes DeleteBucket-Ack sicher wiederaufgenommen; Altkey auf existentem Zielobjekt403 |
| G16 | synthetischer, nichtleerer MA-F-Vorgänger aus genau gepinnten Gitarchiven gebaut; unbekannter Fingerprint verweigert; UUIDs/Versionen/Identitäten/Grants/Referenzen/Audit identisch; ili2pg exportiert die echte migrierte DB und Validator prüft Zielmodelle; separater leerer Frischaufbau |
| G17/G13/G18 | zehn kanonische Dauer-Services, normaler Browser-PKCEflow, historische und aktuelle Bytes, same-JWT revoke, HEAD/Range/ETag; Public-Setup bytegleich ohne Auditänderung; echte Neuerstellung Garage/Origin/Gateway; keine Storagecredentials in Web-ENV |
| G14/G19 Operator | `--operator` verwendet zusätzlich den tatsächlichen einmaligen Tooloperator an synthetischer Source, gebundene Inventur, Copy, exakte Altrechtentfernung, neue Policy, Runtimeprobe vor Source-/Keyretirement |

Die zusätzliche `StorageCutoverProbeIT` ist **rein lesend**, verwendet normale
PKCE-Logins und erhält die exakten Tokens für den Vorher-/Nachhervergleich.
Ihre ausgeführten Tests müssen keine fachlichen Auditzeilen erzeugen.
Bestehende `ComposeAcceptanceIT` wird nur an der geschützt namensgebundenen
synthetischen MA-F-Fixture ausgeführt, niemals an Nutzer-Datasets.

## Lokale Umstellung: noch nicht durchgeführt

Originalverbund, alte Buckets, DB, Identitäten und Audit sind bisher unverändert.
Nach dieser unabhängigen Code-/Migrationsabnahme folgt der ausdrücklich
beauftragte enge lokale Cutover über `ingestion_cutover_g1.py` mit echtem
Reviewreceipt und exakt gleichem SHA-Satz. Read-only Plan vor Wartungsfenster;
danach Schreiber stoppen, Inventur erneut binden, einmalig gebundenen lokalen
Altinhalt löschen, private Dateien bytegleich kopieren, Schema/Runtime umstellen,
same-token Downloadprobe, erst dann Altbucket/alte Keys entfernen.

Bekannte Canary und optionale Foundation-Smoke-Datei werden nur bei exakt
nachgewiesenen Bytes als Fixtures behandelt. Foundation-Beweis wird aus dem
hashgebundenen historischen lokalen Quell-ENV und ursprünglichen Fixturecode
abgeleitet und gegen tatsächlichen S3-GET-SHA geprüft; unbekannte weitere
Sourceobjekte/Keybindungen sind geschlossene enge Blocker. Originalgeheimnisse
und Objektinhalte gehören nie in Reviewkontext/Reports.

Die einmaligen Host-/Tooloperatoren sind keine neue normale Lifecycle-API.
Nach tatsächlichem verifiziertem lokalen Abschluss werden sie aus aktiver
Distribution entfernt; eingefrorener G1-Kandidat und Reviewbelege bleiben erhalten.
Erst dieser belegte lokale Abschluss öffnet die Arbeit an G2.

Mindestens eine eigene risikogerechte Gegenprobe entwerfen und wirklich ausführen.
Produktintegrität vor/nach Builds prüfen, insbesondere generierte Cayenne-Dateien.
Reviewer repariert keine Produktdateien. Alle G10–G19 müssen am aktuellen
SHA-Satz selbst belegt sein; Implementiererlogs sind keine eigene Testausführung.
