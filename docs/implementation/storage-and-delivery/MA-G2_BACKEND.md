# MA-G2 – Liefermodell und Backend

Implementierungsstand, noch keine unabhängige Abnahme. MA-G3 bis MA-G5 bleiben
bis zur jeweiligen Abnahme gesperrt. Die lokale Nutzerinstanz läuft weiterhin
mit dem abgenommenen MA-G1-Schema und dessen Images.

## Fachmodell und expliziter Upgrade

Catalog/Access 20261105 enthalten die fünf Capabilities, die optionale
CSV-Konfiguration je Dataset und vollständige Authority-Revocation. Eine
`accept_delivery`-Aktion bindet technischen Actor und ursprünglichen Initiator.
Die Fachtabellen stammen aus unverändertem ili2pg. Cayenne wird aus der echten
Referenzdatenbank generiert; technische Prozessdaten liegen getrennt in
`di_ingest`. Keine Hibernate-/Startmigration und kein automatischer Fachseed.

Der Upgrade kennt ausschliesslich den gepinnten MA-G1-Vorgängerfingerprint.
Unbekannte Vorgänger und vorhandene nicht zuordenbare Authority-Revocations
stoppen vor DDL. IDs, bestehende Attribute, Grants und historische Auditzeilen
bleiben erhalten. Neue CSV-Konfigurationen und Lieferrechte werden nicht
stillschweigend erzeugt. Der explizite Compose-Migrationsjob benötigt wegen
`CREATE SCHEMA` das vorhandene PG-Administratorkonto. Die Webanwendung bleibt
`di_writer`; Public-/Authz-Konten erhalten keinen Ingestionzugriff.

Die tatsächliche ili2pg-Ausgabe enthält nicht alle modellierten role-basierten
UNIQUEs. Zusatz-DDL erzwingt deren wirkliche Spaltenkombinationen; Runtimeguards
prüfen diese Indizes. Strukturelle Schemaänderungen sind nach einer versiegelten
Submission oder einer angenommenen Version gesperrt. Beschreibungen bleiben
korrigierbar.

## Identität, Rechte und Verwaltung

Browserverwaltung verwendet weiterhin den bestehenden geprüften JWT-/CSRF-/
Origin-Weg. `/management/delivery` zeigt aktuelle Office-/Datasetzuständigkeiten.
`manage_submitters` vergibt ausschliesslich `submit_data`, mit Scope, Zeit und
Begründung. Es gibt keinen HTTP-Parameter für andere Capabilities und keinen
Selbstdelegationspfad für `manage_submitters`. Amtsweite Rechte umfassen auch
künftige Datensätze; die Oberfläche fordert dazu eine ausdrückliche Bestätigung.
Lieferrechte vergeben weder `read_data` noch SQL-/Metadaten-/Publikationsrechte.

Der lokale Operator `compose_operator.py bootstrap-submitters REQUEST.json`
vergibt ausschliesslich den ersten Lieferantenmanager. Die private JSON-Datei
liegt im ausgewählten Runtimeordner (kein Symlink, keine Gruppen-/Fremdrechte,
maximal 16 KiB):

```json
{"schemaVersion":1,"commandId":"<UUID>","officeId":"<UUID oder null>","datasetId":null,"verifiedIssuer":"<ausserhalb dieses Befehls geprüfter Issuer>","verifiedSubject":"<geprüftes sub>","reason":"Begründung"}
```

Genau einer der beiden Scopes ist erforderlich. Inaktive Identitäten werden
nicht reaktiviert. Keine Normalstartaufrufe. Die manuelle Registrierung neuer
Versionen sowie der bisherige Dateiverifikations-/Aktivierungsoperator wurden
entfernt. `DeliveryRegistrationService` ist der einzige fachliche CSV-Annahmekern;
Rückzüge bestehender Dateien bleiben explizit möglich. Historische
unknown/prepared-Testdaten entstehen ausschliesslich in Testprofilen.

## Interne HTTP-Grenze

Alle Pfade liegen unter `/internal/ingestion`, bleiben im Compose-Netz und werden
von APISIX nicht öffentlich weitergereicht. Mutationen verlangen genau einen
UUID-`Idempotency-Key`, `application/json` und tatsächlich höchstens 64 KiB.
Unbekannte Felder, doppelte Schlüssel, zusätzliche JSON-Werte und Typkonvertierung
werden verweigert. Identitäten kommen ausschliesslich aus dem signierten Token.

| Profil | Feste Prüfung |
|---|---|
| Fachperson | RS256, aktueller Issuer, Audience `di-ingestion-user`, Access-Token `typ=Bearer`, `azp=jenkins-delivery`, zusätzlicher `X-DI-Plugin-Credential` |
| Dispatcher | Audience/azp `di-ingestion-executor`, Access-Token, Clientrolle `dispatch`, aktiver PG-Serviceprincipal |
| Executor | Dasselbe Serviceprofil, Clientrolle `execute`, zusätzlich konkrete Execution/Fence/Leasebindung |
| Managementbrowser | Bestehende Management-Audience, CSRF und Origin |

JWKS-/Authentifizierungsdienstfehler sind 503; ungültige Tokens 401; fehlender
Dienstnachweis oder fehlende aktuelle Fachrechte 403. Personenheader haben keine
Wirkung. Keycloak-/Jenkins-Codeflow und Produktkonfiguration folgen in MA-G3;
MA-G2 testet bereits die wirklichen Filterketten mit eigenen RSA-Schlüsseln und
JWKS über HTTP, ohne gemockte Authentication.

