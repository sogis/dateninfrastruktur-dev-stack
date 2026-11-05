# G0 – konkrete Modell-/Upgradezuordnung

Ausgangsmodelle: ADMIN `models/SO_AGI_DataInfrastructure_Catalog_20261104.ili`
und `models/SO_AGI_DataInfrastructure_Access_20261104.ili`. Kein Modellreset.

| Phase | Modelländerung | Physischer Nachweis / Schutz |
|---|---|---|
| G1 | Catalog_20261105 Distribution entfernt storageProfile/legacyAccessUrl; UNIQUE objectKey | Frische ili2pg-Referenz, tatsächliche Spaltennamen/Constraints vergleichen; UUIDs/Bytes erhalten; Kollisionen vor DROP prüfen |
| G1 | Access_20261105 IMPORTS/DEPENDS ON auf neuen Catalog | Kein zweites Runtime-Modell; Metadaten/Fingerprint/Cayenne/Publicviews gemeinsam umstellen |
| G2 | AuthorityAssignment capability ergänzt submit_data/manage_submitters | Bestehende Enumwerte und XOR office/dataset erhalten; getrennte Delegation |
| G2 | AuthorityAssignment revocationReason und AuthorityRevoker.revokedBy optional | Reason/Zeit/Revoker gemeinsam konsistent; vorhandene Entzüge vor Upgrade prüfen, keine Akteure erfinden |
| G2 | CsvDeliveryConfiguration enabled/automaticPublication BOOLEAN, definitionKey TEXT*128, definitionSha256 Sha256, allowedModes Enum | Je Dataset 0..1, genau ein DataSchema, Audit full; bestehende Datasets bleiben deaktiviert |
| G2 | CatalogAction ergänzt accept_delivery und optional initiator Principal | Actor bleibt ausführender Dienst; Initiator aus Submission, unveränderliche alte Snapshots |
| G2 | Strukturell gebundene DataSchema-Fingerprints schützen | Angenommene/versiegelte Verträge nicht unter gleicher ID verändern |

Technische Tabellen `di_ingest` gemäss SPEC_INGESTION_API sind explizite versionierte
SQLmigrationen mit FKs auf die tatsächlich gemappten Fachobjekte. Sie ersetzen
keine ILI-Fachmodelle. Ein Guard in `di_ops` wird vor Dataset/Submission gesperrt;
Berechtigungsänderungen exklusiv, finaler Commit geteilt. Keine externe I/O unter
Guard und keine zweite Transaktionsconnection beim Cayenne-Flush.

Upgrade: vollständiger Ausgangsfingerprint → explizite bekannte Migration →
XTF-Export/Validierung → Cayenne cdbimport/UUIDnormalisierung/cgen → Auditcoverage
und Runtimefingerprint. Nichtleere Regression mit Grants/Decisions/Audit und
historischen Distributionen; unbekannter Stand verweigert Mutation.
