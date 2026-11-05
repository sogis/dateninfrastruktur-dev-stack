# MA-G – konkrete technische Festlegungen

## G0: vorhandener Code und Pins

Kein lokaler S2-ClickHouse-Lader in den sechs aktuellen Branches oder Dirty Trees
gefunden. Es gibt echte CsvValidator-Tasks und DuckDB-CSV/XLSX/Parquet-Konvertierung
in TOPICS `shared/gradle/datenportal-publication.gradle`. G4 übernimmt geeignete
Validator-/Formatbausteine in den generischen Runner und ergänzt den fehlenden
CH-Snapshotwriter. Der alte Publisher wird nicht zum neuen Loader erklärt.

OIDC-Spike: `oic-auth:4.731.v4932b_506e767`, publiziertes erforderliches Core 2.539,
vorhandener Core 2.555.2. `OicCredentials.getAccessToken()` liefert String,
`getExpiresAtMillis()` Long. Der Code der exakten Pluginversion wurde gelesen.
Manual-Konfiguration trennt externen Issuer/Authorization-URL von internem
Token-/JWKS-Endpunkt; Signatur-, Issuer-, Expiry- und Audienceprüfung bleiben an.
PKCE S256 ist im synthetischen Keycloak-Client vorgeschrieben. G0 baut einen
Testaufsatz auf dem vorhandenen Image; G3 muss das neue Produkt-HPI vollständig
neu bauen und Runtime-/Image-/HPIhashes prüfen.

CH-Namensvertrag für G4: private immutable Tabellen in `di_data`,
`v_<version uuid hex>_<execution uuid hex>`; stabile abgeleitete Sicht
`di_public_sql.ds_<dataset uuid hex>_i_<issue uuid hex>_current`.
Nur der Projector ändert diese Sicht; Loader dürfen nur eigene Kandidaten schreiben.
Es gibt keine persönliche SQLrechteprojektion. Diese Namen sind serverbestimmt.

Katalog und Access erhalten die neuen Modellnamen mit Datum `20261105` und
VERSION `2026-11-05`. G1 entfernt Storageprofil/LegacyURL, G2 ergänzt die
fachlichen Lieferverträge. Kein bereits extern veröffentlichter Modellstand wird
überschrieben. Der konkrete Zielhash wird spätestens mit G2 fixiert.
