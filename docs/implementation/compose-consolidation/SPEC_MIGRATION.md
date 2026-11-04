# MA-F – Verbindlicher Übernahme- und Rückfallvertrag

Dieses Kapitel gehört zu `EXECUTION_PLAN.md`. Eine **frische** Installation und die Übernahme eines **befüllten** Bestands sind zwei ausdrücklich unterschiedliche Abläufe. Kein leerer Neuaufbau als vermeintliche Migration. Die in F0 gewählte konkrete Quellmenge ist verbindlich; wechselnde Container-IDs/Quellstände werden neu geprüft.

## 1. Schutzregeln und explizite Quellen

Es gibt heute mindestens zwei logisch verschiedene Quellen:

- Foundation: Compose-Projekt mit PostgreSQL (Keycloak/Superset), Garage, Jenkins, ClickHouse und Superset-Home.
- Management: einzelcontainerbasierte MA-Laufzeit mit Management-PostgreSQL/PostGIS, zusätzlichem Keycloak und zusätzlichem Garage; Runtimezustände unter ADMIN/.runtime.

Die im Screenshot gezeigten Namen sind Suchhinweise, **keine ausreichende Löschberechtigung**. Inventur prüft genaue IDs, Labels, tatsächliche Mounts und zugehörige private State-Dateien. Laufzeitordner `.runtime/managed`, `.runtime/managed-test`, ältere `.runtime/management-db`/`.runtime/identity` und isolierte Reviewcheckouts unterscheiden. Kein `docker ps | grep di-ma | xargs rm`.

Mehrere gefundene Managementquellen dürfen verschiedene Metadaten/Grants enthalten. Gleiche Schemas bedeuten nicht gleichen Fachbestand. Auswahl darf automatisch erfolgen, wenn Zuordnung eindeutig und mit vorhandener Konfiguration belegbar ist. Andernfalls Quelle nicht überschreiben; Daten sichern, Konflikt konkret benennen, Konsolidierungscode auf isolierten Fixtures weiter fertigstellen. Kein automatisches Zusammenführen unterschiedlicher Grants oder Entscheide.

Nur ausdrücklich gewählte eigene lokale Ressourcen übernehmen. Die Erlaubnis zur Migration umfasst das gezielte Lesen ihrer Credentials/State-Dateien und Nutzung durch die Migrationsprogramme. Sie erlaubt **keine** Ausgabe dieser Werte in Chat, Reviewprompt oder Git. Die alte Regel „keine fremde .env kopieren“ gilt weiter für fremde Projekte und Reviewer; sie verbietet nicht die notwendige, kontrollierte Übernahme der tatsächlich ausgewählten eigenen Instanz.

## 2. Minimaler Plan, kein neues Inventarsystem

Ein geschütztes lokales `plan.json`, ein kleines Fortschrittsjournal und ein bereinigter Bericht genügen. Planfelder:

| Feldgruppe | Inhalt |
|---|---|
| `operation_id`, `mode`, `target_project` | Eindeutiger Auftrag; `fresh` oder `migrate` |
| `source_refs` | Exakte Container-/Volumen-IDs, Composeprojekt/Labels, State-Dateipfade, Rollen der Quellen |
| `source_versions` | PG/PostGIS/Keycloak/Garage und Architektur tatsächlich gelesen |
| `target` | Composefile-/Templatehashes, Image-Digest, gewählte Volumenamen, stabile URLs |
| `database_mapping` | Foundation:keycloak→target:keycloak; Foundation:superset→target:superset; MA:management→target:management |
| `identity_mapping` | Quellissuer/-realm/-subject → Zielissuer/-realm/-subject; Grund und Konfliktstatus |
| `storage_mapping` | Quellbucket/-key → Zielbucket/-key, Datei-Hash/Grösse/Metadaten |
| `secret_refs` | Nur Dateiverweise/Feldnamen im bereinigten Plan; keine Secretwerte |
| `backup_refs` | Archive, SHA256, Vollständigkeit, Restore-Nachweis |
| `retire_allowlist` | Nur exakt bezeichnete alte Ressourcen; Volumes standardmässig ausgenommen |
| `source_checkpoint` | Beobachteter Fach-/Identitäts-/Objektzustand und Zeitpunkt der letzten konsistenten Sicherung |

