# Reviewrequest MA-G2 – Fachmodell, Rechte und Lieferauftrags-Backend

- STACK base: `3fce2fb1360a675a2e966824ec53404f25e0213a`
- ADMIN base: `e338727dcff18f2d1d3a803fc29e31417f99ac08`
- PUBLIC base: `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS base: `f32e40253cdd03a9327b66582aa2050557301239`
- PLUGIN base: `5535624776f3c1958192f45782f8724c08b31dd7`
- TOPICS base: `7c83135d69ada644e6e9a0352c3eb1308f798861`

Alle G20–G29 frisch prüfen; keine übernommenen Urteile. Anforderungen vollständig
lesen und eigenen Code-/Zielreview sowie eigene tatsächlich ausgeführte Gegenprobe
vornehmen. Die unten genannten Tests sind Hilfen, kein Ersatz für eigene Prüfung.
Keine Produkt-/Test-/Anforderungsdateien ändern, auch nicht durch Generatoren.

Umfang und aktuelle Grenzen: `MA-G2_BACKEND.md`. G0/G1 sind unabhängig akzeptiert;
MA-G3–G5 sind nicht implementiert/abgenommen. Die lokale Nutzerinstanz bleibt
unverändert auf G1. Keine Original-ENV, Objekte oder Tokens verwenden.

## Änderungen

- Aus ili2pg stammendes endgültiges G2-Fachmodell mit fünf Capabilities,
  CSV-Konfiguration, konsistentem Authority-Entzug und Initiator der Annahme.
- Bekannter nichtleerer G1→G2-Upgrade, tatsächliche Metadaten/Mapping, 17 auditierte
  Fachtabellen; zusätzlich explizite `di_ingest`-Tabellen und Runtimeguards.
- Versionsgebundener CSV-Vertrag aus TOPICS, echte ili2c-Metadatenprüfung,
  deterministische exakte UTF-8-Kanonisierung. G2 genehmigt nur den unveränderten
  numerischen Pilotvertrag; weitere MVP-Typen und echte Verarbeitung folgen G4.
- Scopebegrenzte Lieferantenverwaltung und CSV-Konfiguration im bestehenden
  Managementbrowser, CSRF/Origin, ausdrückliche Bestätigungen für Amtsweite und
  Autopublikation. Expliziter enger Bootstrap, keine normalen Fachseeds.
- Getrennte kryptografische Benutzer-/Dispatcher-/Executorketten mit festen
  Audiences/Clients/Rollen, aktuelle PG-Identität, zusätzlicher Plugin-Nachweis.
- Submission/Seal, Idempotenz, dauerhafter Dispatch, Dataset-Slot, ein Claim,
  persistente Fence-/Leasebindung, typisierte geordnete Checkpoints, sichere
  Status-/Reportsichten, expliziter Retry/Cancel.
- Gemeinsamer Autorisierungs-Guard und tatsächlicher PG-/Cayenne-Fachcommit mit
  Originalbenutzerprüfung, Version, drei Distributionen, Actor/Initiator, Audit,
  COMMITTED und Projektion ausstehend. Autorisierungsrevision/Prüfzeitpunkt im
  unveränderlichen Ereignis. Keine Netzoperation unter Fach-/Autorisierungssperren.
- Einziger Annahmekern ist der refaktorierte DeliveryRegistrationService.
  Manuelle Versionsregistrierung und Dateiverifikation/-aktivierung samt
  Rclone-Verifikator/CLI sind entfernt. Historische unknown/prepared-Testfixtures
  sind ausdrücklich test-only, keine normale Produkt-API.

`COMMITTED` wird nicht als PUBLISHED ausgegeben. Tatsächlicher CsvValidator,
Storage-/CH-/Format-Readback und Projector sind MA-G4. Die G2-Abschlussprüfungen
verwenden ausdrücklich synthetische Attestierungen des vertrauenswürdigen
Executors; sie sind kein vorgetäuschter End-to-End-CSV-Nachweis.

## Ausführbare Nachweise

Im isolierten ADMIN-Checkout:

```sh
python3 scripts/test_models.py
./gradlew test --tests '*CsvContractTest' --console=plain
```

G20: echte Compiler-/Validatorläufe mit gültigem und acht ungültigen XTF-Fällen,
beabsichtigte semantische Error-Diagnose statt Texttreffer im Informationslog.
`test_models.py` beschafft ausschliesslich die exakt gepinnten offiziellen Tools
in sein eigenes ignoriertes `.runtime/`; keine Nutzerdaten.

Im isolierten STACK-Checkout:

```sh
python3 scripts/test_ingestion_definitions_g2.py
python3 scripts/test_ingestion_schema_g2.py
python3 scripts/test_ingestion_credentials_g2.py
python3 scripts/test_ingestion_backend_g2.py
```

- G20/G21: Schemaharness baut den bekannten G1-Vorgänger aus dessen lokalen
  Git-SHAs, erzeugt echte befüllte alte Fach-/Grant-/Auditdaten, verweigert einen
  unbekannten Fingerprint vor DDL und führt den G2-Upgrade aus. Alte Spaltenwerte,
  IDs, private Referenzen und historische Auditzeilen werden vollständig gehasht
  verglichen. Export mit echtem ili2pg und Validierung gegen die Zielmodelle.
  Zusätzlich unabhängige frische DB, keine Konfigurations-/Lieferrechtseeds.
- G22/G23/G25/G26/G27/G28/G29: Backendharness mit frischer eigener PG-DB. Echte
  Cayenne-/JDBC-Transaktionen, Gruppen-/Amtswege, künftige Datasets, begrenzter
  Bootstrap/Delegation, inaktive Identität, Seal-/Auftragsschlüssel, konkurrierende
  Claims, unterschiedliche Attemptziele, Stalefence und Retry/Cancel. Annahme und
  verlorener Ack, kein read_data aus submit, kein COMMITTED-Downgrade.
  Widerruf/Membershipentzug/Principaldisable vor Abschluss; beide parallelen
  Guardreihenfolgen. Erzwungener Fehler nach Flush, Rollback von Fachobjekten,
  Audit und Prozessstate sowie leerer Pool-Auditkontext.
- G23/G24/G29: Derselbe Harness startet die wirkliche Springanwendung gegen diese
  eigene DB, eigene RSA-/JWKS-HTTPquelle und echte signierte Tokens. Falsche
  Signatur/Issuer/Audience/Tokenart/Client/Rolle/Dienstcredential negativ;
  Benutzer-/Serviceprofile und PG-Principaltypen getrennt. Unbekannte/doppelte/
  nachfolgende JSON-Felder und tatsächliche Bodyübergröße abgewiesen. Browser-
  Lieferverwaltung mit echten CSRF-/Origin-Anfragen; Leserecht verleiht keinen
  Zugang zu fremder Lieferprovenienz. Unbekannter Signaturschlüssel bei gestoppter
  JWKS-Quelle ergibt 503.
- Credentials: ausschliesslich eigene synthetische Runtime, atomare explizite
  Vorbereitung, unveränderte bestehende Bytes/Werte, 0600, Wiederholung unverändert,
  vorhandener ungültiger Wert wird nicht automatisch überschrieben.

Jeder Harness erzeugt ein eigenes kanonisches Compose-Projekt mit privaten
Pfaden und Testcredentials; gestartet werden nur PG und kurzlebige Tools. Es
werden keine Nutzer-Volumes kopiert oder bestehende Dienste umgestaltet.
Private Testlogs stehen unter den eigenen `.runtime/mag-g2-*`-Ordnern. Der
Schemaharness ist absichtlich kein Normalstart. Die Vorgänger-Testseedquelle wird
nur aus den gepinnten G1-Commits gebaut.

Die echte Entwicklergenerierung wurde aus dem ili2pg-Referenzschema durchgeführt.
Bei inkrementellem cdbimport wurden zunächst ignorierte Reverse-Relationship-
Namenskollisionen erkannt. Vollständiger Stockimport aus leerer DataMap und
anschliessende Wiederholung beseitigten diese. Abschliessend waren alle 18
Artefakte (17 Auto-Klassen und DataMap) bytegleich, ohne ignorierte Migrationfehler.
Details/Hashbindungen stehen in `MA-G2_MODEL_EVIDENCE.md`. Reviewer darf eine eigene
Generierung nur in einer eigenen Arbeitskopie ausserhalb der Produktbäume
vornehmen; Generatoren niemals auf die Kandidatendateien schreiben lassen.

Der explizite SQLupgrade läuft mit dem vorhandenen PG-Administratorkonto, weil
CREATE SCHEMA nicht zur Runtimeberechtigung des di_migrator gehört. Runtime-
konten bleiben eingeschränkt. Dieser Job ist kein Web-/Normalstartpfad.

Eigene Gegenprobe z.B. abweichender Artifactslot/Manifest trotz korrekter IDs,
Originalprincipal nach Seal inaktiv, oder widerrufener direkter Grant mit weiter
aktivem Gruppenweg. Hypothese, konkrete Ausführung und beobachtetes Ergebnis
festhalten. Bei Mängeln NACHARBEIT; bei fehlender tatsächlicher Prüfbarkeit
NICHT_PRUEFBAR. Nur ABGENOMMEN an den vollständigen Handoff-SHAs öffnet MA-G3.
