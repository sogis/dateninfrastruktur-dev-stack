# MA-F – Abnahme und risikobasierte Regression

Dieser Testplan gehört zum Gesamtauftrag. Er beschreibt **Verhalten**, nicht nur Dateiexistenz oder einen grünen Containerstatus. Die aufgeführten Prüfungen sind auf fünf Phasen verteilt; sie sind keine nach jedem Fix vollständig auszuführende Testsuite.

## 1. Grenzen des Tests

Implementierung und Reviewer verwenden eigene Projekt-/Port-/Volume-/Secret-/Runtimepfade. Tests dürfen das reale Nutzerprojekt nicht stoppen, migrieren oder reinigen. Der spätere kontrollierte lokale Cutover ist eine gesonderte Operatoraktion des Implementierers mit validiertem Plan.

Finale Tests verwenden **dieselbe `compose.yaml`, dieselben Builds, Templates und Setupwerkzeuge wie der normale Start**. Ein Testoverride darf lediglich Isolation, Zielports, Fixtureeingaben und vorübergehende Messung ändern. Keine zweite handgeschriebene Anwendungsarchitektur und keine direkte `docker run`-Kopie des Produktstacks als Abnahmenachweis.

Für eine Migrationsprobe dürfen kurzlebige Quellfixtures die frühere Zweiquellenlage darstellen. Sie werden explizit als solche bezeichnet und nach dem Lauf beseitigt. Sie sind weder HA noch Bestandteil des normalen Zielstarts. Vorher-/Nachherbestände unterscheiden; fremde existierende Dockerressourcen unverändert lassen.

## 2. Prüf-IDs und Mindestbeobachtungen

| ID | Phase | Zu beweisender Vertrag |
|---|---|---|
| F01 | F0 | Inventur ist lesend. Falsche Container-ID, fremdes Label oder abweichendes Projekt wird vor jedem Mutationsaufruf abgewiesen. |
| F02 | F0 | Gewähltes PG16/PostGIS-Image läuft nativ, Ziel-Minor nicht älter als Quellen; drei logische DBs möglich, benötigte Extensions vorhanden. |
| F03 | F0 | OpenCode führt unabhängig echte Datei-/Shellprüfungen aus; fehlender/falscher SHA/Reviewreport öffnet kein Gate. |
| F04 | F1 | Ein Default-Composeprojekt mit genau den zehn Dauer-Services, einmal je Service; kein HA-/Managementparallelstack, echte Composelabels. |
| F05 | F1 | Ein PostgreSQL-Service, DBs keycloak/superset/management. Konten positiv im eigenen Bereich, negativ im fremden; Management-Audit und Ownerrechte korrekt. |
| F06 | F1 | Frischer Imagebuild und explizites Setup, dann Standardstart ohne Host-JAR und ohne XTF/Jenkins-Publikation. Leerer Katalog startet korrekt, keine automatischen Grants. |
| F07 | F1 | Ein Keycloak auf PostgreSQL; echter Browsercodeflow bzw. geeigneter Testtoken. APISIX/Java/Authz/Origin liefern erlaubte Bytes und verweigern unberechtigte Zugriffe. |
| F08 | F1 | Jenkins `/jenkins/`/`/anlieferung` nach Netztrennung erreichbar; vorhandene Superset-ClickHouse-Verbindung funktioniert; keine kaputten localhost-Upstreams. |
| F09 | F2 | Drei nichtleere Quelldatenbanken gesichert und im einen Ziel tatsächlich restauriert; Fachobjekte, Auditzeilen, ACLs/Owners und Sequenzen erhalten. |
| F10 | F2 | Keycloak-Personen/Clients erhalten; MA-Principalbindung auf belegten Zielissuer/-subject übertragen; historisches Audit unverändert; unklare Identität abgelehnt. |
| F11 | F2 | S3-Objektbytes und Metadaten in einem Garage identisch, wiederholtes Copy idempotent; gleichnamiger abweichender Key ist Konflikt. |
| F12 | F2 | Fehler vor Cutover erlaubt belegten Rückfall; inzwischen geänderte Quelle wird erkannt; Neustart des Migrationsprogramms dupliziert weder Daten noch Grants. |
| F13 | F2 | Superset-SECRET_KEY und DB-Credentials konsistent, verschlüsselte Verbindung verwendbar; Backups privat; keine Secrets in bereinigten Logs. |
| F14 | F3 | Alle aktiven Lifecycle-/Managementwrapper führen dasselbe Composeprojekt; kein versteckter Legacylauncher, kein Admin-Repo als zweite Runtimequelle. |
| F15 | F3 | Stop/Start **und** `down` ohne Volumenlöschung mit anschliessendem `up` erhalten UUIDs, Daten, Grants, Audit, Storagebytes und Keycloakzustand. |
| F16 | F3 | Retire/Rollback verweigert nicht gelistete oder inzwischen andere Ressourcen; DB-/Garage-/Keycloak-Schreibschichtdaten vor Entfernen gesichert, alte Volumes nicht gelöscht. |
| F17 | F4 | Echte E2E-Folge auf Standardtopologie: Änderung sichtbar, Antrag, Genehmigung, Download, Widerruf mit gleichem Zieltoken, Audit. |
| F18 | F4 | Mindestens eine aktuelle/historische Repräsentation erbt Datensatzrecht; HEAD/Range/ETag, Pfad-/Header-Spoofing und Ausfall der Authorization API korrekt. |
| F19 | F4 | Nach Neuerstellung des endgültigen Zielverbunds dieselben Zustände; Jenkins-/ClickHouse-/Superset-Sentinels erhalten, OIDC-Neulogin funktioniert. |
| F20 | F4 | Nach Abschluss genau ein regulärer Zielstack, keine aktiven Legacy-/Probe-/Doppelcontainer; Quellübernahme/Rückfall und ggf. offene Livegrenze ehrlich dokumentiert. |