Rohplan, Backups und konkrete Personenkennungen privat behandeln. Verzeichnis 0700, Dateien 0600. Bereinigte Berichte enthalten Hashes, Mengen und Zuordnungsstatus statt personenbezogener Tabellenkopien.

Zulässige Fortschrittszustände z.B. `INVENTORIED → BACKED_UP → TARGET_RESTORED → VERIFIED → CUTOVER → RETIRED`. Jeder Schritt wiederholbar oder vor Wiederholung eindeutig als bereits abgeschlossen erkennbar. Keine Transaktion über PostgreSQL, Keycloak und S3 behaupten.

## 3. PostgreSQL: drei Datenbanken zusammenführen, nicht Datenverzeichnisse

### 3.1 Ziel ist eine neue, geprüfte PG16/PostGIS-Datenablage

Für die Zusammenführung unterschiedlicher PG-Images/Cluster standardmässig **logischer Dump/Restore in ein neues benanntes Zielvolume**. Bestehendes Foundation-PGDATA und MA-PGDATA nicht binär zusammenkopieren. Alpine-/Debian-/Collation-/Extensionunterschiede sind gerade ein Grund, nicht einfach das Image am alten Datadir auszutauschen.

Ziel-PG bleibt Major16, kein Minor-Downgrade. PostGIS-Binaries/Extensionversionen und Locale/Encoding/Collation anhand der Quellkataloge feststellen. Zielbereitstellung darf bei inkompatiblem Stand nicht „best effort“ Daten auslassen. `pg_dump`/`pg_restore` passend zu den Quellen pinnen; kein ungeprüfter Hostclient.

Das neue Volume bleibt nach Cutover das Volume des **einzigen** Service `postgres`. Der alte physische Volumename wird als Sicherung erhalten, nicht neu als Ziel gemountet. Die Zuordnung in Compose/ENV explizit ändern. Ein vorhandener leerer Zielcluster ist kein Nachweis, dass die Datenübernahme funktioniert hat.

### 3.2 Sicherung

1. Relevante Anwendungen/Jobs für den finalen Snapshot in ein lokales Wartungsfenster nehmen; keine konkurrierenden fachlichen Schreiber zulassen. Ein früher Probelauf darf separat auf Read-only-Sicherungen stattfinden.
2. Ganze ausgewählte Datenbanken per `pg_dump -Fc` sichern, nicht nur Fachschemas. Audit, `di_ops`, ili2db-Metadaten, Views, Funktionen, Sequenzen, Migrationstand und Extensionreferenzen gehören dazu.
3. Globalobjekte (Rollen, Memberships, ggf. Tablespaces) getrennt inventarisieren/sichern. Nicht ungeprüft zwei `pg_dumpall --globals-only`-Ausgaben in einen Cluster einspielen: doppelte Adminrollen und überschreibende Passwörter vermeiden.
4. Quellhashes und Dateninvarianten getrennt erfassen. Kein Secret in Prozessargumenten/Fehlerlogs; Passwortdatei/geschützte Toolumgebung verwenden.
5. Quellvolumes und benötigte Container-Schreibschichten erhalten, bis Ziel und Rückfall nachgewiesen sind.

`pg_dump` liefert einen konsistenten Snapshot **einer** Datenbank, aber keinen gemeinsamen Snapshot aller Dienste. Deshalb ist die dokumentierte Schreibpause für den finalen Cutover nötig. Ein inzwischen veränderter Quellbestand invalidiert die reine Übernahme eines älteren Probedumps.

### 3.3 Restore und Datenbankrechte

