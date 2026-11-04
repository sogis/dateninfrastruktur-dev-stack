# Reviewrequest MA-D

## Ausgangspunkt und gültiges Gate

- ADMIN base: `abc26cc5d45a93e7f27b4d6f413720ff0f7fec3c`
- STACK base: `6f19623465086909213c15895022e6e486770b1e`
- PUBLIC base: `8349be8aba4036ca0bb56e89cb62398e34404a5e`

MA-C ist unabhängig ABGENOMMEN am exakten Kandidaten20261104T162930Z; gebundene
Rohbelege und MA-C-accepted.md bleiben erhalten. Keine MA-E-Produktarbeit vor
dieser Abnahme. Fremde historische STACK-Nachweise bleiben unberührt/unversioniert.

## Änderungen und Zielerreichung

PUBLIC erhält expliziten database-Modus mit eigener di_public-DataSource,
JdbcCatalogRepository/CatalogQueryService und unveränderten Darstellungstypen/
VM-Factories. Keine leere Snapshotattrappe: Legacyimport-/Reload-/Snapshot-/
Explorekomponenten existieren im DB-Modus nicht. Kein XTF/current.json/DuckDB/
Jenkins-Bootstrap und kein Fehlerfallback. Boot von4.1.0 auf exakt4.1.2 passend
zum bereits geprüften Java25-/Boot-BOM-Vertrag; JDBC/PG-Treiber über diese BOM.

Alle SQL-Reads ausschliesslich auf api_public-Views, readonly-Konto, kurzlebige
Repeatable-Read-Transaktion für Ergebnisse/Facetten. Parametrisierte literale
AND-Begriffe in Titel/Beschreibung/Keywords; bewusst keine Luceneoperatoren im
DB-Modus, dokumentiert. Filter/Sortierung/begrenzte Pagination mit Identifier-
Tie-Breaker. Bestehende JTE/HTMX-Ansichten, sichere Markdownausgabe und gemeinsame
unveränderte Themenlabels bleiben erhalten. Nur Rootdatensätze als Top-Level,
Defaultissue intern. Serien ohne publizierte Ausgabe bleiben ohne erfundene
Ausgabe darstellbar. Attribute/Schema und zusätzliche echte Ausgabenerläuterung.

DB-Readiness statt Snapshotwahrheit; Ausfall503 bei lebender JVM. Alte komplette
Katalogartefakte und Explorekontexte im DB-Modus410, Links entfernt. Publickonto
hat keinen Zugriff auf Mutation, reale Fach-/Grant-/Audit-/Storage-/Herkunfts-
Basistabellen. Antragslink mit Root-Dataset-UUID und Meine Zugänge zeigen zu
/access. Echte Portal→APISIX→Keycloak→Admin-Navigation zusätzlich geprüft.

ADMIN: Java-Legacyimport mit wirklichem vollständigem Dry-run der verfügbaren
62-Root-Datei und echtem ausgewähltem Standalone-/Serienapply aus der vorhandenen
konfliktfreien Beispieldatei. Quellen/Modellpfad/Hashes in docs/legacy-import.md.
Konfliktbericht statt first-wins: tatsächliche Kontakt-/Office-/Quellabweichungen
werden nicht angewendet. Bekannte Altzugänge nur open→open, übrige restricted mit
Warnung; unbekannt stoppt. Identifier/UUID-/Herkunftszuordnung dauerhaft, identische
Offices/Schemadefinitionen normalisiert, Attribute erhalten. Kein Copy-Paste-
Roottext als Fake-Issue-Note. Legitime Ausgabenerläuterungen erhalten. Ursprüngliche
XML-Herkunft zusätzlich technisch geschützt aufbewahrt, nicht öffentlich.

Fehlende Liefer-/Prüfwerte bleiben unbekannt; Legacyversionen/-dateien prepared.
Alte URL nur Referenz, keine verfügbare Altdatei, kein produktiver S3-Write oder
neuer Lader. Auswahl-Apply samt Herkunft/Actor-Audit/Receipt atomar und idempotent;
spätere Adminbeschreibung wird nicht überschrieben. V008 nur technische Herkunft,
keine handgeschriebene alternative Fachtabelle. Gepinnte explizite B→C→D-/C→D-
Upgrades über bekannte Vorgänger und unveränderte alte Modell-/Mapping-/
Migrationshashes, bei unbekanntem DBzustand Abbruch vor DDL/Artefaktwrite.

MA-C-REV-01/02 gezielt korrigiert: OIDC-Sessioncookie muss positiv existieren;
Malformed-until führt tatsächlich zu400 statt503. Standard-CSRF, JWT-/Authz-SQL,
Fachmodelle, Rechteanker und Transaktionsgrundvertrag bleiben unverändert.
Operator-Logging unterdrückt SQLbindings auch ohne Springstart. Testharness
reicht nur explizite eigene Runtime-ENVkeys in Container weiter; keine Original-
.env/globalen Appcredentials. Playwright-GC explizit aus.

## Selbst auszuführendes Reviewkommando

