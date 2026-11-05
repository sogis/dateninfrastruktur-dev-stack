# MA-G0 – tatsächlich gelesener Ausgangsstand

Inventur am 5. November 2026, vor Produkt-/Datenumstellung. Kein Reset/Push.

| Repo | Branch | Ausgangs-HEAD | Dirty-State vor G0 |
|---|---|---|---|
| STACK | main | 8ee609cff186f80472f54356ec5e493661670d93 | Nur ungetrackte historische c001–c005-Kandidaten/c001–c003-Reviews unter grundinstallation; erhalten |
| ADMIN | main | 6009fb04063f16fcdb2ea6b3d9153e9553c9e4f1 | sauber |
| PUBLIC | main | b1f20075be43eb4d0edf771ee1440ea0e30e1801 | sauber |
| PLUGIN | main | 579f3fd54432a977122afb186469fbb40d95322f | sauber |
| JENKINS | main | 08931fa8254d096e2addcd3aee97bc1b753f087d | sauber |
| TOPICS | main | 6b0b635f066dc8de5000e3e549b983fb772dfb33 | sauber |

Alle sechs Remotes sind die bestehenden `https://github.com/sogis/<reponame>.git`.
Keine weiteren lokalen Branches in diesen Repos. ADMIN war vorhanden und wurde
nicht neu angelegt. Mutterordner bleibt ohne Gitrepo. Benachbarte Projekte,
`datenportal-*`-Quellen und vorhandene ungetrackte Historie werden nicht geändert.

## Lokale Laufzeit – nur lesend geprüft

Aktives kanonisches Composeprojekt `dateninfrastruktur`, zehn Dauer-Services.
Bestehende Containerzuordnung wurde über `ComposeContext.verify_project()` gegen
Workspace/Composepfad und `di.instance` geprüft. Sichtbare Hostports: Gateway
18081, Keycloak 18080, Superset 8088, CH 8123/19000. Admin/Origin/PG/Jenkins/Garage
haben keine eigenen publizierten Hostports. Volumes bleiben unverändert; auch
fremde und offline gehaltene MA-F-Originalvolumes werden nicht bereinigt.

PG: vier Datasets/vier Ausgaben/acht Versionen/16 Distributionen, vier Principals,
zehn AuthorityAssignments, vier AccessGrants, sechs AccessDecisions, zwei Anträge,
acht CatalogActions, 208 Auditzeilen. Kein DataSchema/AttributeDefinitionbestand.
Management-Tabellen-/Sequenz-/Rechtecheckpoint (kanonische Zusammenfassung):
`541b6b699e7c9fdc8c828f87d84a27283c0abf1b4be0743a1396dbcf44613679`.
Die komplette lesende Prüfbasis liegt privat im aktiven Runtimeverzeichnis
`ma-g0-inventory/`; keine Dumps/Principalinhalte im Reviewhandoff.

Jenkins: acht Jobs über authentifizierte lesende API inventarisiert. Die konkreten
Namen liegen privat; G3 muss Eigentümerschaft/Marker pro Job belegen. Home und
fremde Jobs bleiben erhalten. Keycloak-/Jenkinsidentitäten wurden nicht verändert.

Garage: `ch.so.daten` enthält vier alte Entwicklungsobjekte (510021 Bytes).
`di-managed-private` enthält 17 Dateien (13787 Bytes) und 18 virtuelle
Verzeichniseinträge; PG referenziert insgesamt
16 Distributionen. Alle 16 referenzierten Keys sind im Quellbucket vorhanden;
eine weitere Datei bleibt bis zur Herkunftsprüfung geschützt. Ein weiterer lokal aliasierter Bucket enthält ein Objekt
(51 Bytes). Dies ist **kein** Beleg, dass unbekannte Objekte gelöscht werden dürfen.
G1 muss Referenzen, technische Canaries und verbleibende unbekannte Objekte
konkret zuordnen. Bucket-IDs, Keys, Pfade und Detailinventuren bleiben privat.
Kein Objekt wurde in G0 verändert, kopiert oder gelöscht.

## Tatsächliche Implementierungen

TOPICS hat vorhandene reale CsvValidator-Tasks und DuckDB-CSV/XLSX/Parquet-
Exportbausteine. In den sechs lokalen Branches und Dirty Trees wurde kein
S2-ClickHouse-Lader gefunden. Eine alte Spezifikation und ein README-Satz sind
kein Codebeleg. G4 ergänzt den fehlenden Snapshotwriter im selben Runner.

ADMIN: Spring Boot 4.1.2, Java25, Cayenne Runtime/Buildtools 5.0-M3.
Jenkins/Plugin: Core 2.555.2, Java21; GRETL Java17.0.15 im vorhandenen Image.
Echter G03-Lauf meldet ilivalidator 1.15.0 (27cd81f), ili2c 5.6.8 (e6f7ab6),
iox-ili 1.24.4 (8e966a0). GRETL-Koordinate 5.0.0-SNAPSHOT; tatsächliche
JAR-/Taskhashes müssen den Snapshot unabhängig vom beweglichen Namen binden.
Keine Framework-/ORM-/Engineänderung.

OpenCode Desktop-CLI: tatsächlich `opencode v2.2.5`; vorhandene Modellliste enthält
`deepseek/deepseek-flash`. Ein eigener lesender Providerzugriff beantwortete die
Probe mit READY (Session `ses_e5403b154ffeN9bnjLGbdCtvtw`). Dies ist ein
Zugriffsnachweis, **keine** unabhängige Phasenabnahme. Die folgt separat am
committeten, isolierten Kandidaten.

## G0-Proben und offene Gates

G01: neuer zentraler MA-G-Phasenvertrag/Specpfad/Runtime, alle sechs Repos,
aktuelle Workspacevorlage und sämtliche JSON-Verträge werden gebunden.
Gate-Negativregression und Routing-/Hashprobe ausgeführt.

G03: echter GRETL-CsvValidator mit vorhandenem
`SO_Bevoelkerung_Altersstruktur_20261015` (SHA256
`09438e64baae5701e3ecf0a4ca2b19419207c2223968d6416864f1fd61130a48`).
Gültige CSV positiv, falscher Zahlentyp und fehlendes Pflichtfeld real negativ.
Transitive ILI-Abhängigkeit: nur Compilerbuiltin INTERLIS. Keine Online-Modellwahl.

G02: echter Browser-Codeflow mit PKCE S256, aktueller Jenkinsuser →
OicCredentials.getAccessToken() → kryptografische Prüfung durch den echten
ADMIN-ManagementJwtDecoder. Positiv 200, falsche Audience 401, anderes Subject
403. Der Token bleibt im Speicher. Eigene PG-/Keycloak-/Jenkinsproben wurden
anschliessend entfernt; keine Nutzerkonfiguration verändert.

Die unabhängige Phasenabnahme steht noch aus. Keine Behauptung einer bereits implementierten G1–G5-
Funktion, kein lokaler Cutover aus Testcontainern abgeleitet.
