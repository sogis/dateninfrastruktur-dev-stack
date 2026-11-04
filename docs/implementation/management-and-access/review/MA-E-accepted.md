# Review MA-E / 20261104T190434Z

## Urteil

**ABGENOMMEN**

Am exakten Kandidaten-SHA-Satz sind alle acht Pflichtprüfungen M26–M33 vom Reviewer selbst ausgeführt und bestanden; der finale Integrationstest lief real gegen PostgreSQL 16/PostGIS, Keycloak, Garage/S3, zwei APISIX- und zwei Admin-/Public-Instanzen. Die eigene Gegenprobe wurde ebenfalls ausgeführt und bestand. Der Produktstand ist vor/nach dem Review byte-identisch, es sind keine Reviewer-eigenen Container/Volumes/Netze zurückgeblieben, und es gibt keine blockierenden Findings.

## Bindung

| Gegenstand | Wert |
|---|---|
| Phase / Kandidat | MA-E / 20261104T190434Z |
| Handoff-SHA256 | `e4130882766b6b1b89db186a4635350fb513738e03a1892c716f0482f274e331` |
| Spec-Aggregat-SHA256 | `350471821674e9fcd3507a34a3b29f7964c452cd9bcd5b81a6d4e4f5f0c30985` |
| Request-SHA256 | `9d395208080d55cd8f3835dc546541870f7885df9a4f2c382be297dc8d87c259` |
| Workspace-AGENTS-SHA256 | `02e456b5a6b0b37d2fdd87314304926f77f6b675aa01cfd7ed366544aae0f091` |
| STACK HEAD | `94cee111e863b3d4d593724b64ff311ab8d2c82d` |
| ADMIN HEAD | `29c00b0c5b65115cc541ed6086ec6e54a938c870` |
| PUBLIC HEAD | `20d94f5fbb9259f446f7ac0b22dd0e72b2d22ca6` |
| Modell | `deepseek/deepseek-flash` |
| OpenCode | `opencode v2.2.5` (Runner-Binary `.../cli/2.2.5-arm64/opencode-cli --version`) |
| Session | `ses_e580d19deffeoMIpqGP2q3R5iT` (aus `OPENCODE_SESSION_ID` und `events.jsonl`) |

Alle 12 Spec-Dateihashes, der Request, die Workspace-AGENTS und der Handoff wurden selbst nachgerechnet und stimmen mit dem Handoff überein. Der Spec-Aggregatwert ist reproduzierbar als SHA256 über `json.dumps(files_sha256, sort_keys=True)`. Alle drei Checkouts stehen exakt auf den Handoff-HEADs, die Working Trees sind leer (`git status --porcelain` ohne Zeile).

Isolation: eigener Workspace unter `.runtime/management-review/MA-E/20261104T190434Z/workspace`, eigenes `.runtime`, ausschließlich eigene gelabelte Container/Netze/Volumes, zufällige Loopback-Gatewayports (z. B. 50597/50598 bzw. 50691/50692), eine eigene PG16/PostGIS-Instanz pro Lauf, keine Nutzer-`.env`, keine fremden Dienste verändert.

## Code und Zielerreichung

Gelesen wurden der vollständige EXECUTION_PLAN, alle drei SPEC-Dateien, TEST_PLAN, OPENCODE_REVIEW_PROMPT, Workspace-/Repo-AGENTS, der MA-E-Request sowie die Diffs `base..head` aller drei Repositories. Zusätzlich wurden die tatsächlich eingesetzten APISIX-3.19.0-Quellen im Image geprüft (`apisix/init.lua`, `plugins/forward-auth.lua`, `plugins/fault-injection.lua`).

Geprüfte Kernverträge:

- **APISIX/forward-auth:** Das Plugin setzt `X-Forwarded-Method` aus der Originalmethode und `X-Forwarded-Uri` zunächst aus der normalisierten `ctx.var.request_uri`; der Request überschreibt `X-Forwarded-Uri` ausdrücklich mit `$real_request_uri` (`extra_headers`). `init.lua` setzt `real_request_uri` vor der Normalisierung auf die ursprüngliche Request-URI. `upstream_headers` entfernt clientseitige `Authorization`, `Cookie`, `X-Access-Token`, `X-ID-Token`, `X-Userinfo` und `X-DI-Gateway-Credential`, weil die Authz-Antwort sie nicht zurückgibt — im Plugin-Quelltext verifiziert und im Test mit echtem Origin-Beobachter belegt. Kein Lua-Authz, kein APISIX→PostgreSQL, keine Casbin-Datei.
- **Rohpfadschutz:** globale `fault-injection`-Regel mit kanonischem Negativ-Lookahead und Ambiguitätsmuster (Encodings, `//`, `..`, Backslash, Query) vor den Routen-Plugins; `response-rewrite`/Nginx-`add_header always` setzen `Cache-Control: no-store` auch auf Fehler und 304.
- **Java-Authz:** `DownloadPathResolver` akzeptiert exakt `/downloads/<lowercase-uuid>/<SafeFileName>`, nur GET/HEAD (sonst 405), max. 200 Zeichen. `AuthorizationController` verlangt genau einen `X-Forwarded-Uri`/`X-Forwarded-Method`-Header. `GatewayCredentialFilter` vergleicht das interne Secret zeitkonstant. Der JWT-Decoder prüft Signatur (RS256), Issuer, Audience, `typ=Bearer`, `exp` und Subject. `JdbcAuthorizationRepository` entscheidet mit genau einer frischen parametrisierten SQL-Abfrage: published/available-Joins, `open→204`, fehlende Identität→401, Grant/Gruppe/Gültigkeit/`revokedAt`/`Principal.active`→204/403, unbekanntes Ziel→404, SQL-Fehler→503; kein Cache, kein Policy-Rollout.
- **S3-Verifikation/Activation:** `RclonePrivateObjectVerifier` prüft zuerst `lsjson --stat` (Name, `IsDir=false`, Größe, begrenzte Metadaten, Timeout) und streamt danach die Bytes mit SHA256/Größenvergleich; `verifyAndActivate` läuft in `AuditedUnitOfWork`; ein fehlendes Objekt rollt Distribution, `row_version`, Audit und Receipt vollständig zurück.
- **Laufzeit:** zwei APISIX, zwei Admin-, zwei Public-Instanzen gegen dieselbe primäre PG; private Garage mit read-only-rclone-Origin auf `downloads/`; keine internen Hostports; persistente Volumes/Secrets; eigentümergeprüfte Stop/Start/Cleanup-Pfade.
- **Browser/Portal:** `BrowserOriginFilter` erlaubt genau zwei explizite Origins, CSRF bleibt aktiv, kein Wildcard-CORS. PUBLIC setzt `gatewayProtected` nur als Darstellungsmarkierung auf den kanonischen `/downloads/`-Pfad; Legacy-Konstruktoren behalten ihr Verhalten. Die `api_public.distributions`-View liefert ausschließlich den kanonischen Pfad, keine `objectKey`-/Storage-/Grant-/Auditfelder.

Nicht betroffen bzw. nicht neu bewertet: MA-A-Modelle, MA-B-Kernpersistenz/Audit und MA-C-Berechtigungsworkflow (durch den E2E funktional mitgeprüft), MA-D-Katalogmatrix (nur die zwei betroffenen PUBLIC-VM-Tests), ClickHouse/Superset/Jenkins. Die lokale HTTP-/Loopback-Grenze, TLS-/Secure-Produktionskonfiguration, Rechtszertifizierung und externe öffentliche Originale bleiben dokumentierte Grenzen.

## Selbst ausgeführte Tests

Hauptlauf (ADMIN, eigener isolierter Runtime-Bereich, keine `--keep-runtime`-Flagge):

```text
CWD: .../workspace/dateninfrastruktur-admin
CMD: python3 scripts/test_downloads_all.py
Exit: 0 (EXIT=0)
```

Der Lauf führte real aus: `lifecycle-ownership-negative 0`, `explicit-setup 0`, `reserve-owned-topology 0`, `explicit-pilot-seed 0`, `admin-jar 0`, `public-jar 0`, `private-two-instance-start 0`, `missing-private-object-rollback 0`, `private-upload 0`, `M29-old-public-cutover 0`, `real-S3-operator-activation 0`, `M26-M33-final-journey 0`, `protected-links-VM-regression 0`, `PASS`, `owned-cleanup 0`. Beleg: `output/M26-M33.console.log`.

JUnit-Belege (jeweils `skipped=0 failures=0 errors=0`):

| Suite | Tests | Beleg |
|---|---|---|
| `ManagedDownloadsIT` | 1 (M26–M33 in einem realen Lauf, 49,8 s) | `output/M26-M33-evidence/M26-M33-final-journey/TEST-ch.so.agi.dateninfrastruktur.admin.ManagedDownloadsIT.xml` |
| `ManagedDownloadFixtureIT` | 1 | `output/M26-M33-evidence/explicit-pilot-seed/…ManagedDownloadFixtureIT.xml` |
| `DetailPageVmFactoryTest` | 27 | `output/M26-M33-evidence/protected-links-VM-regression/…DetailPageVmFactoryTest.xml` |
| `ResultsVmFactoryTest` | 3 | `output/M26-M33-evidence/protected-links-VM-regression/…ResultsVmFactoryTest.xml` |

