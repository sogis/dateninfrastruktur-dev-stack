# Review MA-D / 20261104T175614Z

## Urteil

**NACHARBEIT**

Die neue PostgreSQL-Leseschicht, die öffentlichen Views, die Publicrollen-Grenze, der Zwei-Instanzen-/Ausfallpfad und der Legacyimport laufen im frischen Phasenlauf technisch. Zwei konkrete Ziel-/Vertragsverletzungen bleiben aber offen: die öffentliche Trefferliste im DB-Modus schneidet nach 10 Zeilen ab, ohne Pagination-Steuerung (MA-D-REV-01); der Legacyimport bricht bei einer modellgültigen BAG-Kodierung mit mehreren `ThemeAssignment` in einem `<themes>`-Wrapper als unbehandelte Exception ab, statt zu importieren oder einen Konfliktbericht zu schreiben (MA-D-REV-02). Beide sind reproduziert; keine Produktdatei wurde verändert.

## Bindung

- Handoff-SHA256: `083d481cdd75dba1fa056cca9ee7de49f9e7923a4d0f61266c1024ac865f0fb9`
- Spezifikationsaggregat: `fb7399c4ebf1342edf0dc704220b92202eba865a63d2b15031fb6556e574c613` (aus dem absoluten Dateimap der 12 Dateien nachgerechnet: OK); alle 12 Einzeldateihashes des Handoffs selbst nachgerechnet: OK. Request-SHA256: `399b78ce3ce92687233e6145174462013e6d8b3ac1f14a30e0d12fa2fdced005`; Workspace-AGENTS: `02e456b5a6b0b37d2fdd87314304926f77f6b675aa01cfd7ed366544aae0f091`.
- Repositories/HEADs (selbst geprüft, Working Trees sauber):
  - `dateninfrastruktur-dev-stack` @ `4f75105dae2dbc8e370fd4fe734121be26d2c84a` (base `6f19623465086909213c15895022e6e486770b1e`)
  - `dateninfrastruktur-admin` @ `b3cd23e7ed1879a6bb6e7fff421248bcd9a4709c` (base `abc26cc5d45a93e7f27b4d6f413720ff0f7fec3c`)
  - `dateninfrastruktur-sodata` @ `70aee2d74e31cc6a34253af8d8cc2478325ed98a` (base `8349be8aba4036ca0bb56e89cb62398e34404a5e`)
- Reviewer: `deepseek/deepseek-flash`, `opencode v2.2.5` (tatsächlich laufender Prozess: `.../ai.opencode.desktop/cli/2.2.5-arm64/opencode-cli run --standalone --agent management-review --model deepseek/deepseek-flash`; das ältere `opencode` auf dem PATH ist 1.18.22 und wurde nicht verwendet). Session: `ses_e584ba97dffeANcvGTWk18ucLx`.
- Isolation: eigener Geschwister-Checkout unter `.runtime/management-review/MA-D/20261104T175614Z/workspace`; eigener PostgreSQL-16/PostGIS-Container `di-ma-b-*` mit zufälligem Loopback-Port, eigener Keycloak-/APISIX-/JVM-/Portal-Stack aus `identity_runtime.py`; alle eigenen Container/Netzwerke nach dem Lauf entfernt. Keine Original-`.env`, keine Nutzerdienste, kein `docker system prune`, kein `down -v`.

## Code und Zielerreichung

Gelesen wurden der vollständige EXECUTION_PLAN, SPEC_MODELS, SPEC_PERSISTENCE_AUDIT, SPEC_APPLICATIONS_GATEWAY, TEST_PLAN, OPENCODE_REVIEW_PROMPT, CODEX_STARTPROMPT, SOURCES, AGENTS_ERGAENZUNG, Workspace- und Repo-AGENTS sowie die Diffs `base..head` in allen drei Repositories.

Geprüfte Verträge:

- **PUBLIC DB-Modus**: `DatabaseCatalogConfiguration` (explizite `database`-Quelle, eigene `di_public`-Hikari-DataSource, Readiness-/Startgate ohne XTF), `SnapshotMode`/`SnapshotModeCondition` (Legacyimport-, Reload-, Snapshot-, Explore- und DuckDB-Komponenten im DB-Modus ausgeschlossen), `JdbcCatalogRepository` (nur `api_public`-Views, kurze Repeatable-Read-Transaktion, parametrisierte literale AND-Suche, Filter/Sortierung/Pagination, Identifier-Tie-Breaker), `CatalogQueryService`, `DatabaseCatalogController` (Suche/Detail/Serie/Ausgabe/current, 410 für alte Artefakte/Explore, `/access`-Links), `CatalogReadinessHealthIndicator`, `CatalogErrorControllerAdvice`, application.yml, JTE-Anpassungen. Die V003-Viewdefinitionen wurden gegen die tatsächlich gelesenen Spalten (datasets/issues/versions/distributions/offices/themes/keywords/schemas/attributes) geprüft; Drafts/hidden Issues/Storage-/Grant-/Auditdaten sind nicht Bestandteil der Views.
- **ADMIN Legacyimport**: `LegacyCatalog` (namespace-aware, DTD/externe Entities aus, Datei-/Objekt-Hash, stabile UUIDs, kanonisches XML), `LegacyCatalogImportService` (Dry-run/Apply, Konflikte statt first-wins, Office-/Schema-Normalisierung, prepared-Versionen, keine erfundenen Bytes, Herkunft `di_ops.legacy_origin`, Receipt/Idempotenz, spätere Adminänderung bleibt), `LegacyCatalogImportCommand`, V008, `upgrade_contract.py`/`upgrade-MA-C-to-MA-D.json`, `RuntimeContractVerifier`, `ManagementConfiguration`, `logback.xml`, Test-/Runtime-Harness.
- **MA-C-Minors**: OIDC-Sessioncookie wird positiv auf Existenz geprüft (`OidcLoginIT`); ein ungültiges `until`-Datum führt über `DateTimeException` tatsächlich zu 400 (`ManagementHttpSecurityIT`); CSRF/JWT/Authz-Verträge unverändert.
- **STACK**: `scripts/management/test.sh --phase MA-D` ruft den versionierten Phasenrunner auf; der Request/Work-Queue-Delta ist konsistent.

Zielerreichung: Der Kern (Sodata liest PG-Views ohne XTF/DuckDB/Jenkins, DB-Ausfall 503 ohne Fallback, zweite Instanz sieht Admincommit, Publicrolle nur Views, Legacy-Dry-run/Apply/Replay, B→C→D/C→D-Upgrade) ist technisch belegt. **Nicht vollständig erreicht** sind die öffentliche Vollständigkeit der Trefferliste (REV-01) und die robuste/korrekte Verarbeitung der modellgültigen Legacy-BAG-Kodierung (REV-02). Deshalb `goal_reached: false`.

## Selbst ausgeführte Tests

Ausgangskommando (ADMIN, CWD `/.../workspace/dateninfrastruktur-admin`): `python3 scripts/test_catalog_all.py` → Exit 0; alle Schritte `setup`, `transaction-startup-regression`, `B-C-D-upgrade`, `C-D-upgrade`, `M23-legacy`, `legacy-cli-dry`, `legacy-cli-apply`, `operator-contract`, `portal-fixture`, `M21-M22-M24-M25`, `portal-MVC-regression`, `portal-bootJar`, `admin-bootJar`, `identity-start`, `MA-C-review-minors` = 0, `identity-stop` = 0, danach `Removed only own MA-B container and own anonymous volumes`. Beleg: `output/evidence/phase-runner.stdout.log`, `...stderr.log` (leer).

