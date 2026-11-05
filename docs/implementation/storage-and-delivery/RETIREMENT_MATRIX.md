# G0 – verbindliche Zuordnung aktiver Pfade

Pfade sind relativ zum jeweils genannten Produktrepo. Historische Abnahmen werden
nicht verändert. Die Phasenspalte ist ein Umsetzungsauftrag, kein Erledigt-Nachweis.

| Repo / tatsächlicher Pfad | Aktueller Aufrufer | Ersatz / Wegfall | Neue Regression | Phase |
|---|---|---|---|---|
| STACK compose.yaml (garage/origin/jenkins/storage-tool) | Normalstart/Setup | Ein privater ch.so.daten, Reader/Writer, kein Defaultkey | G10–G19 | G1 |
| STACK services/garage/setup-compose.py | garage-setup | Ein idempotenter Provisioner, keine Fresh/Migrationrechteverzweigung | G10/G11/G13/G19 | G1 |
| STACK scripts/compose_runtime.py render/storage_conf | init/render | Fester Reader/Writervertrag, kein Defaultfallback | G13/G18 | G1 |
| STACK services/apisix/routes.template.json | render/gateway | Bestehender forward-auth/Origin, keine alten Bucketaliasrouten | G12/G17/G55 | G1/G5 |
| ADMIN models/SO_AGI_DataInfrastructure_Catalog_20261104.ili Distribution | ili2pg/Mapping | Neues Catalogmodell ohne storageProfile/legacyAccessUrl | G16/G21 | G1 |
| ADMIN src/main/java/ch/so/agi/dateninfrastruktur/admin/catalog/DeliveryRegistrationService.java | Operator/Backend | Profilfreie Registrierung; später einziger validierter CSVabschluss | G16/G25/G28/G48 | G1/G2/G4 |
| ADMIN src/main/java/ch/so/agi/dateninfrastruktur/admin/catalog/RclonePrivateObjectVerifier.java | Operator | Fester Key/Endpoint, keine Profilauswahl | G17/G18 | G1 |
| ADMIN scripts/legacy_import.py und Gradle legacyImport | One-shot Herkunftsimport | Nach verifiziertem Cutover aus aktivem Tool-/Imagepfad entfernen | G56 | G5 |
| ADMIN scripts/managed_runtime.py, identity_runtime.py, managed_control.py | historische Launcher | Aktive Aliase entfernen, generische Schematools behalten | G50/G56 | G5 |
| PUBLIC src/main/java/ch/so/agi/datenportal/catalog/importxtf/ | CatalogImportConfiguration | Entfernen; ausschliesslich JdbcCatalogRepository | G29/G56/G57 | G5 |
| PUBLIC catalog/service/CatalogSnapshotLoader.java, CatalogSnapshotBuilder.java, CatalogReloadService.java (unter src/main/java/ch/so/agi/datenportal/) | Snapshot-/Reloadbetrieb | Entfernen, DB-Query/VMs behalten | G56/G57 | G5 |
| PUBLIC config/CatalogImportConfiguration.java, SnapshotMode.java, SnapshotModeCondition.java | Springkonfiguration | Keine Source-Type-Auswahl; DB allein | G50/G56 | G5 |
| PUBLIC web/CatalogArtifactController.java, admin/reload/AdminCatalogController.java (unter gleichem Java-Präfix) | alte HTTP-Routen | Entfernen, kein Gesamtkatalogartefakt/Reload | G55/G56 | G5 |
| PUBLIC catalog/database/ und web/*VmFactory.java | DB-Controller/Seiten | Behalten: Suche/Facetten/Paging/Detail/Serien/Ausgaben/Kontakt/Struktur/Downloads | G29/G51/G57 | alle |
| PUBLIC explore/ und src/main/frontend/explore/ | im DB-Modus deaktiviert/410 | Obsolete deaktivierte Produktzweige entfernen, keine Datenwerkstattintegration | G56/G57 | G5 |
| PLUGIN src/main/java/ch/so/agi/jenkins/gretldatenportal/ | altes HPI | Alte RootAction/Scanner/Generator/Teams/ACLs/GUIparser/Steps entfernen; neues delivery-Package | G30–G39 | G3 |
| PLUGIN src/main/resources/ch/so/agi/jenkins/gretldatenportal/ | alte Jelly/JS/Formulare | Neue schlanke APIoberfläche, keine alten Routen-/Stepwrapper | G33/G37/G39 | G3 |
| JENKINS plugins.txt, Dockerfile, jenkins.yaml | Imagebuild | Gepinntes OIDC/neues HPI, Java21/17 erhalten, kein altes Rollenprovisioning | G30/G36/G39/G50 | G3 |
| STACK services/jenkins/jenkins-stack.yaml | JCasC | OIDC, Minimalrechte, ein di-csv-ingest; alte lokale Lieferkonten/Lock/Seeder weg | G31/G32/G39 | G3 |
| TOPICS shared/gretl-datenportal-teams.yaml | Scanner/ACL-Sync | Entfernen; PG-Fachrechte | G22/G39/G56 | G3 |
| TOPICS shared/Jenkinsfile | Organisationspipelines | Fester versionierter CSVjob/Runnerbundle | G31/G35/G38 | G3/G4 |
| TOPICS shared/gradle/datenportal-publication.gradle | initializePublication/Organisationsbuilds | Validator-/Exportbausteine in runner/ integrieren, Katalogpublikation entfernen | G40–G49/G56 | G4 |
| TOPICS shared/gradle/datenportal-{s3,git,initialize}.gradle, organisation-common.gradle | alter Publisher | Entfernen; private immutable Artefakte/keine Gitwrites | G45/G46/G56 | G4 |
| TOPICS shared/gradle/publication-models.json und alte Datasheet-/PublishedCatalog-Bindungen | Offlinebundle/Katalogexport | Datenvalidierungsmodelle behalten, Metadaten-Livetransport entfernen | G40/G50/G56 | G4/G5 |
| STACK scripts/bootstrap-publication.sh, bootstrap.py, management/* Wrapper | alte Betriebseinstiege | Ein kanonischer Betrieb, reine Aliase entfernen; review-phase.py behalten | G50/G56/G59 | G5 |
| STACK scripts/migration_*.py, consolidation.py und Migration-Composeprofile | abgeschlossene MA-F-Umstellung | Generische Helfer entkoppeln; aus aktiver Operator-/Image-API entfernen | G50/G56 | G5 |

## Datengrenzen und Laufzeitobjekte

Nur alter Inhalt des identifizierten lokalen `ch.so.daten` ist zum Purge freigegeben.
Die 16 PGreferenzierten Distributionen einschliesslich Historie sind zu erhalten.
Die Inventur trennt Dateien von virtuellen rclone-Verzeichnissen (17 Dateien,
18 Verzeichniseinträge); die unreferenzierte Datei bleibt bis zur Zuordnung geschützt.
`di-managed-private` erst nach byte-/metadatengeprüfter Übernahme entfernen.
Unbekannte zusätzliche Sourceobjekte sind ein enger Cutoverblocker, keine
Löschfreigabe. Zusätzlicher lokal aliasierter Bucket wird erst nach Nachweis
reiner Foundation-Smoke-Fixtures entfernt; keine Ableitung allein aus seinem Namen.

Jenkins hat aktuell acht Jobs. Individuelle Marker/Definitionen müssen vor Retire
belegen, welche vom bisherigen Plugin stammen. Keine Prefixlöschung, keine
pauschale Übernahme fremder Jobs. Bestehendes Home bleibt. Vier PG-Principals,
Grants/Decisions und alle 208 vorhandenen Auditzeilen bleiben erhalten.

## Sodata-Funktionsmatrix

| Benutzerfunktion | Istpfad | Erhaltungsnachweis |
|---|---|---|
| Suche/Facetten/Pagination/Sortierung | DatabaseCatalogController.index, CatalogQueryService.search, JdbcCatalogRepository | G57 DB-Query-/Webtest |
| Datasetdetail/Kontakt/Struktur/Nutzung | DatabaseCatalogController.dataset, DetailPageVmFactory | G51/G57 |
| Serien/gewählte und aktuelle Ausgabe | DatabaseCatalogController.series/issue | G57 |
| Aktuelle und historische Downloads | DB-Readmodel → /downloads/<uuid>/<filename> → forward-auth → Origin | G17/G51/G52 |
| Explore/WebR | DB-Controller liefert bereits 410, ENV false | Obsoleter Zweig; keine aktive Benutzerfunktion zugesagt |

## Nachweise

G0 inventarisiert, entfernt aber noch keinen Produktpfad und keine Nutzerdaten.
Die jeweilige Phase ergänzt ihren eigenen konkreten Diff-/Test-/Reviewbeleg.