Zielrollen vor dem Restore anhand einer kontrollierten Allowlist anlegen. `postgres` nicht aus einer zweiten Quelle überschreiben. `di_owner`/`di_audit_owner` bleiben NOLOGIN; Anwendungsrollen bleiben unprivilegiert. Foundation-Konten und Managementkonten werden nicht vereinigt.

Datenbanken leer und passend anlegen, notwendige Extensions konsistent bereitstellen. Restore mit Fehlerabbruch; für die kleinen Bestände eine nachvollziehbare Einzeltransaktion innerhalb einer bereits angelegten DB, soweit die konkret gewählten Optionen dies erlauben. Kein `--clean` gegen ungeprüft vorhandene Zieldatenbanken. Keine Fehler ignorieren, bloss weil die Anwendung anschliessend startet.

Owners und ACLs bewusst erhalten. Ein pauschales `--no-owner` ohne anschliessende exakte Rekonstruktion wäre hier falsch: SECURITY-DEFINER-Auditfunktionen, Views und Ownerrollen gehören zum Sicherheitsvertrag. Keine deaktivierten Audittrigger als Ergebnis. Beim vollständigen Restore in die leere DB Schema-/Daten-/Postdata-Reihenfolge nutzen; nicht Fachzeilen durch normale Writeroperationen neu importieren und dabei künstliche Audithistorie erzeugen.

Vorhandene `di_ops.runtime_contract()`, Fingerprint, Mapping und Auditcoverage prüfen. Keine automatische Schemaerneuerung oder cdbimport/cgen-Reparatur eines abweichenden Bestands. Für bekannte notwendige kleine technische Migrationen ein expliziter versionierter Schritt; Fachmodell bleibt unverändert.

### 3.4 Inhaltlich nachweisen

Mindestens vergleichen: fachliche IDs, alle Grants einschliesslich Widerrufe/Gültigkeit, Decisions, Authorities, Memberships, Principal-Zuordnung, Datenversionen/Distributionen, Request-/Receiptzustände, ili2db-OIDs, Sequenzstände und **bestehende Auditzeileninhalte**, nicht nur deren Anzahl. Für kleine Bestände kanonische sortierte Rowhashes möglich; grosse oder sensitive Werte nicht an das LLM ausgeben.

Alte Auditzeilen müssen unverändert bleiben. Zusätzliche kontrollierte Migrationsauditereignisse werden separat gezählt und begründet. Funktionierende neue audierte Schreiboperation und anschliessender Rollback/Permissiontest am Ziel belegen, dass nicht nur die Daten, sondern auch die Sicherheitsmechanik übernommen wurde.

Keycloak/Superset mit ihrem eigenen DBkonto positiv lesen/schreiben lassen; Cross-DB-Verbindung und fremde Tabellenzugriffe negativ testen. PUBLIC und AUTHZ haben nur die bereits vorgesehenen lesenden Rechte.

## 4. Keycloak: eine echte Instanz und eindeutige Personen

### 4.1 Ausgangslage ermitteln

Foundation-Keycloak ist bereits auf PostgreSQL konfiguriert. Der MA-Launcher startet Keycloak ohne `KC_DB`/PostgreSQL-Verbindung und montiert in der gelesenen Fassung nur den Realmimport. Daraus folgt: Der tatsächliche MA-Speicher ist zu prüfen; die vorhandene Datenbank kann in der Container-Schreibschicht liegen. **Die beim Start erzeugte Realm-JSON ist kein aktuelles Benutzerbackup.**

Vor Entfernen/Recreation des MA-Keycloakcontainers aktuelle Persistenz sichern. Für dev-file/H2: nach sauberem Stop Datenverzeichnis aus tatsächlichem Mount bzw. Container-Schreibschicht geschützt sichern; offline mit exakt kompatiblem Keycloak-Image einen CLI-Export aus der gesicherten Kopie erstellen. Ein Compose-Toolservice genügt. Nie zwei Prozesse auf dieselbe aktive H2-Datei schreiben lassen. Für PostgreSQL-Quellen logische DBsicherung plus gezielter Realmexport/-vergleich.

