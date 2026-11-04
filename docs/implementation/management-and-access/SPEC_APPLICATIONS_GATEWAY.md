# Anwendungen und Gateway – Klassen, Methoden und HTTP-Verträge

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Die vorgeschlagenen Typen sind zu implementierende Verantwortlichkeiten. Kleine vorhandene Helfer wiederverwenden; keine Klasse ohne echte Aufgabe, kein allgemeines Framework. Fachmodelle und Persistenzvertrag sind mitgeltend.

## 1. Klare Requestketten

```text
Verwaltung:
  Browser -> APISIX/OIDC -> Admin-Service -> Cayenne -> PostgreSQL
                                                        -> Audittrigger
Katalog:
  Browser -> APISIX -> Sodata -> api_public-Views (nur lesend)
Datei:
  Client -> APISIX -> forward-auth -> Authorization API -> PostgreSQL
           APISIX <- erlaubt / verweigert
           APISIX -> interner Datei-Origin -> privates S3
           Client <- Datei via APISIX, nicht via Admin/Sodata
```

Die Authorization API ist zunächst ein Modul/Package im Adminprozess, kein zusätzlicher Dienst. Sie hat eigene Sicherheitskonfiguration und lesende DB-Verbindung. Ihre Verfügbarkeit ist für Downloads relevant; ein späteres Herauslösen bleibt möglich. APISIX besitzt keine Datenbankcredentials und keinen fachlichen Grantbestand.

## 2. Konfigurations- und Infrastrukturklassen

| Klasse | Vertrag |
|---|---|
| `ManagementProperties` | Typisierte Properties für DB-Vertragsrevision, URLs, Inputgrenzen, Deploymentmodus; Validierung beim Start |
| `ManagementDataSources` | qualifizierte Writer-, Authz- und optional Auditread-DataSources; unterschiedliche Credentials |
| `ManagementCayenneConfiguration` | M3-Runtime/DataMaps mit Writerpool; siehe Persistenzvertrag |
| `ManagementSecurityConfiguration` | getrennte Filterketten für interne Authorization API, Browserverwaltung/Selbstbedienung und Health |
| `SchemaContractHealthIndicator` | prüft lesend erwartete Schema-/Mapping-/Auditrevision; kein DDL |
| `ManagementExceptionHandler` | übersetzt fachliche Fehler in verständliche 400/401/403/404/409/503, keine Stacktraces/Secrets |
| `RequestCorrelationFilter` | serverseitig erzeugte/streng geprüfte Request-ID; keine freie Actorübernahme |

Java 25, Boot-GA und Cayenne5-M3 wie im Hauptplan. Admin JTE/HTMX in der bestehenden Stilrichtung, keine SPA-Pflicht. SQL-/Policy-Entscheide gehören nicht in Templates oder JavaScript.

## 3. Identität, Zuständigkeit und Transaktionsgrenze

### 3.1 Klassenverträge

| Klasse | Methoden / Ergebnis |
|---|---|
| `VerifiedActorResolver` | `resolve(JwtAuthenticationToken)` → ActorContext mit verifiziertem issuer/subject; keine Ableitung aus `X-User` |
| `PrincipalRepository` | `findByExternalIdentity(ctx, issuer, subject)`, `findByOid(ctx, oid)`, begrenzte Suche für Direktvergabe |
| `PrincipalService` | `findOrRegisterVerifiedUser(actor, command)`; idempotent, keine impliziten Daten-/Adminrechte |
| `AuthorityService` | `require(ctx, actor, dataset, capability)`, `listManageableDatasets(actor, capability)`; aktuelle DB-Zuständigkeiten |
| `EffectiveAccessService` | `describeForPrincipal(dataset, principal)` → aktive direkte/Gruppenwege für UI, keine langlebige Cachewahrheit |
| `GroupMembershipService` | `addMember(...)`, `revokeMembership(...)` nur expliziter Operator; gleiche Audit-/Zeitregeln |
| `AuthorityBootstrapCommand` | einmalige kontrollierte Einrichtung lokaler Demo-Zuständigkeiten; kein öffentliches IAM-Adminendpoint |

Verifizierte unbekannte Nutzer können sich erstmalig registrieren und für sich anfragen. Ein reiner Authorization-Check ist **read-only** und legt keinen Principal an. Noch unbekannte Person: open wie anonym; restricted ohne Grant verweigert.

