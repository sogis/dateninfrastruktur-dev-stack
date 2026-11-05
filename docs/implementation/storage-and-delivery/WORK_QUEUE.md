# MA-G Arbeitsstand

MA-G0 unabhängig ABGENOMMEN; MA-G1 Code-/Migrationsabnahme und lokale Umstellung abgeschlossen; abschliessendes Retirementdelta im Review.

| Phase | Status | Unabhängiger Nachweis |
|---|---|---|
| MA-G0 | ABGENOMMEN | review/MA-G0-accepted.md |
| MA-G1 | IN_REVIEW | review/MA-G1-request.md |
| MA-G2 | NOT_STARTED | – |
| MA-G3 | NOT_STARTED | – |
| MA-G4 | NOT_STARTED | – |
| MA-G5 | NOT_STARTED | – |

## Lokaler Zustand

`LOCAL_STORAGE_CUTOVER_VERIFIED` – 16 private Referenzen/13 756 Bytes byte- und
metadatengleich erhalten; genau ein privater Bucket, genau Reader/Writer; alte
Keys/Buckets entfernt. Alle 16 Fachtabellen, historische Auditdaten, fünf
Identitätstabellen und Jenkinsjobdefinitionen unverändert. Zehn gesunde Dienste,
same-token Downloadvergleich und wiederholtes Setup bestanden. Detailbelege privat
unter `.runtime/dateninfrastruktur/ma-g1-cutover/`; siehe LOCAL_STORAGE_CUTOVER.md.

## Echte Entscheidungen / Blocker

Nur konkrete Punkte, keine vorgemerkte neue Architekturstudie. Historische MA-F-Urteile bleiben in ihren bisherigen Dateien.
