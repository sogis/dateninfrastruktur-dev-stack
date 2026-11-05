# MA-F: verifizierter lokaler Endzustand

**IMPLEMENTATION_ACCEPTED · LOCAL_CUTOVER_VERIFIED · RETIRED**  
Abschlussprüfung: `2026-11-05T01:57:04.352014+00:00`.

MA-F0 bis MA-F4 sind unabhängig durch OpenCode 2.2.5 mit
`deepseek/deepseek-flash` (vorhandener DeepSeek Flash 1017) abgenommen.
Der lokale Cutover wurde tatsächlich ausgeführt und anschliessend am übernommenen
Ziel vollständig geprüft. Kein offener Retireauftrag.

## Laufender Verbund

Ein aktives Composeprojekt **`dateninfrastruktur`** mit genau zehn gesunden
Dauer-Services: postgres, keycloak, garage, origin, gateway, sodata, admin, jenkins,
clickhouse und superset. Keine aktive Legacy-/Probe-/Doppelinstanz, kein HA.
Der gesamte Dockerbestand wurde abgeglichen: diese zehn laufenden Container und
zwölf unveränderte, zuvor bereits gestoppte fremde Container; keine weiteren
Testcontainer. Alle zehn Zielcontainer wurden bei der Endabnahme tatsächlich
neu erstellt (`down` ohne -v, danach öffentlicher `up --skip-build`).

