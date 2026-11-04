# MA-F1 – kanonische Topologie

Die Defaultservices in `compose.yaml` sind genau PostgreSQL, Keycloak, Garage,
Origin, Gateway, Admin, Sodata, Jenkins, ClickHouse und Superset. Einmaljobs sind
explizite Setup-/Tools-/Testprofile. Keine Container-Namen, Host-JARs, zweite
Anwendungsdefinition oder Netzwerkraumkopplung. Interne Dienste haben keine
Hostports. Native PG16.10/PostGIS3.5.2-Basis aus F0 unverändert.

`compose_runtime.py` bindet Projekt, Env, Runtime und Composefile explizit.
Bestehende fremde/alte Projekte werden nicht als frische Umgebung adoptiert.
Das ist zunächst die interne Basis; Root-Lifecycle-Umstellung ist F3.

Admin-/Sodata-Images werden aus Quellen gebaut. Das explizite Toolimage enthält
Java25, den gepinnten ili2pg-Compiler, PostgreSQL-Clients und rclone; keine neuen
Hostwerkzeuge für Setup/Start nötig. Das vorhandene Jenkinsimage bleibt anhand
seiner lokalen Image-ID erhalten. Die unveränderte Modell-/Cayenne-/Auditbasis
wird im leeren Managementziel eingerichtet, danach nur lesend verifiziert.
Kein automatischer Fachseed oder Grant. Keycloak und Superset haben eigene DBs
und Konten; fünf Managementkonten plus NOLOGIN-Owner bleiben getrennt.

Garage erhält einen eigenen Origin-Schlüssel: Lesen im verwalteten privaten
Bucket, kein Schreiben/Owner/Neuanlegen. Der bestehende Operatorschlüssel ist
getrennt. OIDC/forward-auth/raw-path-Filter und WebDAV-Range/ETag bleiben aus dem
abgenommenen MA-E-Vertrag; genau ein Upstream pro Dienst. Die früheren öffentlichen
Bucketpfade sind verweigert. Jenkins hat eigene interne Adresse; der Themenadapter
unterbindet alte Portalreloads im DB-Katalogmodus. Superset überschreibt eine
schon gespeicherte verschlüsselte Verbindung nicht.

## Teststand

Eigene einzigartige Projekt-/Port-/Volume-/Runtime-/Secretbindung. Frischer
Imagebuild, explizites Setup, Standard-Compose-Up aller zehn Dienste erfolgreich.
F04–F06: echte Composelabels, drei DBs, native PG-Version/Extensions,
leerer Katalog vor Seed; fünf App-Konten positiv im eigenen DBbereich und
negativ an existierender fremder App-DB; Owner-/Audit-DMLgrenzen.

F07: ausdrückliche Testfixture, acht private Dateien, streaming-verifizierte
Aktivierung, anonym open200/restricted401, gültiger Ben-Token403. Echter
Browsercodeflow Anna→Antrag→Claudia→Genehmigung→Datei; anschliessend alle
historischen CSV-/XLSX-Versionen mit gleichem Anna-Token/Byteshash200.
Interne API und alte Bucketpfade403. Testbrowser/Java25 ist eine Testabhängigkeit,
kein Bestandteil des normalen Startvertrags.

F08: Jenkinslogin und Anlieferungsredirect erreichbar. Echter Gradle7.6.4/Java17-
Adapterlauf im isolierten Jenkins, `reloadPortal=true` bei DBmodus trotzdem
SKIPPED; kein externer Reload. Gespeicherte verschlüsselte Supersetverbindung
führt echten SELECT auf ClickHouse aus. Nach kleinem Fix am Garage-Fehlerpfad
nur Toolimage gebaut und vorhandene Bucket-/RO-Key-Einrichtung idempotent
wiederholt; Schlüssel bleiben erhalten. Kein unveränderter Fachsuite-Neulauf.

Quellen weiterhin unverändert in Betrieb. Keine tatsächliche Übernahme oder
Retire erfolgt; F2/F3 noch ausstehend. LOCAL_CUTOVER_PENDING.