OIDC-Gruppen-/Realmrollen sind nicht automatisch Datensatzrechte. Seed-Admin zur technischen Einrichtung ist von fachlicher AuthorityAssignment getrennt. Eine echte zentrale Kontosperrung ist später zu integrieren; im MVP prüft die API `Principal.active` bei personenbezogenen Rechten. Ein noch gültiges JWT ersetzt diese Prüfung nicht.

### 3.2 Fachservices schreiben nur über AuditedUnitOfWork

Alle mutierenden Services nehmen `ActorContext` aus der geprüften Anmeldung, `CommandContext` sowie eng typisierte Commands entgegen. Keine Requestparameter für actor, approvedBy, issuer oder serverseitige Zeitpunkte. Repositories bekommen den Context der bestehenden UnitOfWork; kein Repository erstellt heimlich eine zweite Transaktion.

Methoden liefern immutable DTOs/IDs, nicht einen offen weiterverwendeten ObjectContext. Aktuelle revisionsabhängige Werte nach Commit gegebenenfalls frisch lesen. Anforderung/Receipt/Auditfehler führt zu Rollback. Nachgelagerte hypothetische ClickHouse-Projektion ist **nicht** Bestandteil dieses Commitvertrags.

## 4. Katalogverwaltung bis Methodenebene

### 4.1 Commands und Services

`DatasetCommands`: `CreateDataset`, `UpdateDraftMetadata`, `UpdatePublishedMetadata`, `SubmitForReview`, `PublishDataset`, `ArchiveDataset`, `ChangeAccessLevel`. Alle Updates tragen Dataset-OID und expectedVersion; commandId aus sicherem Commandvertrag.

| Methode `CatalogCommandService` | Fachlicher Vertrag |
|---|---|
| `createDraft(actor, command, input)` | ownerOffice-Zuständigkeit prüfen; stabile IDs erzeugen; initial restricted bevorzugen; keinen public Default aus fehlendem Formularwert |
| `updateDraft(actor, command, datasetId, expectedVersion, patch)` | nur draft/in_review nach erlaubtem Übergang; manage_metadata; erlaubte Felder explizit |
| `updatePublishedMetadata(...)` | explizite Aktion „Speichern und veröffentlichen“, manage_metadata+publish; sofortiger neuer gültiger Metadatenzustand |
| `submitForReview(...)` | draft→in_review; kein Datenrecht ändern |
| `publish(...)` | in_review/draft→published nur publish; Pflichtmetadaten und Verknüpfungen prüfen; CatalogAction |
| `archive(...)` | published→archived; öffentliche Darstellung/Dateiauslieferung endet, Daten/Entscheide bleiben |
| `changeAccessLevel(..., newLevel, reason)` | manage_access+publish; separates deutliches Kommando; CatalogAction+Audit; alle verfügbaren Versionen betroffen |

Kein generisches `save(anyEntityFromJson)` und keine automatische Bindung aller ORM-Felder. Eigentümerwechsel/Issue-Reparenting nicht Bestandteil einfacher Editformulare; er würde Zuständigkeiten verändern und benötigt einen gesonderten späteren Vertrag.

`DatasetIssueService.createIssue`, `updateIssueMetadata`, `setCurrentIssue`, `setCurrentVersion` prüfen Elternzugehörigkeit, Status und erwartete Rootrevision. `DataVersionRegistrationService.registerAcceptedVersion(reference)` verwendet bestätigte bestehende Lieferinformationen, schreibt keine Fachdatenzeilen und macht keine neue ClickHouse-Lieferung. `DistributionRegistrationService.registerPrepared`, `verifyAndActivate`, `withdraw` prüfen privaten Storagepfad und tatsächlichen Hash/Bytes; kein willkürlicher HTTP-Fetch aus vom Nutzer gelieferten URLs.

Interne Registrierung darf zunächst als Operator-/Fixture-CLI erfolgen. Ein kompletter Upload-/DataVersioneditor ist nicht Pflicht. Backendverträge und reale Testdaten müssen aber existieren.

### 4.2 Minimaler Admin-UI-Umfang

Controller/Views:

- `ManagementDatasetController.list`, `detail`, `editForm`, `saveDraft`, `savePublished`, `submit`, `publish`, `archive`, `changeAccess`.
- `ManagementIssueController.list`, `create`, `setCurrent`; minimal ausreichend zur Serie-/Ausgabeprobe, keine vollständige Tabellenkalkulationsoberfläche.
- `ManagementAuditController.history(datasetId, page)` über scope-geprüften AuditQueryService.

