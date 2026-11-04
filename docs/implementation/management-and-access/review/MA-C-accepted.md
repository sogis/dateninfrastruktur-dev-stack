# Review MA-C / 20261104T162930Z

## Urteil

**ABGENOMMEN**

Am exakten Kandidaten-SHA-Satz wurden die Pflichtchecks **M14–M20** in einem
frischen, selbst gestarteten Lauf ausgeführt; alle JUnit-Klassen liefen mit
`tests>0`, `skipped=0`, `failures=0`, `errors=0`. Die eigene Gegenprobe wurde
real ausgeführt und bestand. Der Produktbaum ist vor/nach unverändert. Offene
BLOCKER/MAJOR: keine. Zwei nicht blockierende MINOR-Hinweise sind unten
dokumentiert; sie ändern weder Authentisierung/Autorisierung noch den
Fachvertrag und wurden nicht repariert.

## Bindung

| Element | Wert |
|---|---|
| Handoff-SHA256 | `0e4d1f4a2f86decae22f85a4b186c3a154eb10681f0d1ac8d1e29b50c78a1c4b` (selbst geprüft) |
| Spezifikationsaggregat | `73d761aef0c9b370efbc3078aa5a529ce4a43d2a314c8bc8f081cf8d7121bac1` (12 Einzeldateien selbst gehasht) |
| Request-SHA256 | `44c959592cfd8a95fb9e0dc277375ad59ab8f302991872bca6d343ce3191c956` (selbst geprüft) |
| Workspace-AGENTS | `02e456b5a6b0b37d2fdd87314304926f77f6b675aa01cfd7ed366544aae0f091` |
| dateninfrastruktur-dev-stack | HEAD `60f32a7f5f6c48610e49afe6a4468cf4d730aa72` (base `5e548cce9864897e5e443b95d49ab5e172dc7bc2`, Vorfahre) |
| dateninfrastruktur-admin | HEAD `abc26cc5d45a93e7f27b4d6f413720ff0f7fec3c` (base `9536465ed4af211bf8b88e435baaec28fb6d01b7`, Vorfahre) |
| dateninfrastruktur-sodata | HEAD `8349be8aba4036ca0bb56e89cb62398e34404a5e` (base=head, unverändert) |
| Reviewer | OpenCode v2.2.5 (Desktop-CLI `.../cli/2.2.5-arm64/opencode-cli`), Modell `deepseek/deepseek-flash` |
| Session | `ses_e589b1101ffeRFC6I4Kd9ExTI4` |
| Isolation | eigener Multi-Repo-Kandidat unter dem Handoff-Workspace; je Lauf eigener PG16/PostGIS-Container mit Zufalls-Loopbackport und frischen Testcredentials; eigener Keycloak/APISIX/JVM-Testverbund; nur eigene gelabelte Ressourcen entfernt |

Alle drei Checkout-HEADs stimmen exakt mit dem Handoff überein; `git status
--porcelain` war vorher und nachher leer. Der Handoff-, Spezifikations-,
Request- und Workspace-AGENTS-Hash wurde selbst nachgerechnet. Der tatsächliche
Runner ist die Desktop-CLI `2.2.5-arm64/opencode-cli`, die `opencode v2.2.5`
meldet und mit `--model deepseek/deepseek-flash` gestartet wurde
(`output/evidence/runner-evidence.txt`). Das `opencode` auf `PATH` ist eine
unabhängige ältere 1.18.22-Installation und nicht der Runner.

## Code und Zielerreichung

Gelesen wurden der vollständige Diff `base..head` beider geänderten Repos
(STACK: 3 Dateien; ADMIN: 69 Dateien) und die neuen Quellen, Templates,
Migrationen und Skripte; Sodata ist `head=base` und wurde nicht verändert.

- **OIDC/JWT/Security:** `ManagementJwtDecoder` erzwingt RS256, festen Issuer,
  Audience, `exp`/`nbf` (eigene Gegenprobe) und `typ=Bearer`. Drei getrennte
  Filterketten (`health`, `internal`, `browser`) verhindern die
  ResourceServer-CSRF-Ausnahme; `GatewayCredentialFilter` schützt die interne
  Authorization-Route, `BrowserOriginFilter` + Standard-Cookie-/XOR-CSRF
  sichern Browser-POSTs, `VerifiedActorResolver` leitet Identität
  ausschliesslich aus dem geprüften JWT ab. `X-User`/`X-Verified-Subject`
  bleiben wirkungslos.
- **Workflow/Transaktion:** `AccessWorkflowService` führt Request, Cancel,
  Approve, Deny, DirectGrant und Revoke im `AuditedUnitOfWork` aus. Reihenfolge
  ist Root-Lock vor Request-/Grant-Lock; `expectedVersion` wird unter
  `FOR UPDATE` geprüft; die aktuelle Capability wird vor und nach dem Lock im
  Schreibkontext geprüft. Receipts binden Actor, Aktion und strukturierten
  Payload; Decision/Grant/Request/Audit commiten atomar. Ein erzwungener
  Auditfehler rollt Decision und Receipt vollständig zurück.