Frische explizite Runtimeinitialisierung erzeugt getrennte private
`DI_INGESTION_PLUGIN_SECRET`- und `DI_INGESTION_LEASE_SECRET`-Werte. Bestehende
Instanzen benötigen deren einmalige explizite Vorbereitung vor dem geprüften
Upgrade: `python3 scripts/prepare_ingestion_g2.py --env <private-runtime.env>`.
Der Befehl hängt ausschliesslich fehlende Werte atomar an; bestehende Bytes und
Credentials bleiben erhalten. Er migriert keine DB, startet keine Dienste und
vergibt keine Fachrechte. Normalstart erzeugt oder rotiert diese Werte nicht. Uploadstandard:
100 MiB; dokumentiertes hartes Maximum 256 MiB. Definitionen dürfen niedrigere
Grenzen setzen. Die Admin-Webanwendung erhält keine S3-Schlüssel.

## Aufträge, Ausführungen und Annahme

Submission-ID und reservierte Version werden serverseitig erzeugt. Seal bindet
Bytes, SHA256, Anzeigename und den einzigen zulässigen Spoolpfad
`uploads/<submission UUID>/input.csv` mittels HMAC-Nachweis des begrenzten
Pluginstreams. Der spätere Worker muss die tatsächlichen Bytes erneut prüfen.

Dispatch ist dauerhaft und at least once. Derselbe Dataset teilt genau einen
Slot über alle Ausgaben; verschiedene Datasets haben getrennte Slots. Pro
Dispatch gewinnt genau ein Jenkinslauf des festen Jobs `di-csv-ingest`. Fence,
aktive PG-Serviceidentität und Lease werden bei schreibenden Callbacks erneut
geprüft. Das Leasegeheimnis ist HMAC aus einem privaten persistenten Schlüssel
und der zufälligen Execution-ID mit vollständiger Laufbindung; gespeichert wird
nur SHA256. Dadurch lässt sich derselbe verlorene Claim-Ack sicher wiederholen,
ohne Klartextgeheimnisse in PG abzulegen. Leasezeit fünf Minuten.

Eine abgelaufene Ausführung erhält keine neue Schreibberechtigung. Ein bewusster
Retry braucht frische Fachrechte und einen beendeten früheren Versuch. Alle
Attempt-Outputs und CH-Kandidaten haben eigene UUID-basierte Ziele; spätere alte
Worker können den Gewinner nicht überschreiben. Cancel invalidiert den alten
Lauf und gibt ausschliesslich dessen uncommitteten Slot frei.

Die fünf Checkpoints sind geordnet und typisiert. Modell-/Definitionshashes,
Input, vollständige Zeilenanzahl und Datenhash, CH-Ziel/Schema sowie drei feste
Format-/Objektslots müssen zum gespeicherten Plan passen. Die Belege sind
Attestierungen des vertrauenswürdigen Executors. Tatsächliche GRETL-, S3-, CH-
und Format-Readbacks werden in MA-G4 ausgeführt; synthetische MA-G2-Belege werden
nicht als fachlicher End-to-End-Nachweis bezeichnet.

Annahme sperrt zuerst den Autorisierungs-Guard (shared), danach Dataset,
Submission und Execution. Rechte-/Membership-/Principal-/Konfigurationsänderungen
belegen den Guard exklusiv. Im selben kurzen PG-Commit werden aktuelle
Originalbenutzerrechte und Vertrag erneut geprüft, Version und drei
Distributionen via Cayenne angelegt, `currentVersion`, Actor/Initiator, Audit,
`COMMITTED` und Projektionsbedarf gespeichert. Keine Netzoperation unter diesen
Sperren. Das technische Resultat ist strikt an die Checkpoints gebunden.

Ein identischer Abschluss nach verlorenem Ack liefert dieselbe Version, auch
nach späterem Entzug. Ein anderer Resultdigest ist Konflikt. COMMITTED wird durch
Fehler-/Cancelcallbacks nicht zurückgestuft. Ohne bestätigte CH-Projektion lautet
die Antwort 202/COMMITTED („Angenommen; SQL-Aktualisierung ausstehend“). Projector
und PUBLISHED-Zustand folgen mit tatsächlicher CSV-Verarbeitung in MA-G4.

Status-/Reportantworten zeigen nur eigene Aufträge aktiver Personen oder aktuell
zuständige Lieferantenmanager. `read_data` öffnet keine Provenienz. Weder
Spool-/Leasewerte noch rohe Runnerlogs oder vertrauliche Konfigurationssnapshots
werden ausgeliefert. Publicviews enthalten keine Ingestiondaten.

## Nachweise

```sh
python3 scripts/test_ingestion_definitions_g2.py
python3 scripts/test_ingestion_schema_g2.py
python3 scripts/test_ingestion_backend_g2.py
```

Die Tests verwenden eigene kanonische Compose-Projekte, Ports, Volumes und
synthetische Credentials. Der Backendtest benötigt nur PG und kurzlebige
Toolprozesse, keinen Test-Jenkins und keine Kopie der lokalen Nutzerdaten.
Java-Unitvertrag: ADMIN `./gradlew test --tests '*CsvContractTest'`.
Rohlogs liegen ausschliesslich in ignorierten privaten Runtimeordnern.