Zusätzlich separat ausgeführt:

```text
CWD: .../workspace/dateninfrastruktur-admin
CMD: python3 scripts/test_managed_ownership.py
Exit: 0 (2 Tests, OK)
```

M26–M33-Zuordnung (jeweils `EXECUTED`, erwarteter/beobachteter Exit 0):

| ID | Beobachtung | Beleg |
|---|---|---|
| M26 | open anonym 200 mit echtem Fixture-SHA/Größe und no-store; restricted 401 ohne Identität, 403 mit Anna/Ben ohne Grant; echter Keycloak-Bearer; ungültiger Bearer 401; gefälschte Forwarded-/Actor-/Gateway-Header 403; `/internal/authorization/check` 403; fehlendes S3-Objekt ohne Teilwrite; echte streamende S3-Operatoraktivierung | E2E-XML; `missing-private-object-rollback.log`; `real-S3-operator-activation.log` |
| M27 | derselbe Anna-JWT vor/nach Approval und nach Revoke; alle vier restricted-Repräsentationen (2 Versionen × CSV/XLSX) auf beiden Gateways; Root open↔restricted sofort wirksam ohne Objektverschiebung/Reload; Ben-Direktvergabe ohne Antrag; nach Revoke GET/HEAD/conditional 403 | E2E-XML |
| M28 | HEAD 200 leer mit passender Content-Length; Content-Type/-Disposition, Accept-Ranges; Range 2–7 → 206 exakt; ETag 304; Range 416; falscher Name 404; POST 405; Rohpfade (Query, `%00`, `%FF`, Zusatzsegment, `//`, `%70`, `../`, `%2e`, `%252e`, Backslash) 400 + no-store; Gegenprobe ergänzt Trailing-Slash, Semikolon, Großbuchstaben-UUID (400) und Trailing-Dot (404) | E2E-XML; `counterexample.result.json` |
| M29 | echter synthetischer Alt-Canary vor Cutover 200 mit exakten Bytes auf beiden Altwegen; private Kopie verifiziert; eigene Website deaktiviert; beide Altwege 403; privater S3-Key mit Credential positiv, anonym 403; alter S3 403/Website 403/404; Origin-RW verweigert; kein interner Hostport | E2E-XML; `M29-old-public-cutover.log` |
| M30 | Authz-/DB-Ausfall 503 (DB auf beiden Gateways, auch open); S3-/Origin-Ausfall 5xx, nie 200; Referenzbytes nach Resume; transparenter Origin-Beobachter ohne Credential-Headernamen; Logscan ohne Token/Secret/S3-Key-ID | E2E-XML |
| M31 | zwei APISIX/Admin/Public gegen dieselbe PG; Approval-Formular von A nach B mit gleicher Session/CSRF/erlaubtem Origin; gleiche Claudia-Session 200; gültiges CSRF mit Evil-Origin 403; Grant/Revoke/Level auf A und B | E2E-XML |
| M32 | Browserfolge Suche→restricted Metadaten→OIDC→Antrag→Claudias Entscheid→Download mit SHA→Entzug→Audit; Ben-Direktgrant; Metadatenänderung auf frischem HTTP-Request beider Portale; Audit mit Claudia-Subject | E2E-XML |
| M33 | eigener Stop/Start aller Dienste auf denselben Containern/Volumes/Secrets; Snapshot (Principal/Dataset/Grant/Decision + Audit-Zeilen + Secrets) unverändert; `managed_setup` liest nur; gleiche Browser-Cookies und alte JWTs entsprechend aktuellem DB-Recht; Ownership-Negativtest bestanden | E2E-XML; `M26-M33.console.log`; `test_managed_ownership.py` |

## Übernommene Nachweise

Keine. Alle M26–M33 wurden vom Reviewer am aktuellen Kandidaten neu ausgeführt. Die früheren MA-0/MA-A/MA-B/MA-C/MA-D-Abnahmen werden nur als Phasengrundlage referenziert, nicht als Ersatz für den MA-E-Abschlusslauf; der Request verlangt ausdrücklich keinen identischen zweiten Gesamtlauf.

## Eigene Gegenprobe

**Hypothese:** APISIX/OpenResty-Normalisierung oder der Datei-Origin könnten eine *near-canonical*-URL (Trailing Slash, Semikolon-Parameter, enkodiertes Dot-Segment, doppelter Slash, Query, Großbuchstaben-UUID) auf dasselbe private Objekt abbilden, oder clientseitige Forwarding-Header (`X-Forwarded-Uri`, `X-Original-URL`, `X-Rewrite-URL`) könnten die Roh-URI-/Methodenentscheidung des Gateways überschreiben. Dann wäre ein restricted-Objekt über eine andere URL als die geprüfte erreichbar.