Keycloak-CLI-Exporte sind kein vollständiger Ersatz für eine Datenbanksicherung; nicht alle Sessions/Ereignisse/Zustände sind darin enthalten. Bestehende Originalkopie erhalten. Ein erneuter Login nach Cutover ist erlaubt und wird dokumentiert; stiller Verlust von Benutzern, Rollen, Passwortcredentials oder fachlichen Principal-Verknüpfungen nicht.

### 4.2 Ziel und Zusammenführung

Ziel bleibt der einzige `keycloak`-Service auf DB `keycloak` im gemeinsamen PostgreSQL. Die bestehende Foundation-Keycloak-DB ist grundsätzlich Ausgangsbasis, damit andere dortige Realms/Clients/Benutzer erhalten bleiben. Keine Totalüberschreibung der DB mit der MA-Demovorlage.

Den Management-Gatewayclient mit den benötigten Audience-/Callback-/Session-Einstellungen idempotent ergänzen. Vorhandene fremde Clients/Gruppen/Benutzer nicht entfernen. MA-only-Benutzer oder belegte Änderungen aus der gewählten MA-Quelle kontrolliert übernehmen. Bei Überschneidungen Foundation-Credentials standardmässig erhalten; Unterschiede und Entscheidung vor Cutover dokumentieren. Gleicher Benutzername oder gleiche E-Mail **beweist keine gleiche Person**.

Die drei Demo-User haben in der vorhandenen Realmvorlage feste UUIDs. Diese zur Übernahme **prüfen**, nicht daraus ableiten, dass jede reale Instanz unverändert ist. Für übernommene Benutzer Ziel-UUID/`sub` verifizieren. Kein pauschales Neuanlegen anhand des Anzeigenamens, kein Merge von Personengruppen mit bloss gleichlautenden Namen.

`--import-realm` überspringt existierende Realms; ein neuer JSON-Mount bewirkt deshalb keine automatische Aktualisierung des vorhandenen Realms. Für gezielte Änderungen einen kontrollierten CLI-/Admin-API-Setupweg benutzen. Vollimport nur in nachweislich passende leere Zielbereiche, nicht mit pauschalem Override eines befüllten Realms.

### 4.3 Issuer-/Subject-Übernahme

Der MA-Quellissuer enthält einen zufälligen Gatewayport und häufig `/auth`. Ziel ist die stabile Foundation-Keycloak-URL (`http://localhost:<KEYCLOAK_PORT>/realms/dateninfrastruktur`, standardmässig Port18080). `issuer` ist Teil der Identität, kein beliebiger Hostalias.

Für jede betroffene Person eine eindeutige Tabelle:

```text
old_issuer, old_subject, principal_uuid,
new_issuer, new_subject, verified_correspondence, migration_id
```

Nur bei belegter eindeutiger Zuordnung die aktuelle Principal-Bindung durch einen privilegienbegrenzten, auditierten Migrationsbefehl umstellen. Interne Principal-UUID, Grants, Authorities und Geschäftsentscheidreferenzen bleiben gleich. Technische Principal-Issuer (`urn:...`) nicht pauschal ersetzen. Kollidiert die neue Bindung mit einer anderen bestehenden Person, abbrechen und nicht Accounts verschmelzen.

**Historische Auditzeilen oder unveränderliche Decision-Akteurssnapshots werden nicht umgeschrieben.** Ein neues Migrationsevent dokumentiert die Änderung der aktuellen Bindung. Keine `sed`-Ersetzung über einen SQLdump. Die JWT-Prüfung akzeptiert anschliessend nur den vereinbarten aktuellen Issuer; keine permanente Multi-Issuer-Sonderregel für alte Zufallsports.