- [Portal und Management](http://localhost:18081/)
- [Keycloak](http://localhost:18080/)
- [Superset](http://localhost:8088/)

Ein nativer PostgreSQL **16.10** / PostGIS **3.5.2** auf einem neuen benannten
Zielvolume führt `keycloak`, `superset` und `dateninfrastruktur_management`.
Anwendungskonten bleiben getrennt. Die beiden alten PGvolumes wurden nicht binär
vermischt oder im Image umgestellt.

## Tatsächliche Übernahme und Erhaltung

Die eindeutig inventarisierten 20 ursprünglichen Container wurden kontrolliert
pausiert, vollständig gesichert und nach erfolgreicher Endprüfung exakt entfernt,
ohne Volumenlöschung. Alle **zehn Originalvolumes** sind weiterhin vorhanden;
sechs werden im Ziel weiterverwendet, vier bleiben offline als Rückfallbestand.
Das neue PGvolume kommt zusätzlich hinzu. Zwölf fremde Container sind nach ID,
Name und Zustand unverändert geblieben.

Drei nichtleere Datenbanken wurden logisch restauriert. Owners, ACLs, Rollen,
Sequenzen und Sicherheitskatalog wurden verglichen. Der aktuelle H2-Keycloak-
Zustand wurde nach sauberem Stop gesichert und mit demselben Image offline
exportiert; Benutzerzuordnungen erfolgten anhand belegter UUIDs. Aktuelle
Principalbindungen wurden auditiert auf den stabilen Zielissuer umgestellt;
historische Akteurssnapshots blieben erhalten. Foundation-Anwendungscredentials
und Superset-SECRET_KEY wurden übernommen.

Alle **107 ursprünglichen Auditzeilen** sind auch nach den neuen Zielschreibvorgängen
inhaltlich unverändert (kanonischer Prefixhash). Die vier bestehenden Principals
bleiben dieselben. Die acht ursprünglichen aktuellen/historischen Dateien liefern
identische Bytes: vier offene Dateien anonym positiv, vier eingeschränkte anonym
401; bestehende wirksame und widerrufene Rechte jeweils 200 beziehungsweise 403.
Alle neun übernommenen S3-Objekte einschliesslich Canary wurden mit Bytes und
Metadaten abgeglichen. Nicht verwaltete Foundation-Artefakte bleiben im Garage-
Bestand; die alten direkten Manifest-/Downloadrouten sind bewusst geschlossen.

Jenkins erhält sein Home, dieselben acht Jobs und den vorhandenen Zugang. Eine
harmlose echte GRETL-/Gradle-Ausführung wurde geprüft, keine Lieferung publiziert.
Die zwei ursprünglichen ClickHouse-Tabellen mit sieben Zeilen haben identische
vollständige Zeilen-/Schemaprüfsummen. Superset benutzt weiterhin seine bestehende
verschlüsselte ClickHouse-Verbindung, vor und nach Recreate tatsächlich getestet.

Die ausdrückliche Endabnahme legte zwei zufällig als `maf-f4-*` gekennzeichnete
Prüfdatensätze mit eigenem Prüfamt und Dateien an; normale Starts legen sie nicht
an. Vorhandene Datensätze und Freigaben wurden dafür nicht verändert. Daher gibt
es jetzt vier Datensätze, vier Principals, vier Grants und sechs Decisions; die
208 Auditzeilen umfassen die unveränderten 107 Altzeilen sowie die auditierten
Migrations-/Prüfvorgänge. Die Prüfdaten und ein deaktivierter Client-Sentinel
bleiben als bezeichnete Nachweise erhalten.

## Endabnahme und unabhängige Prüfung

Am echten lokalen Ziel und unabhängig an eigenen Quellen bestanden:
PKCE-Codeflow über den normalen vertraulichen Gatewayclient, sichtbare
Metadatenänderung, Antrag → Genehmigung → Download → Widerruf mit **demselben noch
gültigen Ziel-JWT** → Audit. Aktuelle/historische CSV/XLSX, HEAD/Range/ETag,
Pfad-/Headerangriffe, interne API, Authorization-API-Ausfall 503 und anschliessende
Erholung sind geprüft. Der kurzlebige Compose-Beobachter empfing keine
Credential-Header; normale Routebytes wurden exakt wiederhergestellt.

Nach Neuerstellung: gleiche Daten-, Audit-, Sequenz-, Identitäts- und Secrethashes,
frisches Login, aktive/widerrufene Rechte und Dateien; zusätzliche Metadatenänderung
mit weiterlaufender Auditsequenz. Der unabhängige Reviewer prüfte zusätzlich den
Ausfall nach bereits erfolgreichem privatem Zugriff für berechtigte, widerrufene
und anonyme Anfragen: kein Fail-Open und kein Autorisierungscache-Bypass.

Codekandidat F4: STACK `3990dab347a2b48a9a17c714eeb118928e07f259`,
ADMIN `6009fb04063f16fcdb2ea6b3d9153e9553c9e4f1`; übrige SHAs und Bindungen stehen
im [unabhängigen F4-Bericht](review/MA-F4-accepted.md). Alle vier Pflichtprüfungen
sind dort frisch `EXECUTED/PASS`, keine übernommene Abnahme. Die nachfolgende
Dokumentationsablage ändert keinen abgenommenen Produktcode.

Ein festhängender erster F4-Modellversuch wurde ohne Urteil geschlossen. Im
abschliessenden unabhängigen Lauf wurden checkout-äquivalente Leserechte in der
isolierten Arbeitskopie hergestellt, nachdem ein restriktiver vererbter Umask den
Supersetstart blockiert hatte; keine Dateiinhalt-/Git-Modusänderung. Ein reiner
JSON-Formatfehler der INFO-Findings wurde durch denselben unabhängigen Reviewer
korrigiert; erfolgreiche Tests wurden dafür nicht wiederholt. Das Standardgate
validiert den korrigierten Bericht samt tatsächlichem Modell/Session und
unverändertem SHA-Satz. Keine BLOCKER/MAJOR/MINOR-Findings.

## Private Referenzen und Betriebsgrenze

Plan-SHA256: `a857dac15466e14b850bec7039d12fb2666e28a8d934c1731cd3e918b2a4301b`. Konkrete Quell-IDs, Secrets und Daten
stehen ausschliesslich in geschützten Runtimeartefakten:

- `.runtime/consolidation/migration.json`: unveränderlicher eigener Plan.
- `.runtime/dateninfrastruktur/migration/`: drei Dumps, Rollen-/Identitäts-/Storage-
  Checkpoints, H2-Originalbackup und finales Journal.
- `.../retirement/manifest.json`: 20 verifizierte vollständige Dateisystemexporte,
  Konfig-/Bindarchive und Originalvolumenmanifest; privater Recovery-Compose.
- `.../final-verification.json`: tatsächlicher Endbestand und gebundene Prüfnachweise.
- `.runtime/compose-review/MA-F4/20261105T013710Z/ACCEPTED.json`: finales Phasengate.

Archive und Originalvolumes bleiben erhalten; endgültige Speicherbereinigung ist
nicht Teil von MA-F. Neue auditierte Zielwrites existieren: die ursprüngliche
Rollbackbaseline wurde absichtlich nicht ersetzt. Ein simpler Rückfall muss deshalb
vor jedem Stop mit `ROLLBACK_UNSAFE` verweigert werden; zuerst aktuellen Zielzustand
sichern und eine ausdrückliche Rückübernahme planen. Siehe
[Betrieb](../../operations.md) und [Migration/Rückfall](../../migration-ma-f.md).
