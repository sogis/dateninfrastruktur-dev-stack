# Reviewrequest MA-E — private Downloads und abschliessende Integration

- ADMIN base: `bae39316946d09d285d2ae9e89bd68d459d87d4f`
- STACK base: `0cbeb8d29f9770fda91ec3361a68b9a18cb34ef3`
- PUBLIC base: `b17595f08f040bd66a470b5152a868cc9785e94a`

MA-D ist unabhängig ABGENOMMEN (20261104T182312Z), gebundener Bericht
MA-D-accepted.md. Diese MA-E-Abnahme ist zugleich der Gesamtintegrationsreview.
Keine identische zusätzliche Schlussprüfung nach Abnahme vorgesehen.

## Änderung → Risiko → neue Prüfung

ADMIN ergänzt den verwalteten Modus des vorhandenen Identity-/PGharnesses:
eigener .runtime-Bereich, zwei APISIX/Admin/Public, eine primäre PG16-DB,
private Garage und rclone-Origin. Kein Umbau/Reload der Nutzer-Foundation,
keine Original-.env, keine Änderungen an Jenkins/ClickHouse/Superset. Nur eigene
zufällige Loopback-Gatewayports; nach explizitem Erstsetup gleicher PGdatenbestand
und gleiches Volume ohne Hostport. Stop/Restart behalten Daten und Secrets.
Start vergibt nie Testrechte. Explizites Setup prüft vorhandenen privaten aktuellen
Vertrag lesend ohne DDL; unbekannter Fingerprint bleibt unberührt.

APISIX3.19.0-Standardplugins: OIDC vor forward-auth; optionaler Downloadlogin,
Java prüft Access-JWT unabhängig. Festes internes Servicecredential, keine
clientseitigen Actor-/Forwarded-Übernahmen. **Im laufenden Image reproduziert:**
APISIX ersetzt request_uri in init.lua durch normalisierte URI. Deshalb gibt
forward-auth.extra_headers ausdrücklich `$real_request_uri` weiter. Ein fester
Standard-fault-injection.abort über real_request_uri verwirft mehrdeutige
Rohpfade auch vor einer sonst auf andere Routen führenden Normalisierung.
Keine Lua-Funktion/-Datei, kein APISIX→PG, kein Casbin-/Policyexport.

Origin rclone1.75.2 WebDAV mit echtem ETag/HEAD/Range, read-only, feste private
Bucket-/downloads-Basis, kein Listing/ZIP/DAVschreiben, keine Hostports, kein
Datei-/Directorycache. Garage kann Bucket-ACL, keine behauptete native Prefix-IAM.
Eigenes RO-Origincredential, RW ausschliesslich lokaler Operator. Authz entfernt
per geprüftem Standard-upstream_headers-Mechanismus Identitäts-/Cookie-/Gateway-
Header vor Origin. Alle Antworten der verwalteten Gateways no-store.

RclonePrivateObjectVerifier/ManagedDeliveryCommand: explizite scoped Aktivierung,
RuntimeContractVerifier, tatsächliche private S3bytes streamen→Hash/Grösse,
begrenzter Prozess, keine URL-/Upload-/Streaming-Webroute. Verifikationsfehler
rollt vorbereitete Datei, Rootrevision, Audit und Receipt vollständig zurück.
Die Verträge/Modelle/Migrationen/ORM/JWT-/Authz-SQL bleiben unverändert.

BrowserOriginFilter erweitert den festen Originvertrag auf zwei explizit
konfigurierte Origins. Cookie-CSRF bleibt aktiv. Tatsächliches A-Formular→B-POST
mit gleichem Cookie/CSRF, gleicher Browserkontext über beide Gateways, fremder
Origin mit gültigem CSRF verweigert. Kein Wildcard-CORS. Lokales HTTP nur Loopback;
TLS-/Secure-/Produktionskonfiguration bleibt dokumentierte Betriebsgrenze.

PUBLIC markiert DB-Distributionlinks als gatewayProtected zur Darstellung.
Auch restricted Links bleiben anklickbar; das ist kein personenbezogener
Rechtscache. Legacykonstruktoren/-Links behalten ihr Verhalten. Dateistreaming
und Schreiblogik bleiben ausserhalb PUBLIC.

## Selbst auszuführender Abschlusslauf

Aus STACK `./scripts/management/test.sh --phase MA-E` oder aus ADMIN
`python3 scripts/test_downloads_all.py`. Ein einziger abschliessender Durchlauf,
keine Wiederholung der unveränderten früheren Gesamtsuiten.

