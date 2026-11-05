# Lokaler Endcutover MA-G

**`LOCAL_CUTOVER_VERIFIED`**, 6. November 2026 (Europe/Zurich).
Der [unabhängig abgenommene Kandidat](review/MA-G5-accepted.md)
`20261105T233409Z` wurde im bereits bestehenden lokalen Compose-Projekt
`dateninfrastruktur` gestartet. Das unabhängige Review nutzte eigene
Checkouts, Testcredentials und synthetische Daten. Der folgende Nachweis
bezieht sich ausschliesslich auf die reale lokale Instanz.

| Prüfung | Vorher und nachher |
|---|---|
| Dienste und Volumes | Zehn gesunde Dienste im selben Projekt. Die benannten persistenten Volumes sind identisch. Admin, Sodata, Jenkins, PostgreSQL und Superset starteten mit den geprüften Images; die übrigen Dienste behielten ihre Container. |
| PostgreSQL | Die 16 bestehenden Fachtabellen wurden mit identischen Altspaltenwerten übernommen. Der Fingerabdruck wechselte von `354516ea…` auf `a7beb105…`; SQL-Mapping und Auditabdeckung wurden separat geprüft. |
| Identitäten und Rechte | Vier bestehende Principals und die fünf verglichenen Keycloak-Identitätstabellen stimmen für alle bisherigen Identitäten überein. Zehn Autoritätszuweisungen und vier Dateifreigaben sind unverändert. Neu ist der explizit registrierte technische Executor; kein neuer Fachgrant. |
| Audit | Alle 208 bisherigen Zeilen stimmen mit der Vorinventur überein. Eine neue Zeile protokolliert die Registrierung des technischen Principals. |
| Private Objekte | Alle 16 referenzierten Dateien (13 756 Bytes) wurden vor und nach der Umstellung über den gebundenen privaten Writer gelesen. SHA-256, Grösse, Content-Type, Objektmetadaten und ETag stimmen überein. `ch.so.daten` bleibt privat, mit getrenntem Reader und Writer. Der [einmalige G1-Purge](LOCAL_STORAGE_CUTOVER.md) wurde nicht wiederholt. |
| Abruf mit denselben Tokens | 48 Beobachtungen identisch: 32 × HTTP 200 mit identischen Dateibytes, 8 × 401, 8 × 403. |
| Jenkins | Acht eindeutig markierte Jobs samt Buildhistorien und elf zugehörige Altobjekte wurden offline archiviert. Genau `di-csv-ingest` ist aktiv. Installiertes HPI und OIDC-Plugin stimmen mit den gebauten Hashes überein. Der bestehende lokale Benutzer erreichte die Anlieferungsseite mit OIDC; der separate Operator-Notfallzugang wurde über das native Formular geprüft. |
| Foundation | Die beiden vorhandenen ClickHouse-Tabellen und fünf Superset-Tabellenprüfsummen stimmen mit der Vorinventur überein. Kein erneuter Lauf oder Reset der separaten ClickHouse-Ladeimplementierung. |

Vor der Übernahme wurden laufende und wartende Jenkinsbuilds ausgeschlossen;
Gateway, Admin, Sodata und Jenkins wurden kontrolliert gestoppt. Die
Managementdatenbank wurde vor dem Upgrade einmal privat gesichert. Der
abgenommene Keycloak-Provisioner stoppte zunächst, weil der bestehende Realm
dem neuen Executor-Client zusätzlich `service_account` zugewiesen hatte.
Entfernt wurde nur diese eine Zuordnung am frisch angelegten, über Marker,
ID und Secret eindeutig gebundenen Client. Die erneute Prüfung bestätigte
`roles` als einzigen Standardscope, die erwarteten Tokenrollen und den
gebundenen technischen Subject. Andere Clients und ihre Rechte wurden nicht
geändert.

Der vollständige Browser-Upload bis zur realen Veröffentlichung wurde im
unabhängigen G5-Lauf nachgewiesen. Auf der Nutzerinstanz wurde der lokale
Start, der neue OIDC-Einstieg und der unveränderte Zugriff auf bestehende
Dateien geprüft. Es wurden dort keine synthetischen CSV-Lieferungen,
Fachdatensätze oder Grants angelegt. Neue Datensätze werden über den
[regulären Bedienweg](../../operations.md) für die Anlieferung freigegeben.

Private Nachweise: `.runtime/dateninfrastruktur/ma-g5-cutover/`.
Die einmalige Schemaübernahme liegt ausserhalb der Defaultimages, aktiven
Compose-Profile und des allgemeinen Bedienwegs. Der abgenommene Quellstand
bleibt im Review gebunden. Keine Änderungen an externem Storage, kein Push,
Merge oder Release.