Pfade `/management/...`, nicht das bereits gatewayseitig gesperrte technische `/admin/...` missbrauchen. Bearbeitbare Pflichtfelder im MVP: Titel, Beschreibung, fachlicher Kontakt, ausgewählte Themen/Keywords, Publikationsstatus über Aktionen, AccessLevel über eigene Aktion. Übrige importierte Felder beim Speichern nicht auf null setzen. Ein existierendes volleres Formular darf erhalten werden.

Lesbare Statusmeldungen: „gespeichert“, „publiziert“, „Datenzugang eingeschränkt“ erst nach Commit. Niemals „SQL-Zugang aktiv“ behaupten; ClickHouse-Projektion fehlt in dieser Etappe.

## 5. Zugangsworkflow und persönliche Funktionen

### 5.1 Serviceverträge

| Typ/Methode | Aufgabe |
|---|---|
| `AccessRequestService.request(actor, datasetId, reason, requestedUntil, command)` | Antrag für Actor; published/restricted; kein bereits wirksames Recht bzw. kein doppelter pending Request; eindeutige Rückgabe |
| `AccessRequestService.cancel(actor, requestId, expectedVersion, command)` | eigener pending Antrag, sonst Konflikt/Verbot |
| `AccessRequestQueryService.mine(actor, page)` | nur eigene Anträge und Status |
| `AccessRequestQueryService.pendingForApprover(actor, filters)` | nur tatsächlicher Zuständigkeitsbereich |
| `AccessDecisionService.approve(actor, requestId, expectedVersion, validity, reason, command)` | aktuelle Authority, atomar Request terminal+Decision+Grant+Audit |
| `AccessDecisionService.deny(...)` | Request terminal+immutable Decision, kein Grant |
| `AccessGrantService.grantDirect(actor, datasetId, beneficiaryId, validity, reason, command)` | zuständiger Berechtiger; aktive Person/verwaltbare lokale Gruppe; kein künstlicher Request |
| `AccessGrantService.revoke(actor, grantId, expectedVersion, reason, command)` | einmalige Beendigung und immutable Revoke-Decision; andere Berechtigungswege erhalten |
| `AccessGrantQueryService.forDataset(actor, datasetId)` | scope-geprüfte Rechteübersicht, effektive Rechte verständlich darstellen |
| `AuditQueryService.forDataset(actor, datasetId, cursor)` | nur berechtigte Historie, begrenzte Ausgabe, redacted Daten |

approve/deny/revoke unter dokumentiertem Rowlock und Revisionstest. Ein Request kann nicht von zwei parallel agierenden Bearbeitern divergierend abgeschlossen werden. Bereits ausgeführtes identisches Kommando wird mit demselben Ergebnis beantwortet. Keine automatische Verlängerung bei erneutem Formularsubmit.

Gültigkeitsintervalle serverseitig prüfen, kein Client-`now` als Wahrheit. Benutzersuche begrenzt, nur bekannte/gezielt angebundene Identitäten. Keine komplette AIO-Verzeichniskopie implementieren. Direkte Rechte an service Principals sind modellseitig vorbereitet, allgemeiner Serviceaccount-Lifecycle ist nicht Pflicht.

### 5.2 UI und Zuständigkeit

Self-Service im Admin-Backend unter `/access/*`, visuell im Portalzusammenhang. Damit bleibt PUBLIC tatsächlich read-only:

| Pfad | Verhalten |
|---|---|
| GET `/access/requests/new?dataset=<uuid>` | Anmeldung falls nötig; Dataset aus vertrauenswürdiger DB, Formular |
| POST `/access/requests` | eigener Antrag, CSRF/Idempotenz |
| GET `/access/me` | eigene Anfragen/Freigaben und effektiver Dateizugang |
| POST `/access/requests/{id}/cancel` | nur eigener pending Antrag |
| GET `/management/requests` | zuständige offene Anfragen |
| POST `/management/requests/{id}/approve` / `deny` | Fachentscheidung |
| GET `/management/datasets/{id}/grants` | Zuständigkeitsgeprüfte Liste |
| POST `/management/datasets/{id}/grants` | Direktvergabe |
| POST `/management/grants/{id}/revoke` | Entzug |

Berechtigungsprüfung in Services, nicht nur versteckte Buttons. Unzuständige können keine fremde Objekt-ID direkt ansteuern. Keine Mutation über GET. Fehlertexte verständlich und ohne sensitive DBdetails. Im UI zwischen „dieser Grant entzogen“ und „durch Gruppe weiterhin berechtigt“ unterscheiden.