Aus STACK: `./scripts/management/test.sh --phase MA-D`.
Aus ADMIN: `python3 scripts/test_catalog_all.py`.
Freier eigener Runtimebereich erforderlich; kein implizites Ersetzen bestehender
eigener oder fremder Daten. Neue gelabelte PG/Keycloak/APISIX/JVM-Ressourcen,
eigene Ports/Volumes/Schreibpfade, Schutz-/Cleanupprüfungen. Reviewer bekommt
isolierte Geschwistercheckouts ohne private Originaldateien. Schrittlogs und
gesicherte tatsächliche JUnit-XML unter ADMIN/.runtime/catalog-d-evidence/.

| ID | Neu ausgeführter Nachweis |
|---|---|
| M21 | JdbcCatalogRepositoryIT: echte öffentliche Views, literal gebundene Suche/Filter/Sort/Pagination; Einzelangebot/Serie/Ausgaben/current; Schema/Attributmapping; zusätzlich veröffentlichte Serie ohne öffentliche Ausgabe, Current404; vorhandene MVC-/VM-/Parserregressionen |
| M22 | DatabaseCatalogModeIT: zwei echte unabhängige Spring/JVM-Webcontexts mit nicht existierender XTF-Datei/unbrauchbarer Manifest-URL; keine Snapshot-/CatalogInputsSource-Beans; tatsächlicher Cayenne-Adminservicecommit erscheint auf neuem HTTPrequest beider Instanzen ohne Reload; gezielter echter DBverbindungsentzug führt503, Liveness200, kein Fallback |
| M23 | LegacyCatalogImportIT plus wirkliche Java-CLI: vollständiger62-Root-Dry-run ohne Fach-/Auditwrites, reale repräsentative Migration, Konfliktverweigerung, unbekannter Zugangscode, Attribute/Beziehungen/prepared-Status, UUID-/Receipt-Replay und gleicher Schlüssel mit anderer Auswahl verweigert, spätere Adminänderung erhalten |
| M24 | PublicCatalogRoleIT: echte positive Viewabfrage, danach reale Fach-/Grant-/Audit-/Objectkey-/Legacyherkunfts-Selects und Mutation/Create verweigert; explizit fehlendes View-Updaterecht, keine Schreibrechte nur aus Pool-readonly behauptet |
| M25 | CatalogDisclosureIT: echte HTTP-/Chromiumdetailseiten, Drafts/hidden Issues404, alte Artefakte/Explore410, sichere MTEXTdarstellung, Root-Antragslinks; PortalNavigationIT klickt tatsächlichen Gateway-Portal-Link durch echten OIDC-Codeflow zum richtigen Adminformular |

Zusätzlich frische AuditedUnitOfWorkIT/ManagementStartupIT und bekannte B→C→D-/
C→D-Migrationsproben über nichtleere UUID-/Auditdaten; echter CLI-Dry-run/Apply;
OidcLoginIT/ManagementHttpSecurityIT mit Cookieexistenz und Malformed-until400.
Kein JUnitcache/UP-TO-DATE für externe DBtests, fehlende/skippte Pflichtklassen
stoppen den Harness. Eigene Gegenprobe durch Reviewer ist weiterhin Pflicht.

## Delta und übernommene Belege

Ein zusammenhängender frischer MA-D-Lauf ist erfolgreich (catalog-d-final.log).
Anschliessend wurden nur der zusätzliche Empty-Series-Fixturefall und gemeinsame
Themenlabelwiederverwendung ergänzt: gezielt JdbcCatalogRepositoryIT+
CatalogDisclosureIT sowie XtfPublishedCatalogParserTest+ResultsVmFactoryTest
neu erfolgreich. Der versionierte Phasenrunner führt diese Fälle zusammen mit
allen M21–M25 erneut aus. Kein Schema-/Authzwechsel durch diesen UI-/Fixturedelta.

Ein zunächst instabiler Fixtureflush ist reproduziert und korrigiert: vollständiges
Schema/Attribute werden vor erster acceptedVersion innerhalb derselben äusseren
Transaktion geflusht. Der reale DB-Immutabilitätsschutz bleibt unverändert und
verweigert zu späte Attributinserts. Kein Abschwächen des Test-/DBvertrags.

Unveränderte MA-A-Modelle und ili2pg-/Cayenne-Mappinggrundvertrag sowie MA-C-
JWT/CSRF/Authorization-SQL bleiben am akzeptierten Kandidaten gebunden. Betroffene
Startup-/UOW-/Upgrade-/UI-/C-MINOR-Verträge frisch geprüft; kein erneuter grosser
unveränderter WebR-/Superset-/ClickHouse-/Foundationlauf. Keine Native-/Produktions-
oder Rechtszertifizierungszusage. Origin/privateS3/forward-auth-Dateikette,
Mehrinstanzen-Downloads und HTTPRange folgen erst MA-E. Portal hat keine
Schreibrechte und keine persönliche SQL-/Superset-Rechteprojektion.

Abschliessender Sicherheitsdelta: Web/Operator verwenden dieselbe extrahierte
RuntimeContractVerifier-Prüfung. ManagementStartupIT läuft neu erfolgreich;
der tatsächliche Java-Apply mit deaktiviertem Audittrigger wird vor jeder
Fach-/Herkunfts-/Receiptmutation verweigert (test_operator_contract.py), nach
Wiederherstellung wird ein echter ausgewählter CLI-Apply positiv geprüft.
Keine Änderung an Fach-/JWT-/Authzlogik; der Phasenrunner enthält die Gegenprobe.