Ein negatives Rechtsergebnis zählt nur, wenn dieselben Credentials vorher am erlaubten Objekt erfolgreich waren und die gesperrte Ressource existiert. Eine kaputte Verbindung beweist keine Autorisierung. Ein 503 beim absichtlichen DBausfall ist korrekt, aber kein Ersatz für den 403-Nachweis bei laufender DB.

## 3. Die besonders wichtigen Proben

### 3.1 Nicht nur Restart, sondern Recreate

Frühere Tests starteten dieselben Container wieder. Das übersieht Zustand in der Container-Schreibschicht.

Im isolierten Zielprojekt:

1. Explizite kleine Fixture mit Metadaten, aktiver und widerrufener Freigabe, Decision, Audit und mindestens zwei privaten Dateien erzeugen; Keycloak-Benutzer/Clientänderung vornehmen.
2. Stabile IDs, inhaltliche Hashes, Secretsreferenzhashes und erlaubte/verweigerte Ergebnisse festhalten.
3. `docker compose down` **ohne** `-v` ausführen.
4. Container aus kanonischem Compose neu erstellen.
5. Inhalte und IDs vergleichen; neues Login, noch gültige fachliche Freigabe und weiterhin wirksamen Widerruf nachweisen.
6. Zusätzliche fachliche Änderung auditiert speichern. Neue PK muss keinen restaurierten Sequenzwert wiederverwenden.

Tokens/Sessions müssen nach explizitem Issuer-Cutover nicht erhalten sein. Nach gewöhnlichem Recreate darf der Issuer nicht zufällig wechseln; ein erforderlicher Login darf keine verlorenen Identitäten/Grants verdecken.

### 3.2 Migrationsprobe mit echten Nichtleerbeständen

Kleine bekannte Fixture genügt, aber nicht drei leere Datenbanken. Beispiel: Foundation-Keycloak enthält Anna und einen fremden Client, Superset enthält einen gespeicherten DBzugang; MA enthält Annas Grant, Bens Widerruf, Claudias Zuständigkeit, Audit und private Versiondateien. Keine weiteren Fachdatensätze nötig.

Nach Übernahme muss die Bedeutung identisch sein. Alte Auditzeilen kanonisch hashen, nicht nur count vergleichen. Erwartbare neue Migrationsauditereignisse separat prüfen. Fremder Client erhalten, nicht durch Realm-Neuimport beseitigt. Ein selbst entworfener Identitäts-/Objekt-/Rollen-Konflikt muss sauber stoppen, ohne die gültige Zielkonfiguration teilweise zu aktivieren.

### 3.3 Wirkliche Standardtopologie

Beobachtete Dockerressourcen mit erwarteten Compose-Services abgleichen. Endzustand: `postgres`, `keycloak`, `garage`, `origin`, `gateway`, `sodata`, `admin`, `jenkins`, `clickhouse`, `superset`, je einmal laufend. Einmaljobs müssen beendet sein. Alle normal laufenden Services gehören zum selben vorgesehenen Projekt. Quellfixturecontainer nur innerhalb eines benannten Migrationslaufs; danach entfernt/gestoppt gemäss Retirevertrag.

Auch den aufgerufenen Prozesspfad lesen: keine Shellfunktion, die hinter `compose up` zusätzlich `managed_runtime.py start` ausführt. Manuell gefälschte Compose-Labels gelten nicht als Nachweis. `up` auf einem zweiten Lauf darf keine weiteren dauerhaften Container erzeugen.

### 3.4 Download-Regression beim Wechsel der Routen