**Neuer Input / Kommando:** `output/counterexample_nearcanonical.py` gegen eine frische eigene minimale Laufzeit (Setup, Fixture, Start, Upload, Aktivierung) mit eigenem PG-Container und zufälligen Loopbackports; `http.client` sendet den Request-Target verbatim (keine Client-Normalisierung). Nur lesende GET/HEAD.

```text
python3 output/counterexample_nearcanonical.py .../workspace/dateninfrastruktur-admin/.runtime/managed-test
```

**Erwartung:** kanonischer open-Pfad 200 mit Fixture-SHA und no-store; HEAD 200 leer; anonymes Range 206 mit exakten Bytes; jede near-canonical-Variante 400 oder 404 und nie das Objekt; Header-Spoofs 401/403; beide Gateways gleich.

**Beobachtung:** 30/30 Prüfungen bestanden auf beiden Gateways: kanonisch 200 (SHA256 `3fb9532244904964a033d947c9f21850d9022f52689bef8694ade4421e117f43`), HEAD 200 leer, Range `bytes=0-3` → 206 mit `6a616872`; Trailing Slash, Semikolon, `%2e`, doppelter Slash, Query und Großbuchstaben-UUID → 400; Trailing-Dot → 404; `X-Forwarded-Uri`/`X-Original-URL`/`X-Rewrite-URL`-Spoofs → 401; `failures: []`. Eine erste Probefassung schrieb versehentlich die Dataset- statt der Distribution-UUID groß und erzeugte einen falschen 200-Treffer; sie wurde vor dem gültigen Lauf korrigiert. Beleg: `output/counterexample.result.json`, `output/counterexample.console.log`.

**Schlussfolgerung:** Die Probe widerlegt die Hypothese; es gibt keinen gefundenen Normalisierungs- oder Header-Bypass. Die kanonische URL bleibt die einzige, die das Objekt liefert.

## Findings

Keine BLOCKER/MAJOR/MINOR-Produktfehler. Nicht blockierende Hinweise (keine Abnahmehinderung):

- Der M33-Snapshot-Digest umfasst Principal/Dataset/Grant/Decision-Zeilen und die Audit-Zeilenzahl; Version-/Distribution-Metadaten werden funktional über die Downloads nach dem Neustart geprüft, nicht per Digest. Für die geforderten Kategorien ausreichend; eine engere Digest-Härtung wäre möglich.
- `managed_control.storage_boundaries` verwendet für den Textmodus-`rclone cat`-Positivnachweis `fixture.files[0]` und setzt damit CSV an erster Stelle voraus; im deterministischen Fixture korrekt, aber an die Fixture-Reihenfolge gekoppelt.
- Im Docker-Daemon verbleiben **vorbestehende, gestoppte** Demo-Ressourcen aus dem Implementierungslauf (`di-ma-e-08e45fc8579a-*`, `di-ma-b-e77f1f71a817-private`). Sie wurden vom Reviewer bewusst nicht verändert.

## Integrität und Grenzen

- **Produkt unverändert:** Alle getrackten Dateien der drei Repositories sind vor und nach beiden Testläufen byte-identisch; kombinierte Manifeste `product-before.sha256 == product-after2.sha256 == 7128b7f56035bc73bc29c2e43499ddf1e6bef78a1e1689ac16bc3a390b1a8c9e`. Alle Working Trees sind clean; die HEADs entsprechen exakt dem Handoff.
- **Eigene Ressourcen:** Keine laufenden Reviewer-Container, -Volumes oder -Netze verbleiben. Der Hauptlauf und die Gegenprobe räumten ihre eigenen, label-/ID-geprüften Ressourcen über die Produkt-Cleanup-Pfade ab. Die oben genannten vorbestehenden Demo-Ressourcen sind nicht Teil dieses Reviews.
- **Ignorierte Testartefakte:** Die sensiblen Laufzeitdateien der Gegenprobe (State, Realm-/Rclone-/Garage-Konfiguration, Rollen-/Fixture-/Token-Dateien) wurden nach der Gegenprobe aus dem isolierten ADMIN-`.runtime` entfernt. Es verbleibt nur der ignorierte Tool-Cache (`tools/`); Container/Volumes/Netze sind entfernt. Nicht Produktbestand, nicht Teil des Handoffs.
- **Grenzen:** Nur lokales HTTP auf Loopback; TLS/Secure, Produktionsdeployment, zentrale Kontosperrung, persönliche ClickHouse-/Superset-Rechteprojektion und Rechtszertifizierung bleiben außerhalb dieser Abnahme. Externe öffentliche Originale werden nicht als durch die lokale Berechtigung geschützt behauptet. Alle Dateien sind synthetische lokale Pilotkopien.
