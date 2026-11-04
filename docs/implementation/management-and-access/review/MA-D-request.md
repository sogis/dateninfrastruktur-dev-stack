# Reviewrequest MA-D

## Ausgangspunkt und gültiges Gate

- ADMIN base: `b3cd23e7ed1879a6bb6e7fff421248bcd9a4709c`
- STACK base: `4f75105dae2dbc8e370fd4fe734121be26d2c84a`
- PUBLIC base: `70aee2d74e31cc6a34253af8d8cc2478325ed98a`

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

Für dieses Delta aus ADMIN: `python3 scripts/test_catalog_all.py --delta`.
Der vollständige ursprüngliche MA-D-Lauf wurde vom unabhängigen Reviewer selbst erfolgreich ausgeführt; siehe MA-D-review-01.md. Der normale STACK-Dispatcher bleibt als vollständige Suite verfügbar, ist für dieses begrenzte Delta nicht erforderlich.
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

## Nacharbeit nach Review 01: MA-D-REV-01 und MA-D-REV-02

Das erste Review war NACHARBEIT; keine MA-E-Implementierung wurde begonnen.

MA-D-REV-01: Der DB-HTTPcontroller übernimmt page/size vor der absichtlich
unpaginierten Legacy-Normalisierung. Die Repositoryantwort trägt das tatsächlich
verwendete, bei Überlauf auf die letzte Seite begrenzte Fenster. Ergebnisse
enthalten Vor-/Zurück-Links; Filter, Suchtext, Sortierung und Seitengrösse bleiben
in diesen Links und beim Aufklappen einer Serie erhalten. Legacykonstruktoren
bleiben kompatibel. Der neue echte HTTP-/Chromium-Reproducer legt 13 veröffentlichte
Roots an: Seite1 zeigt10, Weiter3, die Vereinigung enthält alle13 ohne Duplikate;
page2/size1 zeigt exakt den zweiten, page999/size1 den letzten Eintrag.

MA-D-REV-02: Der Import iteriert ThemeAssignment-BAGs, dedupliziert Themes sowie
identische Creator-/Kontaktstrukturen. Mehrere verschiedene Creator/Kontakte
werden als datensatzbezogene strukturierte Konflikte berichtet, ohne Abbruch
des gesamten Dry-runs und ohne first-wins. Zusätzliche Vorprüfung verhindert
mehrdeutige/mehrfach zugeordnete Distribution-IDs. Eine echte temporäre XTF mit
mehreren ThemeAssignment-Kindern im selben Wrapper wird gelesen und angewendet;
identische Creator/Kontakte werden übernommen, verschiedene verweigert.

Delta-Auswahl: neuer BAG-Reproducer und LegacyCatalogImportIT; echte 13-Root-
HTTP-/Browserprobe sowie JdbcCatalogRepositoryIT, PublicCatalogRoleIT,
DatabaseCatalogModeIT und CatalogDisclosureIT; kleine VM-/URL-/MVC-Regression.
Damit laufen M21–M25 neu mit den betroffenen Verträgen. Unverändert übertragbar
sind die zuvor vom Reviewer selbst ausgeführten OIDC-, Transaktions-,
Startup-, Operator-CLI- und B→C→D/C→D-Upgradenachweise: kein Schema-,
Migrations-, ORM-, Authz-, Credential-, CSRF- oder Dependencywechsel im Delta.
Der Reviewer muss beide Reproducer und eine eigene gezielte Gegenprobe selbst
ausführen. Ein früherer erfolgreicher Test ist keine Abnahme des ersten Kandidaten.

Lokales Ergebnis vor neuem Review: `python3 scripts/test_catalog_all.py --delta` vollständig erfolgreich; setup, Legacy-BAG, Fixture, vier Public-DB-Integrationsklassen und drei VM-/URL-/MVC-Klassen exit0, keine Skips. Rohlog ADMIN/.runtime/catalog-d-delta.log.