| ID | Kommando / CWD | Erwartet | Beobachtet | Beleg |
|---|---|---|---|---|
| M21 | `python3 scripts/test_database_services.py '*JdbcCatalogRepositoryIT' '*PublicCatalogRoleIT' '*DatabaseCatalogModeIT' '*CatalogDisclosureIT'` in `.../workspace/dateninfrastruktur-sodata` (durch den Phasenrunner gestartet) | Exit 0, kein Skip/Fehler | Exit 0; `JdbcCatalogRepositoryIT` tests=1 failures=0 errors=0 skipped=0; echte Views, Suche/Filter/Sort/Pagination, Standalone/Serie/Ausgaben/current, Schema/Attribute, Draft-Ausschluss, Literalssuche | `output/evidence/catalog-d-evidence/M21-M22-M24-M25/TEST-ch.so.agi.datenportal.catalog.database.JdbcCatalogRepositoryIT.xml` |
| M22 | wie M21 (gleicher Gradle-Lauf) | Exit 0 | Exit 0; `DatabaseCatalogModeIT` tests=1; zwei unabhängige Spring-Webkontexte, keine `CatalogService`-/`CatalogInputsSource`-Beans, echter Admin-Cayenne-Commit auf beiden Instanzen sichtbar, `di_public`-Loginentzug → 503 Readiness/Detail, Liveness 200, kein XTF/Manifest-Zugriff | `.../M21-M22-M24-M25/TEST-ch.so.agi.datenportal.catalog.database.DatabaseCatalogModeIT.xml` |
| M23 | `python3 scripts/test_management_services.py '*LegacyCatalogImportIT'` in `.../workspace/dateninfrastruktur-admin` (durch den Phasenrunner gestartet) | Exit 0 | Exit 0; tests=1; 62-Root-Dry-run, Konfliktbericht, repräsentativer Apply (2 Roots), UUID-/Receipt-Replay, andere Auswahl mit gleichem Schlüssel verweigert, spätere Adminbeschreibung erhalten, unbekannter Zugangscode als Konflikt, prepared-Distributionen ohne Bytes/Hash | `output/evidence/catalog-d-evidence/M23-legacy/TEST-ch.so.agi.dateninfrastruktur.admin.LegacyCatalogImportIT.xml` |
| M24 | wie M21 | Exit 0 | Exit 0; `PublicCatalogRoleIT` tests=1; positive Viewabfrage, `UPDATE`-/`CREATE`- und reale Fach-/Grant-/Audit-/Objectkey-/Legacyherkunfts-Selects mit SQLSTATE 42501 verweigert | `.../M21-M22-M24-M25/TEST-ch.so.agi.datenportal.catalog.database.PublicCatalogRoleIT.xml` |
| M25 | wie M21 | Exit 0 | Exit 0; `CatalogDisclosureIT` tests=1; echte HTTP-/Chromium-Detailseiten, Drafts/hidden Issues 404, alte Artefakte/Explore 410, kein `DRAFT_ONLY_SECRET`/`storageProfile`/`objectkey`, kein Inline-Script aus MTEXT, Antragslink mit Root-UUID, `/access/me` | `.../M21-M22-M24-M25/TEST-ch.so.agi.datenportal.catalog.database.CatalogDisclosureIT.xml` |

Zusätzlich im selben Lauf erfolgreich: `AuditedUnitOfWorkIT` (1), `ManagementStartupIT` (2), `DatabaseCatalogFixtureIT` (1), `LegacyCatalogImportIT` (1), `OidcLoginIT` (1), `ManagementHttpSecurityIT` (1), `PortalNavigationIT` (1), Legacy-CLI-Dry-run und ausgewählter CLI-Apply, Operator-Contract-Negativprobe (deaktivierter Audittrigger), B→C→D-/C→D-Upgrade, Portal-MVC-/VM-/Parser-Regressionen (u. a. `CatalogControllerMvcTest` 27, `CatalogDetailControllerMvcTest` 24, `DetailPageVmFactoryTest` 27, `XtfPublishedCatalogParserTest` 22), jeweils ohne Skips/Fehler. Die JUnit-XMLs liegen unter `output/evidence/catalog-d-evidence/`.

## Übernommene Nachweise

Keine. M21–M25 wurden in diesem Review frisch ausgeführt; es wird kein alter PASS als Ersatz verwendet. Die bereits abgenommenen MA-A-/MA-B-/MA-C-Grundverträge wurden nicht vollständig wiederholt; der Phasenrunner prüft die im MA-D-Request genannten betroffenen Startup-/UOW-/Upgrade-/UI-/C-Minor-Verträge.

## Eigene Gegenprobe

**Formale Gegenprobe (REV-02, Legacy-BAG):**