Kein kompletter Sicherheits-Neuentwurf, aber die geänderte Verdrahtung ist sicherheitsrelevant. Repräsentativ neu ausführen: anonym open erlaubt, restricted ohne Login 401, eingeloggte unberechtigte Person 403, Grant erlaubt, Widerruf mit gleichem Token verweigert, historische Version identisch geregelt, interne API nicht öffentlich, encoded/traversal-Pfad verworfen, gefälschte Identitätsheader wirkungslos, keine Credentials am Origin, Authz-Ausfall fail closed.

Datei-Hash und ein korrekter Range-Teilbereich gehören dazu. Fehlender Token wird nicht durch erfundene Header ersetzt. Temporärer Headerbeobachter ausschliesslich als test-only Composejob, anschliessend entfernen. Kein `origin-p…` im Normalbetrieb.

## 4. Welche Änderungen welche Tests auslösen

| Geänderte Stelle | Jetzt neu prüfen | Nicht automatisch neu prüfen |
|---|---|---|
| Compose-Service/DNS/Port/Health | betreffender Start, Erreichbarkeit, Netz-/Bypassgrenze | gesamte INTERLIS-/Cayenne-Modellmatrix |
| PG-Image/Volume/Restore | Restoreprobe, Extensions, Owner/ACLs, Auditfunktion, betroffene Anwendungslogins | vollständige GUI-/CSVvalidierung |
| Keycloak/Ist-Ziel-Identität | tatsächliches Token/Issuer/sub, bestehende Grants, Login, Konfliktfall | Dateiinhalte aller unveränderten Formate |
| APISIX-/Originroute | Authz-/Rohpfad-/Header-/Downloadtests auf echter Kette | kompletter PK-/Constraint-Testbestand |
| Lifecyclewrapper/Ownership | falsches Ziel, Stop/Start/Recreate im eigenen Projekt, korrekter Parameterfluss | alle fachlichen Browserfälle |
| Audit-/Principal-Migrationsbefehl | betroffene Transaktion, Rollback, Konflikt, unverändertes altes Audit | gesamte Katalogsuchmatrix |
| Imagebuild/JAR-Verpackung | frischer Build, Start ohne Hostartefakte, betroffene Readiness | alle unveränderten Services neu bauen |
| Dokumentation/Pfadkorrektur | Link-/Kommando-/Versionskonsistenz | vollständige Runtime nochmals starten |

Die Auswirkungen entscheiden, nicht die Anzahl geänderter Zeilen. Ein Einzeiler in der Authzroute kann mehr Nachtests benötigen als viele Dokumentationszeilen.

## 5. Review nach einem Fix

Vor jedem Delta-Review kurze Tabelle: `Änderung → gefährdeter Vertrag → neu ausgeführte Tests → belegbar unveränderte Nachweise`. Neuer vollständiger Repo-SHA-Satz, neue Handoffbindung. Der Reviewer liest den ganzen neuen Diff und prüft relevante Ziele, führt aber nur gefährdete Tests plus eigene sinnvolle Gegenprobe neu aus.

Beispiel: korrigierter Compose-DNSname für den Origin → echter erlaubter Download, Widerruf und internes Erreichbarkeits-/Headerverhalten. Keine neue komplette ili2pg-Mappingrunde. Geänderter Restore-Ownerpfad → Daten/Audit/ACLs und App-Schreibvorgang neu; bestehender unveränderter UI-Layouttest darf übernommen werden.

Ein fälliger nicht ausgeführter Test ist `NOT_EXECUTED` und blockiert. Ein begründet nicht betroffener Test ist `NOT_REQUIRED`. Übernommener Nachweis braucht akzeptierten Quell-SHA, Testbezeichnung und konkrete Nichtbetroffenheit, nicht bloss „war vorher grün“.

## 6. Lokale Nutzerumstellung separat nachweisen

Reviewer beweisen Code und Migration an eigenen Quellen. Der Implementierer dokumentiert für die tatsächliche Nutzerinstanz danach:

- genaue geprüfte Quellen/Ziel und Backupreferenzen ohne Secrets;
- angewendete Version und Planhash;
- stabile IDs, Daten-/Audit-/Dateiabgleiche;
- erfolgreiche Zielzugänge;
- gestoppte/entfernte alte Container und erhaltene Sicherungsvolumes;
- verbleibende unauflösbare Quellen, falls vorhanden.

Zulässige getrennte Status: `IMPLEMENTATION_ACCEPTED`, `LOCAL_CUTOVER_VERIFIED`, `LOCAL_CUTOVER_PENDING`, `BLOCKED_IDENTITY_MAPPING`. Kein generisches „alles erledigt“ bei bloss bestandenem isoliertem Test.