## 6. Authentifizierung: eindeutiger statt impliziter Vertrag

### 6.1 Zuständigkeit

APISIX-Standardplugin `openid-connect` übernimmt Browser-Codeflow und geschützte Session-Cookies. API-Clients können Bearer-Access-Tokens senden. Admin/Authorization-Backend validiert weitergereichte **Access-Tokens** mit Spring Security Resource Server selbst: Signatur/Algorithmus, fester issuer, exp/nbf und **audience für diese API**. Kein ID-Token als API-Token, kein ungeprüftes JWT-Decoding.

Das verhindert, dass ein erfundener `X-Verified-Subject` die Berechtigung ändert. Backendidentität immer aus validiertem Token. Clientsecrets/Refresh-Tokens verbleiben beim Gateway. Backend bekommt nur benötigte Identitätsinformationen; keine beliebige Weitergabe an Origin.

Die konkrete Gatewaykonfiguration muss gewährleisten, dass OIDC vor forward-auth läuft. Vorgesehener Standardweg: `set_access_token_header=true`, Token in `Authorization` sofern von der konkreten Pluginversion unterstützt. Tatsächliche 3.19-Optionen/Phasenreihenfolge prüfen. Kein eigenes Lua-Plugin als Reparatur.

### 6.2 Öffentlicher Zugriff bleibt anonym möglich

Nicht jede Downloadanfrage darf vor der fachlichen Prüfung einen Loginredirect auslösen. Auf `/downloads/*` optionale Authentifizierung konfigurieren: ohne Identität an Authorization weiter, dort open erlauben/restricted 401. Browserlogin über einen dedizierten `/login`-Einstieg bzw. `/access/*`.

Explizit ungültiges Bearertoken führt zu 401, nicht zu ungeprüft übernommener Identität. Ein abgelaufenes Browserlogin darf eine Erneuerung verlangen; es darf nicht aus alten Claims weiter berechtigen. Öffentlicher Datensatz muss auch ohne Cookie tatsächlich funktionieren. Bearer-Prüfung und Browsersitzung getrennt testen.

### 6.3 Keycloak und Container-URLs

Vorhandenen Realm und Benutzer-IDs erhalten; ergänzend einen Gateway-OIDC-Client, explizite Redirect-URIs und Audience-Mapping für die Management-API. Keine pauschalen Wildcardredirects. Für API-Testtokens zulässigen vorgesehenen Testclient verwenden; eine nur im Test notwendige Grantart nicht unbemerkt allgemein aktivieren.

Browser/externe issuer-URL und Container-intern erreichbare Token-/JWKS-Endpunkte bewusst konfigurieren. `localhost` im Container ist nicht der Host. Java kann festen erwarteten issuer und separat erreichbare JWKS-URI verwenden. APISIX-Discovery/Backchannel muss tatsächlich funktionieren; Keycloak-Hostname-/Backchanneloptionen prüfen. Nicht issuer-/TLS-/Audienceprüfung abschalten, um eine falsche URL zu kaschieren. Lokales HTTP nur auf Loopback/isoliertem Compose, Produktionsgrenze dokumentieren.

Session-Cookie: HttpOnly, passender SameSite/Path, Secure im TLS-Betrieb. APISIX-Instanzen verwenden denselben sicher verwalteten Cookie-/Sessionkey und OIDC-Kontext. Keine Sessionsecrets beim Neustart regenerieren. `returnTo` nur erlaubte relative interne Pfade, kein offener Redirect.

### 6.4 CSRF trotz internem Bearerheader

Der Browser sendet ein Cookie; APISIX macht daraus intern ein Bearertoken. Dadurch sind Browser-POSTs **weiterhin CSRF-relevant**. Nicht pauschal CSRF deaktivieren, weil Admin intern einen Authorization-Header sieht.

Standard-Spring-CSRF-Mechanismus für UI-POSTs, z.B. CookieCsrfTokenRepository mit serverseitig geprüfter Tokenübermittlung in Formular/HTMX-Header und strengem Origin-/Referer-Vertrag. Keine Mutation über GET; SameSite alleine nicht als vollständigen Nachweis verwenden. Keine neue globale Redis-Sessionpflicht. Falls HTTP-Session-basierter CSRF verwendet wird, muss Mehrinstanzenverhalten explizit funktionieren; bevorzugt stateless kompatibler Cookie-/Tokenweg.

