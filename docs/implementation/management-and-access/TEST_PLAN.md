# Risikobasierter Test- und Abnahmevertrag

Mitgeltend zu [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Keine feste Testzahl/Coveragequote und **keine Pflicht, nach jedem Fix alle vorherigen Phasen zu wiederholen**. Die folgende Matrix ist ein Anforderungsinventar, keine lineare Liste, die stets komplett abzulaufen ist.

## 1. Grundprinzipien

1. Beobachtbares Verhalten prüfen: persistierte Beziehungen, tatsächlicher Actor, unveränderte Historie, gültige/ungültige Zugriffe und echte Datei-Bytes. „Klasse vorhanden“, Container healthy oder HTTP200 alleine genügt nicht.
2. Kleine Unit-Tests für reine Regeln, echte PostgreSQL-Integration für Mapping/Transaktionen/Audit/Autorität. Kein H2-Mock als Beweis von PG-Triggern, Locks oder Rollenrechten.
3. JWT/Cookie/Gatewayverhalten mit der tatsächlich gewählten APISIX-/Keycloak-Version prüfen. Unit-Gatewaymocks ersetzen nicht den realen Integrationstest.
4. Bei Fehlerkorrektur zuerst den Defekt reproduzieren, dann minimale Korrektur und nächste relevante Regression. Bei neuen Konfigurationszeilen keine künstliche RED-Inszenierung.
5. Negativtest braucht positive Kontrolle: existierendes Objekt, funktionierende Route, erlaubter Referenzzugriff. Netzwerk-, Parser- oder Treiberfehler sind kein Beweis korrekter fachlicher Verweigerung.
6. Isolierte Datenbanken/Volumes/Ports/Hostpfade und frische Secrets. Nutzerinstanz nicht stoppen, löschen oder ihre Daten verändern. Keine globalen Docker-Bereinigungen.
7. Nach jedem Phasenkandidaten unabhängiger Lauf. Dessen neue Gegenprobe ist klein und zielgerichtet, nicht eine zusätzliche allgemeine Fuzzingplattform.
8. Bei allen Tests unterscheiden: `PASS`, `FAIL`, `NOT_EXECUTED` (Pflicht fehlt) und `NOT_REQUIRED` (begründet nicht betroffen). Ein Pflicht-Skip ist kein PASS.

## 2. Phasenmatrix und vorgeschlagene Testorte

Die Testklassennamen sind Vorschläge. Gleichwertige vorhandene Klassen nutzen; im Request Anforderungs-ID auf tatsächlich ausgeführten Test mappen. Mehrere Assertions können in einem Test dieselbe Anforderung beweisen.

### MA-0 – Voraussetzungen und autonome Prüfung

| ID | Nachweis | Möglicher Test / kleinster geeigneter Lauf |
|---|---|---|
| M00 | tatsächliche Repos, native Architektur, neue/alte Phasengrenzen, offizielle Boot-GA/Cayenne-M3, unveränderte Nutzerarbeit | lesender Preflight + gezielter Dependencyresolve; kein Foundation-Vollbau |
| M01 | Boot startet mit M3 und PostgreSQL; explizite Cayenne-Transaktion kann Actorwert und DML auf derselben Verbindung ausführen | `CayenneRuntimeCompatibilityIT.sameConnectionTransaction`; kleine isolierte Probentabelle |
| M02 | frischer OpenCode2/DeepSeek-Lauf testfähig; fehlende/falsche SHA-/Modell-/Ergebnisbindung öffnet kein Gate | `ReviewGateContractTest`, echter Reviewer-Toolaufruf, ein negativer Handoff |

### MA-A – Fachmodelle

| ID | Nachweis | Möglicher Test |
|---|---|---|
| M03 | beide ILI-Modelle real kompiliert, positive XTF-Fixtures validiert | `ModelCompilationTest`, tatsächlicher ili2c/ilivalidator-Aufruf |
| M04 | Dataset einziger Rechteanker; Serie/Ausgabe/Version getrennt, keine gemeinsamen Metadatenkopien | `ModelContractTest.datasetOwnsAccess`; Strukturanalyse + passende Fixture |
| M05 | Identifikatoren, Zeitintervalle, Scope-XOR und Parentbeziehungen: erlaubter und verbotener Fall; jede Regel hat zuständige Durchsetzungsebene | `ModelConstraintTest` parametrisiert; nicht allein Compiler-Erfolg |
| M06 | DirectGrant ohne Request, Approval mit Request, Revoke, MTEXT und Metaattribute korrekt darstellbar | `WorkflowFixtureValidationTest`, Unicode/Mehrzeilenroundtrip |

Nicht statisch durch ILI prüfbare Invarianten dürfen als DB-/Servicepflicht ausgewiesen werden, aber nicht als schon ausgeführt. Deren Umsetzung wird MA-B/MA-C abgenommen.

### MA-B – Persistenz und Audit

| ID | Nachweis | Möglicher Test |
|---|---|---|
| M07 | echtes ili2pg-Schema, Cayenne-PK/OID/Beziehung; erneutes cgen; XTF-Export/Validierung erhält fachliche Identität | `IliCayenneRoundTripIT.createRelatedObjectsAndExport` |
| M08 | Actor und DML gleiche Connection/Tx; Rollback nach ORM-Flush; Poolgrösse1 trennt Anna/Ben und anschliessend fehlenden Actor | `AuditedUnitOfWorkIT` mit Backend-PID und Auditread |
| M09 | I/U/D plus Join-/Membershipänderung; alte/neue Werte; redacted Felder; no-op-Verhalten | `AuditTriggerIT` |
| M10 | direkte Auditänderung, TRUNCATE/DDL, Decisionmutation und Grantumdeutung verweigert; Rollen nicht Owner/Superuser | `ManagementRoleBoundaryIT`, echte vorhandene Tabellen |
| M11 | externer Installer idempotent; Metadaten-/Physical-Mapping vollständig; entfernter/deaktivierter Trigger erkannt | `AuditCoverageIT.missingTriggerFails` auf isolierter DB |
| M12 | Setup-Re-run und relevante additive Migration erhalten Daten, OIDs, Grants/Audit; kein Neuimport beim Appstart | `SchemaLifecycleIT` |
| M13 | begrenzter Management-Backup/Restore in separate DB erhält Beziehungen/Audit und dokumentierte Rechte | `ManagementRestoreIT`/Testwrapper, keine Nutzer-DB |

### MA-C – Verwaltung und Identität

| ID | Nachweis | Möglicher Test |
|---|---|---|
| M14 | echter Browser-Codeflow + Backend-Access-JWT; falsche Signatur/issuer/audience/abgelaufen abgelehnt | `OidcLoginIT`, wenige `JwtValidationTest`-Fälle |
| M15 | Create/Edit/Publish/AccessLevel mit richtigen capabilities; fremde Office/Objekt-ID verweigert; bestehende Felder bleiben erhalten | `CatalogCommandServiceIT` |
| M16 | Self-Request→Approve/Grant; Deny ohne Grant; DirectGrant; Revoke; Audit/Fachentscheidung korrelierbar | `AccessWorkflowIT` |
| M17 | doppelte idempotente Anfrage, anderer Payload bei gleichem Key, parallele Entscheidung, stale Edit | `ConcurrentDecisionIT` mit zwei echten Connections, `IdempotencyIT` |
| M18 | Authorization liest aktuelle Rootrechte, direkte/Gruppenwege und Intervalle; gleiches JWT bleibt nach Revoke ungültig für Daten | `DownloadAuthorizationRepositoryIT` |
| M19 | Actorheaderfälschung, direkte interne API ohne Servicecredential, CSRF, GET-Mutation und offene Redirects verweigert | `ManagementHttpSecurityIT` |
| M20 | Auditansicht und Berechtigtenliste nur im eigenen Scope; Direktentzug zeigt eventuell verbleibenden Gruppenweg; kein SQL-Aktivversprechen | `ManagementViewsIT` und ein kleiner Browserablauf |

Zeitfälle bevorzugt mit klar vergangenen/zukünftigen fixierten Zeitpunkten plus reinem Intervallgrenztest, nicht minutenlanges sleep. Die produktive API nimmt keinen frei gesetzten `asOf`-Zeitpunkt zur Umgehung aktueller Rechte entgegen.

### MA-D – Öffentliches Sodata

| ID | Nachweis | Möglicher Test |
|---|---|---|
| M21 | Suche/Filter/Sortierung/Pagination, Einzelangebot/Serie/Ausgabe, aktuelle Ausgabe; nur öffentliche sichere Metadaten | `JdbcCatalogRepositoryIT`, vorhandene Controller-/VM-Tests gezielt |
| M22 | Metadatenänderung nach Commit auf neuem Request an zweite Instanz sichtbar; Start ohne XTF/DuckDB/Jenkins; DBfehler ohne Snapshotfallback | `DatabaseCatalogModeIT` |
| M23 | Legacy dry-run, Konflikterkennung, stabile ID-Zuordnung, idempotenter Import; Adminänderung nicht durch Reimport überschrieben | `LegacyCatalogImportIT` |
| M24 | Publickonto SELECT auf View erlaubt, Mutation und reale Grant/Audit/Storage-Basistabelle verweigert | `PublicCatalogRoleIT` |
| M25 | rohe Altartefakte im DB-Modus nicht ausgeleitet; Drafts weder über Details noch Facetten; Antragslinks gehen zum richtigen Backend | `CatalogDisclosureIT`, `CatalogNavigationBrowserTest` |

Keine vollständige WebR-/WASM-/WMTS-/Superset-Suite, solange deren Code/Abhängigkeiten nicht beeinflusst wurden. Ein Bootupgrade verlangt relevante Appstart-/Template-/Security-Smokes, aber nicht jede unveränderte Datenanalyse erneut.

### MA-E – Gateway, Dateien und Gesamtprozess

| ID | Nachweis | Möglicher Test |
|---|---|---|
| M26 | echte private Datei: open anonym erlaubt; restricted ohne Anmeldung/Grant verweigert; berechtigter Zugriff liefert erwarteten Hash | `ManagedDownloadIT` |
| M27 | Grant/Revoke und open↔restricted gelten nach Commit bei nächsten Requests mit gleichem Token; ältere verfügbare Version/Formate erben Rootrecht | `ImmediateRevocationIT` |
| M28 | HEAD, Range/206 und conditional GET korrekt; vor 304 erneut autorisieren; kodierte/mehrdeutige Pfade, falscher Filename, andere Methode verweigert | `DownloadHttpContractIT` |
| M29 | S3/origin/Altgateway nicht anonym umgehbar; zuvor erreichbarer alter Canary nach Cutover tatsächlich gesperrt | `DownloadBypassIT` mit echtem Objekt und positiver Kontrolle |
| M30 | Authz-Timeout/DBfehler fail closed; keine Credentials an Origin oder in Logs; S3fehler nicht als Download200 | `DownloadFailureIT` |
| M31 | zwei APISIX-/zwei Admininstanzen verwenden aktuelle DB ohne Policy-Rollout; gleicher Browser-/Tokenkontext funktioniert über Wechsel | `MultiInstanceAuthorizationIT` |
| M32 | zusammenhängender Browser-/HTTP-Ablauf: Suche→Antrag→Entscheid→Datei→Entzug→Audit; Metadatenänderung erscheint | `ManagementAccessJourneyIT` |
| M33 | Management-/Gateway-Neustart erhält Identitäten/Secrets/Grants/Audit; dokumentierter Standardstart und Grenzen stimmen | `ManagementRestartIT`, Doku-/Konfigurationsprüfung |

**MA-E ist zugleich der Gesamtintegrationsreview.** Er führt die neue zusammenhängende Kette aus, nicht erneut blind alle vorherigen Unit-Tests. Bereits vorhandene ClickHouse-/Superset-Testrechte werden nicht verändert. Falls gemeinsamer Compose-/Secretcode geändert wurde, genau die betroffenen Start-/Isolation-Smokes ergänzen.

## 3. Testschichten und Aufrufvertrag

Empfohlene Struktur in Admin: normale `test`-Unit-/Web-Slice-Tests, eigener `integrationTest`-Task für echte PG-Verträge und `gatewayTest` oder Stackwrapper für reale Services. Bestehende Testcontainers-/Composehilfen weiterverwenden. Nicht zwei konkurrierende Integrationsharnesses einführen. Docker-Runner darf Ports/DBname/ENVpfad explizit übergeben; keine ignorierten Overrides.

Aufruf beispielhaft, **erst implementieren und tatsächlich dokumentieren**:

```text
./scripts/management/test.sh --phase MA-B --selection <pfad>
./gradlew test --tests '*IntervalRuleTest'
./gradlew integrationTest --tests '*AuditedUnitOfWorkIT'
```

Eine Testauswahl enthält Requirement-IDs, tatsächliche Kommandos, Repo/CWD, Begründung und erwartete Beobachtung. JUnit/XML darf zusammenfassend referenziert werden; prüfen, dass Test wirklich ausgeführt wurde und nicht alt/geskippt ist. Keine neue umfassende Evidenceplattform.

## 4. Delta-Testmatrix bei Fehlerkorrekturen

| Geänderte Stelle | Neu prüfen | Nicht automatisch neu prüfen |
|---|---|---|
| MTEXT/Attribut/Assoziation im Modell | Compiler/Validator, betroffene DBabbildung/Cayenne, betroffene Views/Import | gesamte OIDC-/Downloadmatrix |
| row_version/PK-/Transaktionshülle | Keys, Actorbindung, Rollback, Konkurrenz, ein betroffener Fachablauf | sämtliche HTMLlayouts |
| Audittrigger/Installer | I/U/D, Relation, Redaction/Privilegien, Coverage; betroffene Actorprobe | Superset/ClickHouse, komplette Katalogsuche |
| Grant-/Gruppen-/Zeitlogik | passende Positiv-/Negativfälle, direkter Authz-Read, gleicher Token nach Entzug | Backuprestore, unveränderte cgen-Generierung |
| JWT/CSRF/Gatewayreihenfolge | echter Login, API-Token, anonymer open-Zugriff, Spoofing, relevante negative Fälle | alle Metadatenmodelle neu importieren |
| Pfad-/Originrewrite | kanonischer Objektmatch, kodierte Umgehung, HEAD/Range/304, private/alte URL | alle Adminformulare |
| Public-SQL/Filter | relevante Suche/Facetten/Disclosure, zweite Instanz falls Cache betroffen | komplette AuthN-/Auditmatrix |
| Boot/Cayenne/JDBC-/zentrale Security-Abhängigkeit | betroffene Start-/Persistenz-/Securityverträge umfassender, abhängige Integration | keine pauschale Annahme „nur Version, keine Tests“ |
| nur README/Linkkorrektur | Links/Pfade/Kommandokonsistenz | unveränderte Container neu bauen |

Jeder Nacharbeitsrequest nennt **alt akzeptierten Kandidaten**, neuen Diff, Reproducer, neu ausgeführte Pflichtchecks und übernommene Belege. Reviewer darf Auswahl erweitern, wenn ein plausibler Wirkungszusammenhang besteht. „Zur Sicherheit alles“ ohne solchen Zusammenhang ist kein sinnvoller Standard.

### 4.1 Wann alte Nachweise übertragbar sind

`REUSED` ist nur zulässig, wenn der Reviewer bestätigt:
- geprüfter Vertrag und testrelevanter Produkt-/Test-/Konfigurationscode unverändert;
- relevante Abhängigkeiten/Inputs/Schema-/Runtimeversionen unverändert;
- frühere Prüfung tatsächlich unabhängig am referenzierten Kandidaten bestanden;
- neuer Diff kann den Vertrag nicht plausibel beeinflussen.

Im Bericht alten Kandidaten/Reporthash und Begründung nennen. Tests, die den konkreten Defekt oder einen betroffenen Sicherheitsvertrag beweisen, müssen neu laufen. Sind Abhängigkeiten unklar, gezielt nachprüfen statt Übertragbarkeit zu behaupten.

Beim erstmaligen Phasenreview müssen neue Phasenziele selbst getestet werden. Bei Dokumentationskorrektur kann die Gegenprobe die Dokumentations-/Runnerbindung betreffen, muss nicht erneut drei Gateways starten. Beim Abschlussreview bleibt die neue fachliche E2E-Kette Pflicht.

## 5. Eigene Gegenprobe des Reviewers

Mindestens ein eigenständig gewählter sinnvoller Fall je Phase/Reviewumfang. Beispiele als Anregung, nicht vom Implementierer vorgegebene Pflichtkopien:

- Model: Grant versucht Ausgabe statt Root zu referenzieren; zwei currentZeiger auf falsche Eltern.
- Audit: Gruppenzuordnung ändert sich, aber zugehörige Tabelle hat keinen Trigger; Actor nach Poolwiederverwendung falsch.
- Workflow: doppelter Entscheid mit unterschiedlichem beneficiary; direkte Grantlöschung statt Widerruf.
- Public: Drafttaucht nur in Facetten auf; erneuter Import überschreibt publizierte Adminbeschreibung.
- Gateway: gültiger ETag wird nach Revoke benutzt; kodierter Pfad trifft anderes Originobjekt; alter öffentlicher Alias bleibt erreichbar.

Reviewer schreibt Probe ausserhalb des Produktbaums, dokumentiert erwartete/tatsächliche Wirkung und führt sie aus. Keine Reparatur im Review. Findet sie einen Defekt: NACHARBEIT, nicht Test abschwächen.

## 6. Ressourcen, Secrets und Ablauf

Reviewcheckouts als Geschwister, eigene Compose-Projektnamen, Ports, ENVdateien, Schreibpfade und Volumes. Ein anderer Projektname alleine isoliert keine Bindmounts. Buildcaches gemeinsam nur wenn nicht Produktdaten/Secrets überschrieben werden. Dockerimages können anhand belegter Quelle/Image-ID wiederverwendet werden.

Keine globale Installation/Umkonfiguration von OpenCode oder DBeaver. Browserkontext für Tests neu, keine privaten Sessions. Logs minimieren und sanitizen; keine Screenshots mit Passwörtern. Lesender DBeaver/ClickHouse-Bestand bleibt in dieser Phase unverändert. Kein `down -v` gegen Nutzerstack, kein docker system prune.

## 7. Abschlussbeweis

Ein nachvollziehbarer Satz Quellen/Versionen und exakter Commit-Satz, alle MA-Phasen unabhängig akzeptiert, finaler E2E-Lauf, verbleibende Grenzen dokumentiert. Audit ist nachvollziehbar und gegen normale Runtimeänderungen geschützt; keine rechtliche Zertifizierung behaupten. Keine ClickHouse-/Superset-Synchronisierung als bereits implementiert darstellen.
