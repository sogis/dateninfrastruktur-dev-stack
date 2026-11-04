# Reviewrequest MA-C

## Ausgangspunkt und Gate

- ADMIN base: `9536465ed4af211bf8b88e435baaec28fb6d01b7`
- STACK base: `5e548cce9864897e5e443b95d49ab5e172dc7bc2`
- PUBLIC base: `8349be8aba4036ca0bb56e89cb62398e34404a5e`

MA-B ist unabhängig ABGENOMMEN am Kandidaten 20261104T153442Z; Bericht
MA-B-accepted.md und ignorierter gebundener Handoff bleiben unverändert.
MA-C beginnt erst dahinter. MA-D/MA-E werden nicht vorweggenommen.

## Zusammenhängender Umfang

Boot4.1.2/Java25/Cayenne5-M3, JTE/HTMX-Verwaltung unter /management und
Selbstbedienung unter /access. Explizite Metadatenallowlist erhält importierte
übrige Felder; Office-/Datasetzuständigkeiten frisch aus DB. Neue Entwürfe
restricted; Publish/Archive/ChangeAccess als eigene Aktionen mit immutablem
CatalogAction. Serienausgaben und aktuelle Zeiger prüfen Parent und Rootrevision.
Bestätigte Lieferreferenzen/Dateiregistrierung sind Backend-/Operatorverträge;
Aktivierung liest echte Bytes/Hash über vertrauenswürdigen privaten Verifier.
Kein neuer Lader, keine Dateien durch Admin, noch kein S3-Origin.

Request/Cancel/Approve/Deny/DirectGrant/Revoke im selben AuditedUnitOfWork:
Rootlock vor Request-/Grantlock, expectedVersion, aktuelle Capability im
Schreibkontext, immutable Decision, atomare terminale Anfrage+Grant+Audit.
Actor-/Aktions-/Payloadgebundene Receipts verhindern doppelte Ausführung und
Verlängerung. Payloadstruktur mit Feld-/Listen-/Nullgrenzen. Lookup/Registrierung
exakt issuer+subject; GET und Authorization registrieren niemanden.

Standardgateway-OIDC mit eigenem Keycloak, Backend-RS256/issuer/audience/exp/nbf/
Access-Typ-Prüfung. Spring-Bearerfilter explizit ohne CSRF-Ausnahme des
ResourceServer-Configurers; Standard-Cookie-/XOR-CSRF plus Origin/Referer.
Separate interne Filterkette mit Gatewaycredential, keine öffentliche
Durchreichung. Keine Actorheader-/Realmrollenautorität. Kein Rechtecache.
Authorization: eine frische parametrisierte Primary-PG-Anweisung umfasst
Datei/Version/Issue/Root, aktive Principals/Gruppen, Grantintervalle und DB-Zeit;
kanonischer Rohpfad, GET/HEAD und fail-closed-Statusvertrag.

Scopegeprüfte bounded Request-/Freigaben-/Auditansichten; separates Auditreader-
Konto, escaped MTEXT. Direkter Entzug lässt andere Wege bestehen. Kein SQL-
Aktivversprechen. Bootstrap und lokale Gruppen ausschliesslich expliziter
Operator, keine Web-IAM-Konsole.

MA-B-REV-01/02: vollständiger readonly Physical-Mappingvergleich mit kontrollierten
technischen Ergänzungen; fremder Fingerprint wird vor Quelldateischreiben/DDL
verweigert. Expliziter gepinnter B→C-Upgradepfad für allein additive V007,
Vorgängerhash sowie unveränderte Modell-/Mapping-/alte Migrationshashes. Neues
Web-Startup/Readiness prüft notwendigen Receipt-/Auditreadervertrag. Kein DDL
beim Appstart, kein Demo-Reset, kein automatischer Reimport.

## Frische Tests und Reviewkommando

Aus STACK: `./scripts/management/test.sh --phase MA-C`.
Aus ADMIN: `python3 scripts/test_management_all.py`.
Die Suite verlangt freien eigenen Runtimezustand und räumt im finally nur ihre
eigenen gelabelten Container/Netze/Volumes auf. Zufällige Loopbackports und neue
Testcredentials, keine Original-.env. Reviewer bekommt eigene Checkouts.
Playwright-GC ist explizit deaktiviert; keine fremden Browsercaches entfernen.