Eine unabhängige API für mutierende Machinecalls ist nicht Pflicht. Interne Setup-CLI wird nicht über eine ungeschützte Webroute angeboten.

## 7. Authorization API – konkreter Laufzeitvertrag

### 7.1 Eingang und Schutz

Interner GET `/internal/authorization/check`, nur Gateway erreichbar. Kein öffentlicher APISIX-Catch-all darf `/internal/*`, Actuator oder Setupoperationen zum Admin durchreichen. Admincontainer hat standardmässig keinen Hostport.

Anfrage enthält:

- serverseitig von APISIX gesetzte ursprüngliche HTTP-Methode und **rohe** URI;
- vorhandenes Access-Token im vereinbarten Header;
- Korrelationskennung;
- zusätzlich ein Gateway-Servicecredential, im lokalen MVP ein zufälliges internes Secret, in `forward-auth.extra_headers` gesetzt. Backend prüft es; vom Browser mitgeliefertes gleichnamiges Feld wird nicht als Quelle akzeptiert. Produktion kann mTLS verwenden.

Gatewaycredential ist keine Benutzeridentität. JWT-Prüfung bleibt erforderlich. Vorhandene X-Forwarded-Uri/Method/Host aus der Clientanfrage nicht übernehmen. `request_headers` auf tatsächlich benötigte Werte begrenzen. Keine URL-/Userinfo-/Queryparameter als Autoritätsquelle.

### 7.2 Klassen und Methoden

| Typ | Vertrag |
|---|---|
| `DownloadPathResolver` | `DownloadTarget parse(String rawUri, String method)`; exakt kanonischer Pfad, kein S3-Fetch |
| `DownloadTarget` | distributionId UUID, exakt erwarteter fileName, method GET/HEAD |
| `GatewayRequestVerifier` | `verifyServiceCredential(headers)`, `extractOriginalRequest(headers)`; keine clientseitigen Pfadüberschreibungen |
| `AuthorizationController` | `check(request)` → festgelegter HTTP-Status, keine Datei, keine Tokenantwort |
| `DownloadAuthorizationService` | `decide(Optional<VerifiedSubject>, DownloadTarget)` → immutable AuthorizationDecision |
| `JdbcAuthorizationRepository` | `evaluate(issuer, subject, distributionId, fileName, action)`; **eine** frische parametrisierte DB-Abfrage/Statement-Snapshot |
| `AuthorizationDecision` | allowed, reasonCode, datasetId/distributionId intern, policyObservationTime; keine Daten oder Secrets |

Abfrage umfasst gleichzeitig Pfadregistrierung, Root/Issue-Publikationsstatus, Version-/Distributionverfügbarkeit, AccessLevel, Principal.active, direkte Grants, aktive lokale Gruppenmitgliedschaften und gültige Grants. DB-Zeit für Intervalle, nicht manipuliertes Clientdatum. Kein Querycache, kein alter Cayenne-Context, keine asynchrone ReadReplica.

Bei diesem einfachen Rechtevertrag direkte SQL-Abfrage statt einer neuen Policyengine. Logik darf zur Lesbarkeit in feste Views/CTEs strukturiert werden, aber kein frei konfigurierbares Benutzer-SQL. Ergebnis ist kleiner DTO. Nicht zuerst Klassifikation cachen und später Grant aus anderer Transaktion nachladen.

### 7.3 Statusvertrag

| Ergebnis | Status |
|---|---|
| erlaubter open oder Grantzugriff | **204** |
| fehlende notwendige oder ungültige Identität | **401** |
| identifizierter Nutzer ohne gültiges Recht | **403** |
| unbekannte/nicht publizierte/zurückgezogene Datei | **404**, keine Dateiexistenzdetails |
| ungültiger Pfad/mehrdeutige Anfrage | **400** |
| andere Datenmethode als GET/HEAD | **405** |
| DB-/Authz-Abhängigkeit nicht verfügbar | **503**, kein Inhalt |

Nie `200 {allowed:false}`. APISIX wertet erfolgreiche HTTP-Antwort als Freigabe. Fehler dürfen kein 2xx bekommen. Authorization-Endpunkt macht keine Loginredirects; Browserlogin bleibt eigener Einstieg. Begrenzte feste Fehlercodes, keine SQLfehler/Claims an Client.

### 7.4 Aktualitätsgarantie und Grenzen

