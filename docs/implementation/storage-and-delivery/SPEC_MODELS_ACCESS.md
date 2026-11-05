# SPEC_MODELS_ACCESS – gezielte INTERLIS-Evolution und Lieferberechtigungen

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Bestehende `Principal`, `GroupMembership`, `AuthorityAssignment`, `AccessGrant`, `AccessDecision`, Katalogklassen und Auditmechanik sind die Grundlage, keine zweite Benutzerverwaltung.

## 1. Versions- und Modellgrenzen

Neue versionierte Modellnamen verwenden, z.B. `SO_AGI_DataInfrastructure_Catalog_20261105` und `SO_AGI_DataInfrastructure_Access_20261105`. Datum beim Implementierungsbeginn konkret prüfen. Bereits extern publizierte Modellversionen nie mit anderem Inhalt überschreiben. Während der noch nicht veröffentlichten MA-G-Entwicklung werden konkrete Modellhashes je Phase gebunden; spätestens G2 ist der fachliche Zielvertrag fixiert.

G1 entfernt die Storagefelder und aktualisiert erforderliche Imports. G2 ergänzt Lieferfähigkeiten und CSV-Konfiguration. Frühere Modellstände bleiben nur als eng benannte Upgrade-/Regressionfixtures oder Git-Historie, nicht als zweite auswählbare Runtime. Sodata benötigt weder Datasheet noch PublishedCatalog.

Keinen separaten „ProcessingProfile“-Katalog oder Spezialjobtyp vorwegnehmen. `csv_standard` ist ein fester Implementierungsvertrag, keine Benutzeroption.

## 2. Catalog: bestehende Klassen und präzise Änderungen

### 2.1 Distribution

| Element | Ziel |
|---|---|
| `format`, `fileName`, `mediaType`, `availability`, `byteSize`, `sha256` | Beibehalten und bestehende Constraints verschärfen, wo der Lieferabschluss Nachweise verlangt. |
| `objectKey` | Beibehalten, eindeutig im einen privaten Backend, serverseitig generiert. |
| `storageProfile` | Entfernen, inklusive SQLspalte/ORMattribut/DTOparameter/UNIQUE-Kombination. |
| `legacyAccessUrl` | Entfernen, keine alte URL als aktiver alternativer Zugriff. |

`UNIQUE objectKey` ersetzt `UNIQUE storageProfile, objectKey`. Vor Umstellung Kollisionen tatsächlich ausschliessen. Es gibt keine neue Verpflichtung, bestehende Distribution-UUIDs oder Keys umzunummerieren.

### 2.2 CsvDeliveryConfiguration – eine kleine fachliche Konfiguration

Neue CLASS im Catalog-Topic, genau 0..1 pro Dataset. Eine CSV-Lieferung ist nur bei vorhandener **aktivierter** Konfiguration möglich. Keine implizite Aktivierung aufgrund der Dateiendung.

| Attribut/Beziehung | Typ / Regel |
|---|---|
| OID | UUIDOID |
| `enabled` | MANDATORY BOOLEAN; Migration bestehender Datasets setzt nicht automatisch true. |
| `automaticPublication` | MANDATORY BOOLEAN; nur mit Capability `publish` veränderbar. |
| `definitionKey` | MANDATORY TEXT*128; technischer Schlüssel aus dem freigegebenen Vertragsbestand, kein Skriptpfad/URL. |
| `definitionSha256` | MANDATORY Sha256; Fingerprint des genehmigten CSV-Vertrags. |
| `allowedModes` | Kleines Enumeration-Attribut `(replace_only, append_only, replace_and_append)`; keine frei erfundene Mehrzweckengine. |
| `dataset` | Genau ein Dataset; pro Dataset eindeutig. |
| `schema` | Genau ein DataSchema. Modell, Modellversion und Modellhash müssen aufgelöst sein. |