| ID | Neu ausgeführter Nachweis |
|---|---|
| M14 | OidcLoginIT: echter Chromium→APISIX→Keycloak-Codeflow, HttpOnly/SameSite-Cookie, Backend-Access-JWT; JwtValidationTest: tatsächlich signierte RSA-Tokens mit falschem issuer/aud/exp/Signatur/ID-Typ abgelehnt |
| M15 | CatalogCommandServiceIT: Create/Edit/Submit/Publish/Access/Archive, falsche Capability/fremdes Office/ID, erhaltener Importinhalt; DeliveryRegistrationIT: Serie/Ausgaben/Zeiger und echte private Testdateibytes mit SHA256 |
| M16 | AccessWorkflowIT: Antrag→Approve/Grant, Deny ohne Grant, DirectGrant ohne Fakeantrag, einmaliger Revoke; Audit-Command und Transaktions-ID korreliert; erzwungener Auditfehler rollt Decision/Receipt vollständig zurück |
| M17 | zwei echte parallele DBverbindungen entscheiden denselben Request, genau ein terminaler Entscheid; identischer Request/Approve replayt ohne Duplikat/Verlängerung; anderer Payload konflikthaft; stale Metadatenrevision verweigert |
| M18 | DownloadAuthorizationRepositoryIT: alte/neue verfügbare Versionen erben Root; direkt+Gruppe, deaktivierte Gruppe/abgelaufene Membership/zukünftiger Grant; Revoke letzter Weg; offene/archivierte Datei; ManagementHttpSecurityIT: derselbe echte JWT mit/nach Grant204→403 ohne Restart |
| M19 | ManagementHttpSecurityIT: Actorheaderfälschung, ID-Token/ungültige Signatur, fehlendes Gatewaycredential, öffentliche interne Route, CSRF/Origin/GET-Mutation und Originalpfad/-methode verweigert; keine returnTo-Weiterleitung implementiert |
| M20 | ManagementViewsIT plus Browser: eigene Anträge, scoped Audit/Freigaben/beschränkte Identitätssuche, unzuständige Person verweigert; effektive Wege und UI-Hinweis zu verbleibenden Gruppenzugängen |

Zusätzlich frische AuditedUnitOfWorkIT/ManagementStartupIT als kleinste relevante
Transaktions-/Frameworkregression; echte bekannte B→C-Upgradeprobe über nichtleere
UUID-/Auditdaten, fremder Fingerprint ohne Quellwrite; reproduzierter physischer
Mappingdrift. JUnit wird nicht gecacht, fehlende/skippte angeforderte Klassen
scheitern. Logs/gesicherte JUnit-XML unter ADMIN/.runtime/management-c-evidence/.

## Übertragbare Nachweise und Grenzen

ILI-Modelle, ili2pg/cdbimport/cgen, PK-/Audittriggergrundvertrag und öffentliche
Views unverändert vom akzeptierten MA-B. Physisches Mapping und betroffene
Startup-/UOW-/Upgradeverträge trotzdem frisch geprüft. Kein erneuter grosser
unveränderter Superset-/ClickHouse-/WebR-/Foundationlauf. Der Reviewer führt
M14–M20 und eine eigene Gegenprobe selbst aus; frühere Akzeptanz ersetzt diese
Ausführung nicht.

Keine Native-/Produktionszusage, keine ClickHouse-/Superset-Rechteprojektion.
Isolierte C-Testtopologie hat ausdrücklich loopbackgebundene direkte Testports;
endgültige private Deploymentgrenzen/Origin/echte Download-HTTP-Verträge sind
MA-E. Sodata bleibt bis MA-D unverändert. Keine privaten Originalsecrets im
Handoff oder Commit, kein Remote-Push. Audit ist keine Rechtszertifizierung.

Nach dem frischen Gesamtlauf wurde allein die Scope-vor-Revisionsprüfung geschärft.
AccessWorkflowIT/CatalogCommandServiceIT/ConcurrentDecisionIT/IdempotencyIT/
DeliveryRegistrationIT laufen dafür neu; JWT-/OIDC-/Mappingcode bleibt unverändert.

Ergänzende Frameworkregression `python3 scripts/compatibility.py` und
`python3 scripts/management/test_review_gate.py` sind erfolgreich neu ausgeführt.