Eine neu begonnene Entscheidung nach dem erfolgreichen Commit liest den neuen Stand. Ein bereits während der vorherigen Transaktion begonnener Request kann den vorherigen Snapshot gesehen haben; kein universeller atomarer Zeitpunkt über laufende Downloads behaupten. Im Test denselben weiterhin gültigen JWT benutzen, grant/revoke durchführen, danach neue Anfrage auf jede Instanz: Wirkung ohne Logout, Reload, Policydatei oder Podrestart.

Gilt mehrere Wege: Widerruf des direkten Grants kann Gruppenzugriff erhalten. Ein endgültiger Entzug aller Wege wird nur behauptet, wenn tatsächlich keiner mehr besteht. Datenbankausfall: für **alle verwalteten** Dateien fail closed, nicht nur restricted; andernfalls könnte veraltete open-Klassifikation ausgenutzt werden.

## 8. Kanonische Pfade und privater Datei-Origin

Erlaubte URL exakt `/downloads/<uuid>/<SafeFileName>`. UUID kanonisch, Dateiname entspricht dem registrierten Eintrag. Unbekannte UUID/anderer Name verweigern. Für MVP keine Queryparameter an Downloads; keine Tokens in URL. Range läuft über HTTP-Header.

Ablehnen: zusätzliche Pfadsegmente, `..`, Backslash, wiederholte Slashes, NUL, ungültiges UTF-8, Prozentkodierung des ansonsten erlaubten ASCIIpfads und doppelte Kodierung. Den **rohen** URI prüfen, damit vorgelagerte Normalisierung keinen anderen Originpfad zulässt. Autorisierter Pfad und Originpfad müssen identisch sein. Redirect-/Rewrite-Regeln dürfen nicht nach der Prüfung auf ein anderes Objekt wechseln.

Privater Origin:

- rclone mit technischem **read-only** S3-Zugang, auf privates Bucketprefix `downloads/` begrenzt;
- keine Websitefreigabe/anonymous S3-Rechte; kein Hostport des Origin;
- keine Directory-/Bucketlistings durch Gateway: nur die exakte Dateiroute erreicht Origin;
- Archive/Originale/Prüfberichte liegen ausserhalb des Origins, auch bei open nicht automatisch abrufbar;
- keine Presigned-URL-Redirects, die später den Gateway umgehen;
- externe S3-Direktzugriffe mit technischen Credentials sind Operatorzugänge, keine Benutzer-Downloadalternative.

Wo Garage nur Bucketrechte anbietet, darf Prefixisolation nicht als native S3-Policy behauptet werden. Dann technisches Konto für den privaten Bucket + eng konfigurierter Originpfad und keine Preisgabe des Kontos; optional getrennte interne Buckets zur technischen Isolation sind erlaubt, aber nicht als fachliche open/restricted-Klassifikation.

## 9. APISIX-Konfiguration und Datei-HTTP

Statische Routekonfiguration, keine Berechtigungsupdates in `apisix.yaml` pro Benutzer. Standards verwenden:

```yaml
# Strukturbeispiel, keine vollständige lauffähige Route.
plugins:
  forward-auth:
    uri: http://admin:8080/internal/authorization/check
    request_method: GET
    request_headers:
      - Authorization
      - X-Request-ID
    allow_degradation: false
    status_on_error: 503
    timeout: 2000
    keepalive: true
```

OIDC, interne Servicecredentials, Routenprioritäten, Host-/Origin-/Headerregeln und Responseheader vollständig ergänzen und am wirklichen Plugin prüfen. Timeout konfigurierbar, lokale 2000ms ist ein Startwert, keine Performancegarantie. Bounded DB-/HTTP-Pools, keine unendlichen Retries im Requestpfad.

Dateiübertragung muss GET/HEAD, mindestens einfache Byte-Range/206, Content-Length, Content-Type, Content-Disposition, Accept-Ranges und relevante ETags korrekt behandeln. Kein vollständiges Laden in Java-RAM. Bei ungültiger Range sinnvoller Fehler, keine andere Datei. Auch HEAD/conditional GET/304 müssen **vor** Antwort autorisiert werden. Gültiger ETag darf eine inzwischen entzogene Berechtigung nicht umgehen.

**Zugangsdaten zum Origin entfernen:** nach erfolgreicher forward-auth-Prüfung dürfen Authorization, Cookie, X-Access-Token, X-ID-Token, X-Userinfo und interne Gatewaysecrets nicht an rclone/S3 weitergereicht werden. Standard-Pluginmechanismen in richtiger Phase verwenden; z.B. `upstream_headers` zum Entfernen nicht zurückgegebener Authheader nur nach tatsächlich geprüfter Semantik. Nicht vor der Identitätsprüfung entfernen. Kein eigenes Lua-Plugin.

