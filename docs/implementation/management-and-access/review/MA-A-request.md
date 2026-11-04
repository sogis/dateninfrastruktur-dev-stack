# Reviewrequest MA-A

## Ausgangspunkt

- ADMIN base `f3cc249fb0bd39261afdd2d48ee83598ac5b6958`.
- STACK base siehe akzeptierter MA-0-Kandidat `b5957ce`; anschliessender separater Nachweiscommit `a8e303c633d00db29ae4d24bcb53db3491b67d31` ändert nur bereinigte Abnahme/Arbeitsstand.
- PUBLIC unverändert seit MA-0: `8349be8aba4036ca0bb56e89cb62398e34404a5e`.
- MA-0 unabhängig akzeptiert, Rohbericht/Runnerbindung unter ignoriertem MA-0/20261104T141858Z; bereinigte Abnahme `review/MA-0-accepted.md`.
- Neue Phase, kein übertragener statt neu ausgeführter MA-A-Pflichtnachweis.

## Änderungen

Zwei neue ILI2.4-Modelle in ADMIN/models: Catalog und davon abhängiges Access.
Dataset(kind=series|standalone) einziger Rechteanker, UUIDOID durchgängig;
keine ACL/Metadatenkopien auf Issue/Version/Distribution. Normalisierte Themen,
Keywords, Schemaattribute. Principals, lokale Gruppen, scoped Authorities,
Request/immutable Decision/beendbarer Grant und CatalogAction getrennt.
Vollständige di.audit-Metaattribute einschliesslich Assoziationen, gezielte
Redaction auf Principal.displayName. Keine DB-/UI-Vorwegnahme.

Positive synthetische XTF2.4-Folge mit Standalone/Serie, historischen Formaten,
Antrag/Genehmigung/Ablehnung/Direktvergabe/Widerruf, Gruppen-/Zeitfällen.
Fünf Negativdateien verletzen jeweils einen beabsichtigten Vertrag.
`models/constraints.md` weist jede wichtige Regel Modell, DB oder Service zu;
Folgepflichten werden nicht als bereits implementiert ausgegeben.

Toolkompatibilität konkret reproduziert: verschachtelter DATETIME-Alias führt
im Validator beim Zeitvergleich zu `incompatible values`. Expliziter XMLDateTime-
Formatbereich löst dies bei weiter aktiven Constraints; reales Invalidintervall
wird fachlich abgelehnt. Vokabulare aus gepinnter Base-Quelle ohne Codeänderungen.

## Neu ausgeführte Testauswahl

Alle Kommandos aus ADMIN: `python3 scripts/test_models.py` (Exit0).

| ID | Nachweis |
|---|---|
| M03 | tatsächlicher ili2c5.6.9-Lauf beider Modelle, IMD16; positive Datei durch ilivalidator1.15.0 mit forceTypeValidation/allObjectsAccessible |
| M04 | erzeugtes IMD16: UUID-OIDs, alle fachlichen Grant-/Decision-/Requestkatalogziele ausschliesslich Dataset, keine gemeinsamen Metadaten auf Children |
| M05 | fünf echte XTF-Negativprüfungen: UniqueIdentifier, Grantintervall, Scope-XOR, verschachtelte Gruppe, available-Datei ohne Hash; erwarteter semantischer Fehler erforderlich, Compiler-/Toolfehler zählt nicht |
| M06 | Workflowreferenzen/DirectGrant ohne Request/Revoke, Unicode und Zeilenumbrüche, komplette Audit-Metaattribute und Redaction; alte Vokabulare identisch |

Rohbelege pro Compiler/Validatorlauf liegen in ADMIN/.runtime/model-tests/.
Reviewer führt das Kommando selbst aus und erfindet eine relevante neue Gegenprobe.

## Nichtbetroffenheiten / Grenzen

MA-0-Runner und Compatibility-Spike unverändert. Kein neuer PG-/Gateway-/OIDC-
oder Foundationlauf für reine neue Fachmodelle nötig. SQL-Mapping, Transaktionen,
Audittrigger und Serviceauthz sind ausdrücklich erst MA-B/MA-C. Dateiexistenz,
öffentlicher DB-Katalog und Downloadautorisierung folgen MA-D/MA-E. Modellvalidator
behauptet keine automatische SQL-Constraintumsetzung. Keine Legacydaten importiert.

## Übergabe

Lokale Produktcommits vor Handoff. Dessen exakter SHA-Satz und Spec-/Requesthashes
sind verbindlich. Erst unabhängiges ABGENOMMEN öffnet MA-B.