- **Katalog:** `CatalogCommandService` ändert nur die explizite Allowlist
  (Titel, Beschreibung, Kontakt, Themen, Keywords) und erhält importierte
  übrige Felder. Create/Edit/Submit/Publish/Access/Archive prüfen die
  jeweiligen Capabilities; `DatasetIssueService` prüft Elternzugehörigkeit,
  Status und Rootrevision; `DeliveryRegistrationService` registriert bestätigte
  Lieferungen und aktiviert nur nach Verifier-Evidenz (echte lokale
  Testdateibytes und SHA256).
- **Authorization:** `DownloadPathResolver` akzeptiert nur exakt
  `/downloads/<kanonische UUID>/<SafeFileName>` für GET/HEAD und weist
  Query-/Encoding-/Mehrdeutigkeitsfälle ab. `JdbcAuthorizationRepository`
  verwendet genau eine frische parametrisierte Primary-PG-Anweisung für
  Distribution/Version/Issue/Root, aktive Principals und Gruppen, Intervalle
  und DB-Zeit; Status 204/401/403/404/400/405/503 ist fail closed.
- **Ansichten:** `ManagementQueryService` liefert begrenzte, scope-geprüfte
  Request-/Grant-/Audit-/Identitätssichten; Audit läuft über das separate
  `di_audit_reader`-Konto. JTE gibt MTEXT escaped aus; die UI behauptet keinen
  SQL-Aktivzugang.
- **Startup/Migration:** Start und Readiness prüfen den gepackten
  Persistence-Contract, `di_ops.management_web_contract()`, das
  Auditreader-Konto und die Auditabdeckung ohne DDL. V007 ist die einzige
  additive B→C-Migration; `verify_physical_mapping.py` prüft das vollständige
  physische Mapping, `upgrade_contract.py` erlaubt nur den gepinnten
  Vorgängerfingerprint, und `contract_fingerprint.py` schreibt die
  Contractdatei erst nach erfolgreicher Prüfung. Damit sind die früheren
  MA-B-REV-01/02-Hinweise umgesetzt.

Nicht betroffen/ausserhalb dieses Gates: MA-D (Sodata-DB-Lesepfad) und MA-E
(private S3-/Origin-/Downloadkette, finale Deployment-/TLS-Grenzen,
ClickHouse-/Superset-Rechteprojektion, Native-Vollmatrix). Sodata wurde nicht
verändert.

## Selbst ausgeführte Tests

Hauptkommando (exakt der STACK-Dispatcher, der intern
`dateninfrastruktur-admin/scripts/test_management_all.py` startet):

    cwd:  /Users/stefan/sources/dateninfrastruktur/dateninfrastruktur-dev-stack/.runtime/management-review/MA-C/20261104T162930Z/workspace/dateninfrastruktur-dev-stack
    cmd:  ./scripts/management/test.sh --phase MA-C
    exit: 0 (erwartet 0)

Der Lauf startete einen eigenen `di-ma-b-*`-PG16/PostGIS-Container mit
Zufalls-Loopbackport, importierte das ili2pg-Schema, führte die gezielten
MA-B-Regressionen (AuditedUnitOfWork/ManagementStartup/B→C-Upgrade/
Mapping-Drift) und danach JWT, alle M15–M18/M20-Service-ITs, den BootJar, den
eigenen Keycloak/APISIX/JVM-Verbund sowie die Browser-/HTTP-Tests M14/M18/M19
aus. Im `finally` wurden ausschliesslich die eigenen Container/Netze/Volumes
entfernt.