CSV-Dialekt, geordnete Spalten und Typmapping liegen im versionierten technischen Vertragsartefakt aus TOPICS, identifiziert durch Key/Hash. **Nicht** dieselbe vollständige Liste unabhängig in YAML, PG und Java pflegen. `AttributeDefinition`/DataSchema bleiben fachlich; die technische Spaltenabbildung muss gegen sie und das kompilierte INTERLIS-Modell geprüft sein.

`enabled`/Definition/Schema ändern: `manage_metadata` nötig; bei veröffentlichtem Dataset zusätzlich `publish`. `automaticPublication` aktivieren/deaktivieren: `publish`. Jede Änderung erzeugt einen Auditvorgang und einen neuen Vertragsfingerprint; laufende Aufträge werden nicht still auf das neue Modell umgebogen.

### 2.3 DataVersion, DatasetIssue und Dataset

Die Hierarchie Dataset → Issue → Version → Distribution bleibt. Standalone-Datasets verwenden weiterhin ihre technische Standardausgabe. Das Lieferrecht ist **immer Dataset-weit**, keine Rechtefelder an Issue/Version/Distribution.

Für neu durch CSV angenommene Versionen gilt zwingend:

- `validationStatus=success`, passender `validationAt`, keine Fehler, Modell-/Vertragsbeleg.
- `acceptedAt` wird vom Server beim Commit vergeben, nicht aus dem Upload übernommen.
- `sourceSha256` ist der Hash der gelieferten Eingangsdatei; Snapshot-/Outputhashes sind davon unterschieden.
- `sourceReference = urn:di:submission:<uuid>` bindet die Provenienz. Keine beliebige Benutzereingabe als vertrauenswürdiger Ursprung.
- `objectCount`/`attributeCount` beziehen sich auf den **vollständigen** neuen Snapshot, nicht nur Appendzeilen.
- `currentVersion` wird erst im verbindlichen Fachcommit geändert. Versionsnummern werden serverseitig pro Ausgabe unter Sperre vergeben; keine `MAX+1`-Racebedingung.

Bereits vorhandene manuelle Versionen mit `unknown` werden nicht rückwirkend als validiert bezeichnet. Ihre unveränderte Existenz kann erhalten bleiben; nur neue CSV-Lieferungen unterliegen dem strengeren Annahmevertrag. Kein aktiver Web-/Workerpfad darf eine neue CSV mit `unknown` verfügbar machen.

## 3. Access: Fähigkeiten und Delegation

### 3.1 AuthorityAssignment

Enumeration erweitern um `submit_data` und `manage_submitters`; vorhandene Werte unverändert. `office XOR dataset` bleibt. Zuweisung an aktive User-/Group-/Service-Principals möglich; menschliche Uploads benötigen einen User-Principal.

Vorhandene zeitliche Gültigkeit weiterverwenden. Ergänzen, falls im Istmodell fehlend: `revocationReason` und eine optionale Beziehung `revokedBy` zu Principal. Entzug ist ein nachvollziehbarer Vorgang, kein DELETE. Zeit/Revoker/Reason müssen gemeinsam konsistent sein. Der technische Audittrigger bleibt zusätzlich aktiv.

### 3.2 Rechteumfang