- Hypothese: Ein modellgültiger Legacy-`PublishedCatalog` mit zwei `ThemeAssignment`-Einträgen in **einem** `<themes>`-BAG-Wrapper (kanonische BAG-Kodierung; `themes : BAG {1..*} OF ThemeAssignment`) lässt sich trockendlaufen; beide Themen werden übernommen oder als strukturierter Konflikt gemeldet, nicht als unbehandelte Exception.
- Input: `output/counterexample/multi-theme.xtf` – Kopie von `published_catalog_examples_only.xtf`, im ersten `<themes>`-Wrapper um ein zweites vollständiges `<ThemeAssignment>` (`Geografie` + `themeUri`) ergänzt (beide Felder vorhanden, Modellwert gültig).
- Kommando/CWD: `python3 scripts/legacy_import.py ../../output/counterexample/multi-theme.xtf --report=../../output/counterexample/multi-theme-report.json` in `.../workspace/dateninfrastruktur-admin` (eigene isolierte DB).
- Erwartet: Exit 0 und ein Plan/Report mit beiden Themen (oder ein strukturierter Konflikt), kein ungefangener Fehler.
- Beobachtet: Exit 1; `org.apache.cayenne.CayenneRuntimeException` verursacht durch `java.lang.IllegalArgumentException: Ambiguous legacy scalar ThemeAssignment/localTheme` in `LegacyCatalog.at`/`LegacyCatalogImportService.themes`; kein Report geschrieben.
- Beleg: `output/counterexample/multi-theme.stdout.log` (Stacktrace), `multi-theme.stderr.log` (leer).

**Zweite ausgeführte Gegenprobe (REV-01, öffentliche Liste):**

- Hypothese: Der DB-Modus erhält die bestehende öffentliche Darstellung (alle veröffentlichten Roots, `page`/`size` ohne Wirkung wie im bestehenden MVC-Vertrag) auch bei mehr als 10 Einträgen.
- Input/Aufbau: isolierte Management-DB, `DatabaseCatalogFixtureIT` (3 veröffentlichte Roots), danach 10 zusätzliche veröffentlichte Standalone-Roots über dieselbe Fach-Engine (gültige Default-Ausgabe, `currentissue` gesetzt), insgesamt 13 öffentliche Roots; Portal-Jar aus `dateninfrastruktur-sodata` im `database`-Modus gegen diese DB.
- Kommando/CWD: `python3 ../../output/counterexample/portal_listing_probe.py` in `.../workspace/dateninfrastruktur-admin` (startet das Portal auf einem freien Loopback-Port, beendet es im `finally`).
- Erwartet: 13 gerenderte Zeilen (bzw. 13 über eine echte Pagination erreichbar), Seite und `page=2&size=1` konsistent.
- Beobachtet: `GET /` = 200, Anzeige „13 Einträge gefunden“, aber nur 10 `dp-entry-row`-Zeilen (8 Probe- + 2 Fixture-Identifiers); `GET /datasets?page=2&size=1` = 200, ebenfalls 10 Zeilen und derselbe erste Ausschnitt; keine Pagination-Steuerung.
- Beleg: `output/counterexample/portal_listing_probe.stdout.log`.

## Findings

### MA-D-REV-01 — MAJOR — Öffentliche Trefferliste im DB-Modus bricht nach 10 Einträgen ab

- Datei/Methode: `dateninfrastruktur-sodata/src/main/java/ch/so/agi/datenportal/catalog/database/CatalogQuery.java` (Konstruktor: `size = min(100, size>0 ? size : 10)`), `JdbcCatalogRepository.search` (LIMIT/OFFSET aus diesem Wert) und `DatabaseCatalogController.index` (übergibt `params.normalized().toSearchQuery()`, also `PageRequest.unpaged()`; `page`/`size` werden nicht durchgereicht; die Templates haben keine Pagination-Steuerung).
- Reproduzierbarer Fehler: 13 veröffentlichte Roots, `GET /` zeigt „13 Einträge gefunden“, rendert aber nur 10 Zeilen; `GET /datasets?page=2&size=1` ändert den Ausschnitt nicht. Bei den vorhandenen 62 Legacy-Roots wären 52 Einträge über das Portal nicht erreichbar.
- Verletzter Vertrag: TEST_PLAN M21 „Suche/Filter/Sortierung/Pagination“ und der MA-D-Request „Filter/Sortierung/begrenzte Pagination“; die bestehende öffentliche Darstellung listet alle sichtbaren Einträge (der bestehende MVC-Vertrag ignoriert `page`/`size`, aber ohne 10er-Abschneidung); die Doku `docs/database-catalog.md` behauptet „vorhandene … Pagination bleibt erhalten“.
- Minimal erforderliche Korrektur: Entweder den bestehenden Unpaged-Vertrag im DB-Modus erhalten (kein hartes 10er-Limit; sichere Obergrenze z. B. über `SearchProperties.maxPageSize`) **oder** `page`/`size` explizit an `CatalogQuery` durchreichen und eine echte Pagination-Navigation rendern; in beiden Fällen einen HTTP-Test mit >10 veröffentlichten Roots ergänzen, der die Anzahl gerenderter Einträge gegen `totalElements` prüft.