`Cache-Control: no-store` zunächst für alle verwalteten Downloadantworten einschliesslich open und Fehler/304. Kein APISIX proxy-cache auf diesen Routen. So kann open→restricted für neue eigene Abrufe durchgesetzt werden. Bereits heruntergeladene oder fremd gecachte Kopien sind nicht widerrufbar. Statische Portalassets können getrennt weiter cachen. Same-origin bevorzugt; kein wildcard CORS zusammen mit Credentials.

## 10. Migration alter öffentlicher Wege

Die neue private Route allein schützt keine alte öffentliche Kopie. Für jedes migrierte Testobjekt ein kleines Inventar: alte Gateway-/Website-/S3-URLs, alte Rohkatalog-/DuckDB-Artefakte und kontrollierte Copies. Neues privates Objekt mit Hash/Grösse prüfen. Dann eigene alte öffentliche Auslieferung sperren/entfernen und negative Abrufe nachweisen; erst danach als kontrolliert einschränkbar registrieren.

Keine pauschale Bucketlöschung oder Änderungen fremder Datenportal-/S3-Bestände. Auf laufender Nutzerinstanz Migration standardmässig dry-run; apply nur ausdrücklich auf bezeichnete eigene Testobjekte mit gesichertem Original. Integrationstests verwenden eigene synthetische Canaries, die zuvor nachweislich öffentlich erreichbar waren. Ein 404 auf einer nie existierenden Datei beweist nichts.

Externe öffentliche Originale bleiben öffentlich; private Demoidentität davon unterscheiden. Der noch vorhandene alte Bucket kann für nicht migrierte Legacyartefakte bestehen bleiben. Der Verwaltungsdienst darf deren Schutz dann nicht behaupten. Keine anonyme Aliasroute für die neuen kontrollierten Datasetdateien.

## 11. Sodata: DB-Lesepfad statt Gesamtsnapshot

### 11.1 Klassen und Methoden

| Typ | Vertrag |
|---|---|
| `CatalogQuery` | q, Filter, sort, page, pageSize; begrenzen, sort allowlist |
| `CatalogQueryService` | `search(CatalogQuery)`, `facets(CatalogQuery)`, `findDataset(identifier)`, `findIssue(datasetIdentifier,issueKey)`, `findCurrentIssue(datasetIdentifier)` |
| `JdbcCatalogRepository` | gebundene Queries auf api_public-Views; Abbildung auf immutable DTOs |
| `CatalogPage`, `DatasetDetail`, `IssueDetail`, `DistributionLink` | read-only Darstellungsdaten ohne private DB-/Storagefelder |
| `DatabaseCatalogConfiguration` | expliziter database-Modus, Public-DataSource, Contracthealth; keine Startup-XTF-Abhängigkeit |
| vorhandene Controller/VM-Factories | nur Datenquelle austauschen; bestehende JTE/HTMX-Darstellung gezielt erhalten |

Bekannte vorhandene Einstiege: `CatalogService.withSnapshot`, CatalogController, CatalogDetailController, CatalogArtifactController, CatalogSearchService, FacetService und ViewModel-Factories. Tatsächliche Namen prüfen. Nicht die ganze App neu schreiben und nicht jede bisherige Methode mit einer leeren Snapshotattrappe bedienen.

DB-Modus ausdrücklich per `DATENINFRASTRUKTUR_CATALOG_SOURCE_TYPE=database` oder gleichwertiger vorhandener Konfiguration. Dann keine Abhängigkeit von current.json, DuckDB oder Jenkins. Alte fixture/file-Modi können für Vergleich bestehen bleiben, aber bei DBfehler **kein** stiller Rückfall auf eventuell unsicheren alten Stand. 503 und aussagekräftige Readiness, Liveness bleibt Prozesszustand.

### 11.2 Suche und Konsistenz

Kleine DB-basierte Suche reicht: parametrisierte tokenisierte Titel-/Beschreibung-/Keywordabfrage oder PostgreSQL Fulltext mit dokumentiertem Verhalten. Vorhandene vereinbarte Suche/Filter/Sortierung möglichst bewahren. Komplexe bisherige Lucene-Operatoren entweder wirklich unterstützen oder die Abweichung ausdrücklich dokumentieren, nicht still falsche Ergebnisse behaupten. Deterministische Secondary-Sortierung für Pagination.