Der Runner braucht einen frischen eigenen .runtime/managed-test-Bereich und
stoppt bei bereits vorhandenem Zustand statt ihn zu ersetzen. Eigene gelabelte
Container/Netze/Volumes, zufällige Ports, private Schreibpfade/Secrets. Kein
--keep-runtime beim normalen Review: finally entfernt ausschliesslich geprüfte
eigene Ressourcen. Verbleibende Originalsourcen/Nutzercontainer bleiben erhalten.
Die gewünschte Testmenge wird über reale JUnitklasse/Skips/Exitcode geprüft.
Belege unter ADMIN/.runtime/download-evidence/<UTC>/, ohne Credentials.

| ID | Neue tatsächliche Prüfung |
|---|---|
| M26 | ManagedDownloadsIT: echte private CSV und gültige XLSX, open anonym Hash/Bytes, restricted401 ohne Identität/403 ohne Grant, realer Keycloak-Bearer; vollständige S3verifizierte Operatoraktivierung; negative fehlende Datei ohne Teilwrite |
| M27 | gleicher weiterhin gültiger Anna-JWT vor/nach Approval/Revoke; alle vier historischen restricted Dateirepräsentationen (2 Versionen × CSV/XLSX) auf beiden Gateways; Root open↔restricted ohne Objektverschiebung/Config-/Policyreload; Ben-Direktvergabe ohne fiktiven Antrag |
| M28 | echte HEAD/GET, Content-Length/-Type/-Disposition, Accept-Ranges, Range206 exakt erwartete Teilbytes, ETag304, Range416; nach Revoke HEAD/conditional403; raw Socket-HTTP für Kodierungen, Zusatzsegmente, doppelte Slashes, Dotsegmente, Backslash, Querys, falscher Name/Methode |
| M29 | tatsächlicher zuvor öffentlicher Canary über beide alten Gateways200 und erwartete Bytes, private Kopie verifiziert, eigene Website deaktiviert und beide alten Routen403; credentialed gleicher privater S3key positiv, anonymous403; alter S3key403/Website404 nach Cutover; Origin-RWversuch verweigert, kein interner Hostport |
| M30 | gezielte eigene Authz-A-/PG-/Garage-/Originpause mit festen Timeouts, 503 bei Authz/PG auch open, S3/Origin nur Serverfehler ohne Download200, Referenzhash nach Resume; transparenter Test-Originobserver misst Headernamen statt sie zu bereinigen, tatsächliche credentialfreie Requests; Scan eigener Logs gegen Tokens/Secrets ohne Werteausgabe |
| M31 | beide tatsächlichen APISIX-/Admin-/Publicinstanzen gegen dieselbe primäre DB; jede Grant-/Revoke-/Levelprobe auf A/B, gleiche Browsersession; echtes Formular/CSRF von A an B, gültiger CSRF mit Evil-Origin403 |
| M32 | echte Browserfolge Suche→restricted Metadaten→OIDC→Antrag→Claudias Entscheid→Dateidownload mit Hash→Entzug→Audit; Ben-Direktgrant, Metadatenänderung auf frischem HTTPrequest beider Portale sichtbar; Audit mit realem Claudiasubject |
| M33 | eigener Stop/Start aller Dienste bei gleichen Containern/Volumes/Secrets, Daten-/Principal-/Grant-/Decision-/Auditdigest unverändert; explizites Setup des privaten aktuellen Vertrags liest nur; gleiche Browsercookies und alten JWTs nach Neustart wirksam entsprechend aktuellem DBrecht |

ManagedDownloadFixtureIT richtet ausschliesslich ausdrücklich gewählte synthetische
Office/Manager/Serviceactor/Ben-Identität sowie prepared Dateien ein. Kein fake
Verifier: Fixturecallback wirft, Aktivierung erst nach tatsächlichem S3-/Cutover-
Nachweis. Registrierung über die abgenommenen Fachservices/AuditedUnitOfWork.
Zusätzlich nur betroffene PUBLIC ResultsVmFactoryTest/DetailPageVmFactoryTest.
Kein pauschaler Foundation-/WebR-/ClickHouse-/Superset-/Modellneubau.

## Lokale Ergebnisse und Grenzen

Ein vollständiger M26–M33-Lauf samt betroffener VMregression ist erfolgreich
(ADMIN/.runtime/managed-final-second.log, Belege20261104T184732Z). Die zuvor
reproduzierte Restartlücke war fehlende Keycloak-Readiness trotz schon erreichbarem
Portal; Start wartet nun auch auf Discovery und JWKS. Der erfolgreiche Lauf
beweist gleiche Browsersitzung und unveränderte Daten/Secrets nach Restart.
Der letzte Kandidatenlauf ergänzt explizite fehlende-S3-Verifikation/Txrollback
und verlangt bei Origin/S3ausfall konkret 5xx; sein Ergebnis wird vor Commit
unten ergänzt. Keine Erwartungsabschwächung oder Schein-PASS.