Ein neuer Login liefert dieselbe zugeordnete Person und dieselben fachlichen Rechte. Alte noch gültige Tokens dürfen wegen des Issuerwechsels scheitern. Das ist eine dokumentierte explizite Umschaltung, keine Regression des späteren Sofortentzugs. Im neuen Normalbetrieb funktioniert Entzug wieder mit demselben noch gültigen Zieltoken.

### 4.4 Konkreter Umsetzungspunkt

Falls kein geeigneter Operator existiert, einen kleinen `PrincipalIdentityMigrationCommand` in ADMIN vorsehen:

- `plan(mapping, target)` prüft alte Bindung, Zielbeleg, Uniqueness und Referenzen nur lesend.
- `apply(mapping, migrationActor, expectedFingerprint)` verwendet bestehende audierte Transaktion, prüft Precondition nochmals und ändert nur bezeichnete aktuelle Bindungen.
- `verify(mapping)` bestätigt interne IDs, unveränderte Rechte/Entscheide, neue Bindung und separaten Auditnachweis.

Keine öffentliche UI/API für diesen privilegierten Vorgang; kein generischer Identity-Merge-Service. Ein versioniertes SQL-Migrationswerkzeug mit gleichem Vertrag ist ebenfalls zulässig. Wiederholte Ausführung muss bereits korrekt zugeordnete Personen erkennen, nicht erneut verschieben oder Rechte duplizieren.

## 5. Garage/S3: ein Server, keine physische Zusammenkopie

Foundation-Garage und seine benannten Volumes grundsätzlich als Ziel erhalten. Die Dateien der ausgewählten MA-Garage über die S3-Schnittstelle in denselben Garage-Server kopieren. Die zwei Garage-Metadatenverzeichnisse niemals binär zusammenkopieren; Cluster-/Nodeidentität nicht durch Dateimischung „migrieren“.

Der Managementbucket `di-managed-private` kann im Ziel denselben Namen behalten. Objektkeys und das in Management gespeicherte Storageprofil nach Möglichkeit unverändert; nur Endpoint/Credential ändern. Dadurch bleiben Distribution-UUID und kanonische Downloadpfade stabil.

Copy statt Move/Sync-delete. Vorhandenes identisches Zielobjekt erkennen; ein Zielobjekt gleichen Keys mit anderen Bytes/Metadaten ist ein Konflikt, keine still überschreibbare Datei. Quellbestand zunächst vollständig inventarisieren. Für verwaltete Distributionsobjekte alle Bytes bzw. verifizierte Inhalts-SHA256 und Grösse vergleichen; ein S3-ETag ist nicht pauschal SHA256. Auch Content-Type und für die Auslieferung relevante Metadaten prüfen.

Privater Origin erhält einen eigenen read-only Schlüssel nur für benötigte Buckets. Keine Passwort-/Zugriffsübernahme von Benutzer-JWTs. Bei Garage-Keys sind Bucketrechte, nicht unbewiesene AWS-Präfixpolicies, massgeblich. Die Rootbegrenzung des internen Origin bleibt zusätzlich bestehen.

Nach Übernahme müssen dieselben Distributionen dieselben Bytes über neue Gatewayadresse liefern. Alte lokal kontrollierte öffentliche Aliasse für diese Daten werden gesperrt. S3-API/Website-/Originports dürfen die Autorisierung nicht umgehen. Ein neuer 404 auf nie vorhandener Datei ist kein Negativbeweis: Positivnachweis mit technischem Zugriff, danach anonymer Versuch.

Bestehende Foundation-Buckets mit nicht migrierten Artefakten erhalten, nicht pauschal leeren. Bei bewusstem Rückzug ihrer alten Downloadroute Dokumentationshinweis; keine unbestellte Datenvernichtung. Externe amtliche S3-Originale bleiben ausserhalb der Migration.

## 6. Superset, Jenkins, ClickHouse und übriger Zustand