| Aktion | Erforderliches fachliches Recht |
|---|---|
| Datensätze für die Lieferung auflisten | `submit_data`, aktueller aktiver User/Gruppe, gültige Konfiguration. |
| Lieferung anlegen, versiegeln, bewusst neu versuchen | `submit_data` auf diesem Dataset oder dessen OwnerOffice. |
| Für einen anderen Principal `submit_data` erteilen/entziehen | `manage_submitters` im vollständig passenden Scope. |
| `manage_submitters` erstmals vergeben | Nur expliziter privilegierter Bootstrap; nicht automatisch von Lieferantenmanager delegierbar. |
| Dataset-Metadaten, Modell/Vertrag oder Ausgabe ändern | Bestehende `manage_metadata`-/`publish`-Regeln. |
| `open/restricted` ändern | Bestehender fachlicher Publikations-/Zugriffsvertrag; `submit_data` genügt nicht. |
| Geschützte Daten lesen | `AccessGrant.read_data`; Lieferrecht ist kein zusätzlicher Lesepfad. |
| Eigene Lieferung und bereinigten Prüfbericht sehen | Aktiver ursprünglicher Lieferant; auch nach Lieferrechtsentzug, solange Principal aktiv. Keine Rohdateien anderer Personen. |
| Lieferungen des betreuten Bereichs sehen | `manage_submitters` des jeweiligen Scope. |
| Rohe Jenkinskonsole/Workspace/gesamte Buildartefakte sehen | Nur Plattformoperator, nicht aus fachlichem Lieferrecht abgeleitet. |

Ein Office-Grant umfasst **alle** zugehörigen Datasets, auch neu hinzukommende. Die UI muss dies nennen. Keine negativen Einzelgrants erfinden; Teilmengen werden mit Dataset-Zuweisungen abgebildet. OwnerOffice-Wechsel ändert die dynamische Scopeprüfung und wird auditiert.

Gleicher Benutzername/E-Mail reicht nicht. `(issuer, subject)` ist die stabile Identitätsreferenz. Gruppenzugehörigkeiten bleiben in PG; eine Keycloak-Gruppe darf nicht ungeprüft zu einer Authority werden.

### 3.3 Konkrete Serviceverträge in ADMIN

Package vorzugsweise `ch.so.agi.dateninfrastruktur.admin.ingestion` bzw. vorhandenes `access`.

| Typ / Methode | Verantwortung und Fehler |
|---|---|
| `SubmissionAuthorizationService.listEligible(ActorContext, PageRequest)` | Parametrisierte aktuelle PG-Abfrage; nur lieferfähige Datensätze, keine Leerlisten als Fallback bei DBfehler. |
| `SubmissionAuthorizationService.requireSubmit(ObjectContext, actor, datasetId, issueId)` | Aktiver Principal, Zugehörigkeit Issue→Dataset, gültiger Grant direkt/Gruppe/Office, Dataset/Ausgabe/Konfiguration zulässig; sonst 403/409. |
| `SubmitterAdministrationService.grant(actor, command, scope, beneficiary, validity, reason)` | `manage_submitters` prüfen, Scope nicht erweitern, nur `submit_data` vergeben, zugehörige Authority und Audit atomar. |
| `SubmitterAdministrationService.revoke(actor, command, assignmentId, reason)` | Entzug idempotent über CommandReceipt, kein Löschen der alten Authority. |
| `DeliveryConfigurationService.update(actor, command, datasetId, expectedVersion, dto)` | Bestehenden AggregateWriteGuard verwenden; technische Definition muss registriert/geprüft sein; automatische Publikation nur mit `publish`. |
| `DeliveryConfigurationQuery.resolve(datasetId)` | Liefert bindendes Konfigsnapshot mit Hash; kein beliebiger Skriptpfad. |
| `SubmitterController` | JTE/HTMX unter `/management/.../submitters`; CSRF/Originprüfung, erwartete Revision, keine direkte Tabellen-API. |
| `CsvDeliveryConfigurationController` | Kleine Einrichtung für bestehende Datasets; kein allgemeiner Modeler. |
| `DeliveryAuthorityBootstrapCommand` | Explizite Office-/Dataset-/Subjectreferenzen, technische Operatoridentität, idempotente einmalige Ersteinrichtung; niemals im Normalstart. |

`AuthorityService.describe/requireAny` und Management-VMs müssen neue Fähigkeiten korrekt differenzieren. Eine neue Capability darf nicht allein durch ein generisches „hat irgendeine Authority“ Zugang zu allen Verwaltungsaktionen eröffnen.

## 4. Fachliche Provenienz und technische Submission