| ID | Nachweis im Lauf | Erwartet/Beobachtet | Beleg |
|---|---|---|---|
| M14 | OidcLoginIT (echter Chromium→APISIX→Keycloak-Codeflow, Cookie, Request/Approve/Audit/403-Browseransichten) und JwtValidationTest (falscher Issuer/Audience/ID-Typ/Ablauf/Signatur) | 0/0, jeweils tests=1, skipped=0, failures=0 | `output/evidence/M14-evidence.txt` |
| M15 | CatalogCommandServiceIT (2 Tests) + DeliveryRegistrationIT (1 Test): Create/Edit/Submit/Publish/Access/Archive, fremde Capability/Office, erhaltener Importinhalt, Serie/Ausgaben/Zeiger, echte private Bytes/Hash | 0/0, tests=2/1, skipped=0, failures=0 | `output/evidence/M15-evidence.txt` |
| M16 | AccessWorkflowIT (2 Tests): Antrag→Approve/Grant, Deny ohne Grant, DirectGrant ohne Fakeantrag, einmaliger Revoke, Audit-/Transaktionskorrelation, erzwungener Auditfehler-Rollback | 0/0, tests=2, skipped=0, failures=0 | `output/evidence/M16-evidence.txt` |
| M17 | ConcurrentDecisionIT (zwei echte Verbindungen, genau ein terminaler Entscheid) + IdempotencyIT (Replay ohne Duplikat/Verlängerung, anderer Payload Konflikt) + Stale-Revision in CatalogCommandServiceIT | 0/0, tests=1/1/2, skipped=0, failures=0 | `output/evidence/M17-evidence.txt` |
| M18 | DownloadAuthorizationRepositoryIT (alte/neue Versionen, direkt+Gruppe, deaktivierte Gruppe, abgelaufene Membership, zukünftiger Grant, letzter Weg, open/archiviert) + ManagementHttpSecurityIT (gleicher JWT 204→403 nach Revoke ohne Restart) | 0/0, tests=1/1, skipped=0, failures=0 | `output/evidence/M18-evidence.txt` |
| M19 | ManagementHttpSecurityIT: Actorheaderfälschung, ID-Token/ungültige Signatur, fehlendes Gatewaycredential, öffentliche interne Route, CSRF/Origin, GET-Mutation, Originalpfad/-methode | 0/0, tests=1, skipped=0, failures=0 | `output/evidence/M19-evidence.txt` |
| M20 | ManagementViewsIT (eigene Anträge, Scope für Audit/Freigaben/Identitätssuche, unzuständige Person) + OidcLoginIT-Browserablauf (eigene Ansicht, Freigabe, Audit, 403) | 0/0, tests=1/1, skipped=0, failures=0 | `output/evidence/M20-evidence.txt` |

Zusätzlich im selben Review frisch ausgeführt:

- `python3 scripts/compatibility.py` (ADMIN, exit 0, Endzeile „PASS
  Boot/Cayenne/PostgreSQL actor/transaction + ili2pg UUID schema with PostGIS“;
  `output/evidence/supp-compatibility.stdout.log`).
- `python3 scripts/management/test_review_gate.py` (STACK, exit 0, „OK“;
  `output/evidence/supp-review-gate.stdout.log`).

## Übernommene Nachweise

Keine. Alle Pflicht-IDs M14–M20 wurden in diesem Review selbst neu ausgeführt;
es wurde kein fremder MA-C-Beleg übernommen. Die bereits abgenommenen Phasen
MA-0/MA-A/MA-B wurden nicht als Ersatz für M14–M20 gewertet; die gezielten
MA-B-Regressionen liefen im selben frischen Lauf erneut.

## Eigene Gegenprobe

- **Hypothese:** M14 verlangt auch `nbf`-Prüfung, der gelieferte
  `JwtValidationTest` prüft aber nur falschen Issuer/Audience/Typ/Ablauf/
  Signatur. Würde `ManagementJwtDecoder` ein korrekt signiertes Token mit
  zukünftigem `nbf` akzeptieren, könnte ein vorab ausgestelltes Token vor
  Beginn seiner Gültigkeit verwendet werden.
- **Neuer Input/Aufbau:** `output/evidence/nbf-probe/NbfProbe.java` startet
  einen eigenen lokalen JWKS-HTTP-Server, erzeugt einen echten RSA-Schlüssel
  und signiert zwei RS256-Tokens mit korrektem Issuer, Audience, Subject,
  `typ=Bearer` und `exp`; das Kontrolltoken hat kein `nbf`, das Prüftoken
  `nbf=now+3600` und `exp=now+7200`.
- **Kommando/CWD:** im Output-Verzeichnis
  `javac --add-modules jdk.httpserver -cp "$(cat test-classpath.txt)" -d nbf-probe/classes nbf-probe/NbfProbe.java && java --add-modules jdk.httpserver -cp "nbf-probe/classes:$(cat test-classpath.txt)" NbfProbe`
  (Classpath ohne Produktdateiänderung über ein lesendes Gradle-Init-Skript
  ermittelt).
- **Erwartung:** Kontrolltoken akzeptiert; Token mit zukünftigem `nbf` wird mit
  `JwtException` abgelehnt.
- **Beobachtet:** `CONTROL_ACCEPTED sub=probe-user`;
  `FUTURE_NBF_REJECTED: An error occurred while attempting to decode the Jwt:
  Jwt used before 2026-11-04T17:33:49Z`; Exit 0.
- **Schlussfolgerung:** `nbf` wird tatsächlich erzwungen; kein Defekt. Die
  Probe ist unabhängig von den gelieferten Tests und ändert keine
  Produktdatei. Beleg: `output/evidence/nbf-probe/nbf-probe.log`.