Eigene neue Reviewer-Gegenprobe und vollständiges Code-/Zielreview bleiben
Pflicht. Keine Produktreparatur durch Reviewer. Lokale Code-/Daten-/Ressourcen-
Isolierung und Workspace-AGENTS-Hash müssen bestätigt sein.

Betrieb: STACK README und ADMIN/docs/managed-downloads.md, eigene Setup-/Start-/
Stop-/Status-/Restart-/Aktivierungskommandos. Kein Push/Release, keine externen
S3-/Produktionsänderungen. Keine Native-/Rechtszertifizierung, kein zentraler
Kontosperr-Lifecycle und keine persönliche ClickHouse-/Superset-Rechteprojektion.
Alle Dateien sind synthetische lokale Pilotkopien; externe Originale bleiben
öffentlich und werden nicht als geschützt bezeichnet.

Zusätzlicher echter Reproducer vor Kandidat: rclone cat allein kann für einen
fehlenden exakten Key erfolgreich ohne Bytes enden. Das wurde mit tatsächlicher
Fehlaktivierung als leere Datei reproduziert, nicht als PASS gezählt. Verifier
prüft jetzt zuerst `lsjson --stat`: genaues Name/IsDir=false/Size-Metadatum,
Erfolgscode, begrenztes Metadatenvolumen und Timeout. Danach tatsächlicher
Bytestrom und Übereinstimmung mit stat-Grösse. Fehlender Key wird neu zuverlässig
verweigert; die gezielte Wiederholung belegt vollständig unveränderte Datei,
Rootrevision, Audit- und Receiptzahlen. Der frische finale Runner enthält diesen
Negativfall vor jedem Upload und danach den positiven echten S3-Apply.

HTTP-Parse-Reproducer vor Kandidat: `%00` wird von OpenResty bereits vor den
Plugins mit400 abgelehnt. Daher ergänzt die geprüfte Standard-Nginx-Direktive
`add_header Cache-Control no-store always;` auch diese frühen Fehlerantworten;
kein Lua. Echte Socketgegenprobe nach Reload zeigt400 plus no-store. Separate
gezielte Garage-/Originpause liefert jeweils504/no-store, danach denselben
positiven Objekt-SHA. Der finale zusammenhängende Lauf enthält die Prozent-NUL-
und ungültige-UTF8-Probe sowie die strikte 5xx-Ausfallprüfung.

Der finale Logscan umfasst ausdrücklich auch S3-Access-Key-IDs. Ein echter
Reproducer fand diese IDs im Garage-Info-Requestlog (keine ausgegebenen
Passwörter/JWTs). Deshalb Garage explizit RUST_LOG=warn, keine Abschwächung des
Scans und keine Credentialzeilen im Report. Gateway behält begrenzte URI-/Status-
Diagnose. Die neue Runtimekonfiguration wird vor Abgabe frisch integriert geprüft.

Finaler lokaler Kandidatennachweis: `python3 scripts/test_downloads_all.py
--keep-runtime --keep-failed-runtime` vollständig erfolgreich (managed-final-sixth.log,
Belege20261104T190004Z): fehlendes S3objekt mit vollständigem Rollback verweigert,
Upload/Cutover/verifizierter Apply, M26–M33 mit striktem5xx, Rohpfad400/no-store,
Key-ID-/Secret-/JWTlogscan0, alle JVM-/Browser-/Restartfälle und VMregression0.

Anschliessender enger Lifecycle-Schutz: Start/Stop vergleichen den gespeicherten
DBcontainer zusätzlich mit dem durch Namen/Label verifizierten DBzustand;
Netzwerkbesitz wird vor Start/Join/Rclone/Operator geprüft. Abweichende IDs
verweigern den Eingriff. Neue test_managed_ownership.py-Proben bestehen, tatsächlicher
idempotenter Start/Stop der eigenen behaltenen Laufzeit ebenfalls. Keine Änderung
an HTTP-/Authz-/S3-/Fach-/Transaktionslogik in diesem letzten Schutzdelta; der
Abschlussrunner führt die zwei Negativproben mit aus. Kein weiterer lokaler
identischer E2Elauf allein wegen dieser Abbruchbedingungen.