Die bestehende generische `audit.row_change` bleibt für alle neuen/angepassten **Fachtabellen** aktiv. Metaattribute werden weiterhin ausserhalb ili2db interpretiert. Neue Tabellen müssen in der tatsächlichen Coverage erscheinen; nicht bloss Annotationen hinzufügen.

`CatalogAction` erhält bei Bedarf `accept_delivery` und optional `initiator` (Principal) als ausdrückliche Herkunft. `actor` ist die tatsächliche technische ausführende Serviceidentität; `initiator` die bei Annahme verifizierte Person. Bestehende Actorsnapshots/Entscheide werden nicht überschrieben. Das Label „im Auftrag von“ darf nur aus der gespeicherten Submission kommen, nie aus einem Workerpayload.

Die fachliche Aktion bindet Dataset, angenommene Version und Submission-UUID/Command-ID. `di_ingest.submission` enthält die Prozessprovenienz, `di_ingest.event` nachvollziehbare Zustandswechsel. Hochfrequente Heartbeats sind kein fachlicher Auditvorgang; ihre Änderung braucht keine riesigen JSONB-Vollbilder. Inhaltliche Entscheidungen, Retries, Entzüge, Commit und Fehlerstatus dagegen schon.

Keine Tokens, Passwörter oder CSVbytes in Audit-JSON. Fachlich nötige Gründe geschützt speichern; öffentliche Views enthalten sie nicht.

## 5. Transaktion und konkurrierender Rechteentzug

Die Schlussprüfung darf nicht aus einem minutenalten ObjectContext kommen. Vor Fachcommit eine frische PG-Sicht verwenden. Der vorhandene Connection-/Actorvertrag bleibt: `AuditedUnitOfWork`, `set_config(..., true)` und Cayenne-Flush auf derselben tatsächlichen Transaktionsconnection.

Für den kleinen Single-Instance-MVP ist ein **kleiner gemeinsamer Autorisierungs-Schreibschutz** zulässig: eine Guardrow in `di_ops`, Finalisierung hält `FOR SHARE`; jede Änderung, die Lieferberechtigung beeinflusst (Authority, Membership, Principal.active, OwnerOffice), hält `FOR UPDATE`. Reihenfolge immer Guard → Dataset → Submission/Execution. Keine externe I/O unter diesen Locks.

Damit gilt: Ein vollständig committeter Entzug vor Beginn der finalen Rechteprüfung blockiert die Veröffentlichung. Hat der Fachcommit den Guard bereits, wird er vor dem nachfolgenden Entzug linearisiert; das ist kein rückwirkender Widerruf eines bereits angenommenen Datenstandes. Prüfzeitpunkt und Autorisierungsrevision dokumentieren. Alternativer gleichwertiger Mechanismus nur mit reproduzierbarem Konkurrenztest, nicht mit einem Kommentar „nochmals prüfen“.

## 6. Schemaevolution statt Datenbankreset

1. Neue ILI-Modelle kompilieren und positive/negative Fixtures validieren.
2. In einer **isolierten frischen Referenzdatenbank** mit gepinntem ili2pg und identischem Mappingprofil das Ziel erzeugen.
3. Physische Namen/Typen/FKs/Checks/Metadaten vergleichen. `kind→akind`, UUID-/Datetime-Abbildung und eingebettete Assoziationen nicht erraten.
4. Eine explizite Migration für den bekannten Ausgangsfingerprint ableiten. Kein `--schemaimport` in ein befülltes Fachschema, kein `DROP SCHEMA CASCADE` zur Bequemlichkeit.
5. Entfernte Felder nach Konsistenzprüfung löschen; neue Tabellen und Enumchecks/Views/Funktionen/Triggers aktualisieren. Bestehende UUIDs, technische IDs und Sequenzfortschritt erhalten.
6. ili2db-Modell-/Klassen-/Attributmetadaten kontrolliert dem neuen Modellstand anpassen; keine blinde Übernahme instanzabhängiger Basket-/Importtabellen. Neuer SQLstand muss mit XTF-Export/erneuter Validierung zusammenpassen.
7. Cayenne `cdbimport/cgen` explizit im Entwicklungsweg, M3-UUIDnormalisierung und bestehenden PK-Generator erhalten. Keine Runtime-DDL. DataMap-/Fingerprintdatei gemeinsam aktualisieren.
8. Auditinstaller, Redaction, AggregateRevision und Publicviews neu verifizieren. Unbekannter Quellstand stoppt; kein „best effort“ mit fehlenden Constraints.
9. Upgrade einer nichtleeren Testdatenbank mit bestehenden Grants/Decisions/Audit/Distributionen tatsächlich ausführen. Vorher/nachher fachliche IDs und unveränderte historische Auditzeilen vergleichen.