### MA-D-REV-02 — MAJOR — Legacyimport bricht bei modellgültiger BAG-Kodierung mit mehreren ThemeAssignments ab

- Datei/Methode: `dateninfrastruktur-admin/src/main/java/ch/so/agi/dateninfrastruktur/admin/legacy/LegacyCatalogImportService.java` `themes(Element root)` (Zeile 55: `text(e,"ThemeAssignment/localTheme")` pro `<themes>`-Wrapper) und `LegacyCatalog.at` (Zeile 24: wirft `Ambiguous legacy scalar`, sobald ein Pfadsegment mehr als ein Kind hat).
- Reproduzierbarer Fehler: Ein `<themes>`-Wrapper mit zwei vollständigen `<ThemeAssignment>`-Kindern (kanonische XTF-BAG-Kodierung, Modell `themes : BAG {1..*} OF ThemeAssignment`) führt im Dry-run zu Exit 1 und `IllegalArgumentException: Ambiguous legacy scalar ThemeAssignment/localTheme`; es wird kein Konfliktbericht geschrieben. Dieselbe Skalarannahme trifft auch `at(xml,"creator/Office")` für `creator : BAG {0..*} OF Office`.
- Verletzter Vertrag: MA-D verlangt die einmalige Legacyübernahme mit Erhalt der Themen/Attribute und einem Konfliktbericht statt first-wins; die verfügbare Fixture kodiert je Theme einen eigenen `<themes>`-Wrapper und deckt die kanonische BAG-Form nicht ab; ein modellgültiger Eingabefall darf nicht als unbehandelte Exception enden.
- Minimal erforderliche Korrektur: In `themes()` alle `ThemeAssignment`-Kinder je `<themes>`-Wrapper iterieren und je `localTheme` aufnehmen (Duplikate deduplizieren); für `creator`/weitere BAGs entweder alle Werte verarbeiten oder einen expliziten, strukturierten Konflikt erzeugen; eine Fixture mit mehreren Assignments in einem Wrapper (und Mehrfach-Creator) in `LegacyCatalogImportIT` ergänzen.

## Integrität und Grenzen

- Produktstand unverändert: Alle 1224 getrackten Dateien der drei Workspace-Repositories wurden gegen die Runner-`before.json` geprüft (122 + 169 + 933), **0 Hash-Abweichungen**; `git status --porcelain` in allen drei Checkouts leer. Beleg: `output/product-integrity.json`, Runner-Ausgangssnapshot `before.json`. Die Original-Repositories ausserhalb des Workspace wurden nur gelesen; keine Nutzeränderungen, keine fremden Dienste, keine Secrets in Logs/Berichten.
- Eigene Ressourcen: Der eigene PostgreSQL-Container (`di-ma-b-*`), die Keycloak-/APISIX-/Admin-/Portal-Container und das eigene Docker-Netz wurden entfernt; verbleibende eigene Container: keine. Die ignorierten `.runtime/`- und `build/`-Pfade im isolierten Workspace enthalten nur Test-/Evidenzartefakte.
- Nicht ausgeführt/nicht erforderlich: M00–M02 sind der MA-0-Gate und nicht Teil der MA-D-Pflichtmenge (Handoff `test_selection` M21–M25); es fehlt keine Pflicht-ID. Kein MA-E-Datei-/Origin-/S3-/Range-Test, kein echter externer Legacy-Produktionsbestand, keine Native-Vollmatrix, keine Rechts-/Revisionssicherheitszertifizierung. Die 62-Root-Datei und die Beispieldatei sind synthetische lokale Fixtures; die Aussagen gelten für den geprüften Kandidaten, nicht für einen produktiven S3-/Gateway-Betrieb.