**Superset:** vollständige Metadatenbank übernehmen. `SUPERSET_SECRET_KEY` erhalten, sonst können gespeicherte verschlüsselte Verbindungsdaten unbrauchbar werden. Ziel-DBhost ändern, nicht Dashboard-/Benutzerbestand neu initialisieren. Existierende ClickHouse-Verbindung positiv benutzen; Upsert des Bootstrapverbindungsobjekts darf keine Benutzeränderungen zurücksetzen. Entschlüsselungs-/Loginfehler nicht durch Erzeugen einer leeren neuen Superset-DB „lösen“.

**Jenkins:** identifiziertes Homevolume erhalten. Plugin/Jobs/Credentials nicht neu aus Quellen kopieren oder Seedzustand unbesehen ersetzen. Pipelinejobs dürfen keinen alten Gateway-Netzwerkraum mehr voraussetzen. Mindestens Login, Seed-/Jobliste und eine harmlose Job-/GRETL-Ausführung prüfen. Keine echten Datensatzlieferungen als Migrationstest starten.

**ClickHouse:** existierende Volumes und Credentials wieder einbinden; kein Reimport des Testbestands bei jedem Start. Vorhandene Fachdaten/Versionen nicht verändern. Datenbestand lesen und ein bestehendes Leser-/Rechteverhältnis prüfen; neue Testzeilen nur in eindeutig test-only isolierten Beständen.

Keine unabhängigen Container nur für alte Foundation-/MA-Konten beibehalten. Offlinevolumes/Backups sind zulässige Sicherungen, keine aktiven Dienste.

## 7. Geordneter Cutover

### Vorbereitung

- F0/F1/F2 und der F3-Code haben ihre notwendigen unabhängigen Abnahmen.
- Ein aktueller Plan mit Hash und konkretem Ziel liegt vor; Wiederholung erkennt bereits erfolgte Schritte.
- Zielkonfiguration enthält richtige Secrets, Volumenamen und Ports.
- Sicherungen und ein tatsächlich erfolgreicher Proberestore sind vorhanden.

### Ausführung

1. Eigene beteiligte Schreiber/Jobs und Frontends kontrolliert pausieren; ursprünglichen Running-/Restartzustand erfassen.
2. Finale konsistente Sicherungen und Inventur erstellen; Abweichungen gegenüber der Probe berücksichtigen. Bei nicht geklärten Differenzen stoppen, nicht einfach alten Snapshot nehmen.
3. Ziel-Postgresvolume mit den drei DBs wiederherstellen, Rollen/Owners/ACLs verifizieren. Keycloak- und Storageübernahme durchführen.
4. Nötige Principal-Issuerumstellung auditiert ausführen; alte Decisions/Audit unverändert lassen.
5. Quellenfrontend stoppen; stabile Ports für Ziel verfügbar machen. Kein Portkill und kein `--remove-orphans` ohne Bestandsabgleich.
6. Kanonischen Compose-Stack mit neuen Volumemappings starten. DBprüfung, Login, Grant/Entzug, Dateibytes, Audit, Superset-Verbindung und Jenkinszugang prüfen.
7. Erst bei Erfolg Ziel als aktiv markieren. Das Migrationjournal erhält Quell-/Zielabgleich und `LOCAL_CUTOVER_VERIFIED`.
8. Quellen nach Abschnitt 8 stilllegen. Normale `up.sh`-Aufrufe können sie danach nicht versehentlich neu starten.

Während einer finalen Datenübernahme dürfen Quell- und Zielinfrastruktur vorübergehend gleichzeitig vorhanden sein. Das ist Migration, kein HA-Zielbetrieb. Die Abschlussprüfung erfolgt erst nach Ende dieser Überlappung.

## 8. Alte Ressourcen und Rückfall

### Retire

Nur Objekte aus der geprüften Allowlist stoppen. Vor jedem Eingriff exakte ID/Label/Mountbeziehung erneut bestätigen. Alte Restartpolicies so behandeln, dass ein Docker-Neustart die retired Container nicht reaktiviert.