Eine kurze lokale Schutzkopie für die irreversible Schemaoperation ist erlaubt; daraus entsteht kein Auftrag für regelmässigen Backupbetrieb.

## 7. Technische Tabellenrechte

`di_ingest` wird durch explizite SQLmigrationen verwaltet, nicht durch einen zweiten unmodellierten Fachrechtebestand. Die dortigen FK-/UUID-Bezüge verbinden sich mit den tatsächlich gemappten Fachobjekten. Administratoren können keine SQL-Datensätze per Browser direkt schreiben. Der Worker erhält HTTP-Zugriff, **keinen PG-Writerlogin**.

ADMIN erhält für Ingestion den eng benötigten DB-Zugriff. `di_public` bleibt bei Publicviews, `di_authz` bei lesender Downloadautorisierung. Historische Query-/Audit-Endpunkte dürfen Submission-Begründungen nicht aus Versehen öffentlich projizieren. Die automatische Lieferung benutzt nicht den globalen Migrationsowner.

## 8. Erstkontakt einer Identität und unveränderliche Schemabezüge

`IdentityProvisioningService.ensureUser(VerifiedIdentity)` darf beim ersten **kryptografisch verifizierten** Kontakt eine minimale User-Principalreferenz anlegen. Unique `(issuer,subject)`, ursprüngliches `provisionedAt`, kein Passwort und **keine** automatische Capability oder AccessGrant. Eine vorhandene inaktive Person darf durch erneutes Login niemals wieder aktiviert werden. Userclaims dürfen keine bestehenden fachlichen Authorities oder lokalen Gruppen überschreiben.

Für den MVP wählt die Lieferantenverwaltung aus den bereits bekannten aktiven Principals/Gruppen. Neue Personen können sich einmal anmelden oder durch einen ausdrücklich administrativen Vorgang mit belegtem Issuer/Subject registriert werden. Keine neue AIO-/LDAP-Vollsynchro und keine Zuordnung allein über E-Mail. Service-Principals für Ingestion sind ausdrücklich provisioniert und an den vorgesehenen Client/Audience gebunden, nicht aus beliebigen Benutzerclaims abgeleitet.

Ein von angenommenen Versionen oder versiegelten Aufträgen referenzierter **struktureller DataSchema-Vertrag** darf nicht unter gleicher Identität umgedeutet werden. Neues Typschema/anderes Modellset → neuer DataSchema-Bezug und neuer Definitionhash. Beschreibende Korrekturen dürfen auditiert möglich bleiben; strukturelle Fingerprints/Historie bleiben unverändert. Eine neue DeliveryConfiguration kann auf die neue Struktur wechseln; bestehende Aufträge behalten ihren früheren gebundenen Vertrag und werden bei einer nicht mehr erlaubten Annahme mit CONFIGURATION_CHANGED zurückgewiesen.

Die Adminoberfläche zeigt vor Aktivierung der automatischen Publikation klar: künftige gültige Lieferungen bereits lieferberechtigter Personen werden ohne Einzelgenehmigung angenommen. Eine versteckte Defaultaktivierung ist verboten.