Kein persistent veralteter Katalogcache. Zusammengehörende Detail-/Facetten-/Resultatabfragen können eine kurze read-only Transaktion verwenden, damit eine Seite konsistent ist. Nächster HTTP-Request beginnt frisch. Authz ist davon unabhängig und verwendet eine einzelne frische Entscheidung. Test auf zwei Portalinstanzen.

Eine Beschreibung kann eingeschränktes Markdown enthalten: bestehenden sicheren Renderer verwenden. Kein ungefiltertes HTML aus MTEXT. Themen/Keyword-/Zählerfacetten dürfen versteckte Draftobjekte nicht verraten. Ebenso Detail-ID-Zugriff und Serien-Ausgabeverweise prüfen.

### 11.3 Artefakte und persönliche Links

Im DB-Modus alte komplette XTF-/DuckDB-Downloads und Explore-Kontexte deaktivieren (404/410 dokumentieren), soweit kein echter aktueller gefilterter Export gebaut ist. Die Exportneuentwicklung ist nicht Pflicht. Alte UI-Links entfernen, nicht eine historische Datei als aktuellen Katalog ausgeben. Keine laufende Authz aus Lucene/Snapshot.

Sodata zeigt Antragslink zu `/access/requests/new?dataset=<oid>` und „Meine Zugänge“ zu `/access/me`. Adminbackend bearbeitet diese Schreibfunktionen. Public-DBkonto bleibt strikt read-only. Ein BFF mit eigener zweiter Schreibimplementierung ist unnötig.

## 12. Start, Mehrinstanzen und Betrieb

Admin startet mit Schema-/Auditrevisionprüfung ohne DDL. Sodata lädt DB-Views, braucht keinen öffentlich autorisierten Dateiabruf für eigenen Bootstrap. Dadurch kein Kreis „Sodata braucht Katalog → Gateway fragt Sodata“. Setupdateien/Imports nutzen ausdrücklich interne technische Wege.

Relevante Zusatzkonfiguration: Adminimage, Writer/Authz/Public-Zugang, OIDC-Client-/Sessionsecret, interne Gateway-Authz-Secret, private Origincredentials. Werte frisch lokal erzeugen, erhalten, nie ins Git. Keine zusätzlichen Hostports für DB/Authz/Origin; Zugriff über Gateway. Bestehende APISIX/Jenkins-Netzwerktopologie nur ändern, wenn nötig und getestet.

Für MA-E zwei APISIX- und zwei Admin-Instanzen mit gleichen statischen Regeln/Sessionkontext, derselben DB und getrennten Laufzeitpfaden. Eine zweite Publicinstanz für Aktualitätsprobe. Isolierter Compose-Test genügt, kein Kubernetes. Alle Entscheidungen lesen primär, keine Policypropagation. Neue Instanz braucht korrektes Konfigurations-/Secretsetup, aber keinen Grant-Download.

Betriebsdiagnose: Health, DBrevision, Fehler-/Timeoutzähler, Korrelationskennungen, keine vollständigen JWTs/SQLbindings. Nach Neustart gleiche Benutzer-IDs, Daten, Grants und Audit. Nicht automatisch Testfreigaben erneut vergeben.

## 13. Fehlerverträge

- Falscher Bearerissuer/audience/signature, gefälschter Actorheader: 401/403, keine Daten, keine Mutation.
- Richtiger Actor aber falsches Dataset/Scope:403.
- Stale Form/doppelter divergierender Entscheid:409, keine partielle Mutation.
- Unbekannte/withdrawn Datei:404; echter Origincontent darf nicht ausgeliefert werden.
- PostgreSQL-/Authorizationausfall:503/fail closed, nicht „open aus Cache“.
- Unmögliche Auditierung: Mutation scheitert, kein Grant ohne Nachweis.
- S3-Fehler nach erfolgreicher Autorisierung: kein erfundener Download-Erfolg; Originstatus sinnvoll, keine Credentials.
- Kopie bereits ausserhalb eigener Infrastruktur: nicht rückholbar, Betriebsgrenze benennen.

Die konkrete Testsuite ist in TEST_PLAN festgelegt. Keine beliebigen HTTPfehler als erfolgreichen Sicherheitsnachweis zählen: zuerst mit gültigem Referenzzugriff echtes Objekt und Erreichbarkeit beweisen.