## Findings

### MA-C-REV-01 — MINOR (nicht blockierend)
- **Datei/Methode:** `src/test/java/ch/so/agi/dateninfrastruktur/admin/OidcLoginIT.java:27`,
  `realBrowserCodeFlowRequestApproveAndScopedViews`.
- **Beobachtung:** Die Zusicherung
  `anna.cookies().stream().filter(c -> c.name.equals("di_management_session")).allMatch(...)`
  ist bei leerem Filterergebnis vakuum-wahr. Fehlte das Session-Cookie
  vollständig, würde der Test nicht scheitern.
- **Vertrag:** M14 verlangt den Nachweis des HttpOnly/SameSite-Cookies; die
  Produktkonfiguration setzt die Flags korrekt und der echte Browserflow
  bestand, aber die Assertion beweist die Existenz des Cookies nicht positiv.
- **Minimaler Fix:** Nichtleere Cookie-Liste (oder `anyMatch` auf den
  erwarteten Cookie) vor der Flag-Prüfung zusichern.
- **Nicht blockierend:** Kein Produktfehler; die Cookie-Flags sind in
  `identity_runtime.py` gesetzt und der reale Login lief durch.

### MA-C-REV-02 — MINOR (nicht blockierend)
- **Datei/Methode:** `ManagementController.java:61` (`instant`) und
  `ManagementExceptionHandler.java:17–20` (`error`).
- **Beobachtung:** `Instant.parse` wirft `DateTimeParseException`, eine
  `DateTimeException`, nicht `IllegalArgumentException`. Ein fehlerhaftes
  optionales `until` bei `POST /access/requests` oder
  `/management/requests/{id}/approve` fällt daher in den generischen
  503-Zweig (`TEMPORARILY_UNAVAILABLE`) statt 400 (`INVALID_INPUT`).
  Reproduziert durch direkten Aufruf des Produkthandlers:
  `MALFORMED_UNTIL_STATUS=503` (`output/evidence/error-mapping-probe/probe.log`).
- **Vertrag:** SPEC_APPLICATIONS_GATEWAY §2/§13 erwartet verständliche
  400/401/403/404/409/503 für Clientfehler. Der Request bleibt fail closed;
  es ist ein Antwortvertrags-, kein Autorisierungsfehler.
- **Minimaler Fix:** `DateTimeException` in `instant()` abfangen und
  `BusinessException.invalid` werfen oder `DateTimeException` im 400-Zweig des
  Handlers ergänzen.
- **Nicht blockierend:** Ausserhalb der Pflichtchecks M14–M20; keine
  Sicherheitslücke und keine falsche Freigabe.

## Integrität und Grenzen

- **Produktstand vorher/nachher:** `before.json` (SHA256
  `09e503dd40f19a787e31595c97d0ea8e3dcb70a2950ab098a9f1170e5048a98c`)
  wurde mit dem Zustand nach dem Review verglichen: 120 STACK-, 153 ADMIN- und
  917 Sodata-Dateien byte-identisch; keine Änderungen, keine entfernten oder
  hinzugefügten getrackten Dateien; `git status --porcelain` leer. Beleg:
  `output/evidence/integrity.json`.
- **Eigene Ressourcen:** keine `di-ma-*`-/`di.identity`-Container oder -Netze
  nach den Läufen; die Skripte entfernten ausschliesslich ihre eigenen
  labelgeprüften Container/Volumes. Verbleibend sind nur ignorierte
  checkout-lokale Testlogs/XML/Screenshot sowie die Kopien unter `output/`.
- **Secrets:** keine Original-`.env`, keine Credentialdateien, keine Tokens
  gelesen oder in Berichte/Logs kopiert. Testcredentials waren frisch und
  zufällig; die Harness-Logs redigieren bekannte Testgeheimnisse.
- **Grenzen:** MA-D/MA-E sind nicht Teil dieses Gates. Es gibt noch keinen
  echten privaten S3-/Origin-, finalen TLS-/Deployment- oder
  Sodata-DB-Umschaltnachweis; ClickHouse-/Superset-Rechteprojektion und
  Native-Vollmatrix sind nicht geprüft. Audit ist keine
  Rechtszertifizierung und schützt nicht gegen DB-Owner/Superuser. Die
  isolierten Loopback-Testports sind Testinstrumente, keine produktive
  Netzwerkgrenze.
- **Pflichtstatus:** M14–M20 = EXECUTED/PASS; keine NOT_EXECUTED-Pflicht.
  MA-0/MA-A/MA-B/M21–M33 sind begründet NOT_REQUIRED für dieses Gate; die
  gezielten MA-B-Regressionen liefen dennoch erneut.

Original `review.json` SHA256: `ebb079ef9f066955e9d94932d4287ee8078f606e82d959f16593a56c941adfd5`.