Nach erfolgreichem Cutover und Sicherung von Daten **aus der Container-Schreibschicht** alte zusätzliche Container gezielt entfernen, **ohne `--volumes`/`-v`**. Benannte und anonyme Datenvolumes separat in einem Retentionmanifest behalten. Damit bleibt Docker Desktop übersichtlich, ohne Datensicherung wegzuwerfen. Wenn ein sicherbarer Zustand noch ausschliesslich im Container steckt, diesen nicht entfernen: gestoppt lassen und als offene Retireaufgabe ausweisen.

Keine `docker system prune`, `docker volume prune`, globale Netzlöschung oder wilde Präfixsuche. Normales `down.sh` darf weder Migrationsarchive noch alte Sicherungsvolumes löschen. Endgültige Speicherbereinigung ist nicht Teil dieses Auftrags.

### Rollback

Vor Öffnung für neue Nutzerschreibvorgänge: Ziel stoppen, ursprüngliche Konfig-/Volumen-/Endpunktzuordnung wiederherstellen und Quellen kontrolliert starten. Nur gespeicherte geprüfte Objekte, keine zufällig gleichnamigen Container. Falls Altcontainer entfernt wurden, muss deren benötigte Runtime-/Persistenzkonfiguration aus dem privaten Backup rekonstruierbar sein.

**Nach neuen fachlichen Writes im Ziel** ist ein simples Zurückstarten der alten Quelle kein verlustfreier Rollback. Dann zuerst neuen Zustand sichern und einen expliziten Rückübernahme-/Abgleichplan erstellen. Migrationsprogramm darf nicht unbemerkt „zurücksetzen“. Diese Grenze im Betriebsdokument nennen.

Die F2-Probe muss mindestens einen Fehler vor Cutover und den Rückfall zeigen. Kein vollständiges Disaster-Recovery-Projekt, aber ein echter Nachweis der hier verwendeten Rückfalloperationen.

## 9. Kleine konkrete Werkzeugschnittstelle

Ein gemeinsames Skript genügt, z.B. `STACK/scripts/consolidation.py`:

```text
inventory --output <private-file>                 # nur lesen
plan --inventory <file> --output <private-plan>    # nur lesen/Plan erstellen
backup --plan <file>                              # geschützte Archive, keine Zielaktivierung
restore --plan <file>                             # nur explizites leeres/eigenes Ziel
verify --plan <file>                              # Inhalte, Identitäten, ACLs, Dateibytes
cutover --plan <file> --apply                      # nur nach validierten Preconditions
retire --plan <file> --apply                       # nur verified Quellenliste, keine Volumes löschen
rollback --plan <file> --apply                     # nur zulässiges Zeitfenster, Write-Guard
```

Intern reichen `discover_sources`, `verify_ownership`, `build_plan`, `checkpoint_sources`, `backup_databases`, `restore_databases`, `reconcile_identity`, `copy_objects`, `verify_target`, `cutover`, `retire_sources`. Jeder Aufruf erhält den konkreten Plan/Composekontext, keine versteckten globalen Zielcontainer. Exitcodes/Fehlerklassen für `SOURCE_CHANGED`, `IDENTITY_CONFLICT`, `TARGET_NOT_EMPTY`, `OWNERSHIP_MISMATCH`, `RESTORE_FAILED`, `VERIFICATION_FAILED` und `ROLLBACK_UNSAFE` eindeutig behandeln.

`--apply` ist die technische Grenze zur Mutation, nicht eine wiederkehrende manuelle Bestätigung des Reviewers. Codex darf gedeckte eigene lokale Schritte automatisieren, wenn der Plan eindeutig ist. Reviewer arbeiten immer mit eigenen isolierten Fixtures. Bei einer echten unauflösbaren Nutzerdatenentscheidung präzise blockieren, nicht raten.
