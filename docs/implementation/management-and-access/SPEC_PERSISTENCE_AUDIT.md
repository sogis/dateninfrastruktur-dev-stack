# Persistenz und Audit – PostgreSQL, ili2pg und Cayenne 5-M3

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Ziel ist tatsächliche, kontrollierte Persistenz mit nachvollziehbaren Änderungen – kein neues ORM-, Schema- oder Auditframework.

## 1. Datenbanktopologie und Berechtigungen

Eine neue logische Datenbank `dateninfrastruktur_management`, getrennt von Keycloak und Superset. Bestehende PostgreSQL-16-Daten bleiben unverändert.

**ili2pg/PostGIS:** MA-0 prüft die konkrete gepinnte Version mit einem geometriefreien UUID-Modell. Die ili2pg-Dokumentation nennt PostGIS/uuid-ossp; `--setupPgExt` erzeugt entsprechende Extensions. Deshalb nicht ungeprüft Vanilla-PostgreSQL voraussetzen. Funktioniert der notwendige Vertrag ohne PostGIS, dritte DB in vorhandener Instanz verwenden. Andernfalls eigener lokaler PG16+PostGIS-Service für Management, native Hostarchitektur prüfen. Kein unkontrollierter Imageaustausch unter den bestehenden Keycloak-/Superset-Volumes. Erweiterungs-/Migrationzugänge nie in die Webanwendung geben.

Logische Schemas: `di_management` (ili2pg-Fachschema), `api_public` (normale aktuelle SQL-Views), `audit` (technische Historie), `di_ops` (nur nötige Import-/Idempotenz-/Vertragsinformationen).

| DB-Rolle | Erlaubnis |
|---|---|
| `di_owner` NOLOGIN | Fachschema-Eigentümer, kein Appkonto |
| `di_audit_owner` NOLOGIN | Auditobjekte/-funktionen; keine fachliche Mutation |
| `di_migrator` | explizites Setup/Migration, niemals Webruntime |
| `di_writer` | Admin-DML auf benötigte Fachtabellen; kein DDL/TRUNCATE/CREATEROLE/GRANT, nicht Owner |
| `di_authz` | SELECT auf benötigte Autorisierungsbeziehungen, kein Audit/Schreiben |
| `di_public` | SELECT nur auf benannte `api_public`-Views, keine Basistabellen |
| optional `di_audit_reader` | enger Readzugang; Service beschränkt zusätzlich auf Dataset-Zuständigkeit |

Laufzeitkonten weder Superuser noch BYPASSRLS, kein SET ROLE auf Owner. Default-PUBLIC-Rechte prüfen. Sequenzrechte nur soweit benötigt. Eine zweite DataSource mit denselben Admincredentials ist keine Trennung. Persönliche Fachanwender erhalten keinen `di_writer`-Zugang.

## 2. Schema-/Mappingprofil und Lebenszyklus

### 2.1 Reproduzierbares Profil

`db/mapping-profile.json`: genaue Modelle/Hashes, ili2pg-/Compiler-/Validatorversionen, verwendete echte Optionen und Namensraum. Benötigte Fähigkeiten: UUIDOID, stabile TIDs, FK/NOT NULL/UNIQUE, `--createMetaInfo`, `--createStdCols`, nachvollziehbare Enum-/Assoziationsabbildung. Weitere Flags nur nach Prüfung ihrer echten Semantik.

Physische Tabellen-/Spaltennamen aus ili2db-Metadaten lesen, nicht aus Klassennamen raten. Das aufgelöste Mapping kann als `db/model-mapping.json` versioniert und bei Setup überprüft werden. Unbekannte Mehrdeutigkeit führt zum Fehler, nicht zu still fehlenden Constraints/Triggern.

### 2.2 Schlüssel und OIDs

Cayenne darf nicht einen von ili2pg unkoordinierten PK-Generator verwenden. Prüfen: Typ/Default/Sequenz von t_id; TID-UUID-Spalte; generierte FKs. Vorzugsweise DB-generierte Werte korrekt in Cayenne markieren. Falls ein eigener schmaler PK-Adapter benötigt wird, die tatsächliche ili2db-Sequenz verwenden. Keine ungeprüfte zusätzliche AUTO_PK_SUPPORT-Welt.

In M3 liegt PkGenerator am DataNode. Drei verbundene Klassen in einer Transaktion anlegen, neu laden, per ili2pg exportieren und validieren. Damit tatsächlich Keys, Beziehungen und stabile OIDs beweisen, nicht bloss erfolgreiche INSERTs.

### 2.3 Zeit, Enum und Text

MTEXT samt Unicode/Zeilenumbrüchen verlustfrei. Enums als stabile fachliche Codes, nicht Ordinalzahlen. Verwaltungsevents in UTC; tatsächliches ili2pg-DATETIME-Mapping auf timestamp/timestamptz dokumentieren und JDBC-Konvertierung explizit testen. Host-Zeitzone darf keinen stillen Einfluss haben. DATE bleibt DATE. Audit explizit timestamptz.

`current_timestamp` bedeutet PostgreSQL-Transaktionsbeginn, nicht Commitzeitpunkt. Audit erfasst `clock_timestamp()` plus Transaktions-/Commandkennung; weder Sequenz noch Zeit als strenge globale Commitreihenfolge ausgeben.

### 2.4 Erstaufbau und Migration

`SchemaBootstrapCommand.run(SetupOptions)`:

1. Zielinstanz/Namensraum prüfen, Setup serialisieren.
2. Leeres Fachschema mit gepinntem ili2pg erzeugen. Existiert es, auf bekannte Vertragsrevision prüfen, nicht blind neu erzeugen.
3. Versionierte Zusatzmigrationen für Constraints, row_version, Views und Audit anwenden.
4. Auditinstaller ausführen und Abdeckung prüfen.
5. Rollenrechte vergeben, Schema-/Mappinghash speichern.
6. Demo-Seeding nur explizit mit technischer Identität; keine Benutzer-/Grantresets bei Appstart.

Eine vorhandene Migrationslösung weiterverwenden. Flyway ist zulässig, sofern sinnvoll integriert; keine zweite generische Migrationsengine entwickeln. ili2pg bleibt Quelle des initialen Fachschemas. Runtime hat keine DDL-Rechte und führt weder `cdbgen` noch `createSchemaIfNeeded()` aus.

Spätere Modelländerung: bewusste Daten-/Schemamigration, nicht destruktiver Neuimport. Nach Migration Mapping, SQL-Views und Auditabdeckung prüfen. MA-B verlangt idempotentes Setup und einen echten begrenzten Upgrade-/Restore-Nachweis. Ein verwendeter Additivschritt kann diesen Test liefern; kein künstliches Zweitmodell nur für die Testzahl.

Legacyimport über Java/Cayenne-Fachservices mit dry-run und technischer Actoridentität. Direkter ili2pg-Replace auf laufendem auditiertem Bestand ohne Actor-/Transaktionsvertrag ist nicht erlaubt. Schema-Probe auf isolierter leerer DB vor Auditinstallation ist davon getrennt.

## 3. Cayenne-Konfiguration und generierter Code

### 3.1 Boot-Integration

Normale Spring-Beans, keine JPA-Abhängigkeit und keine erfundene Cayenne-Autokonfiguration. Qualifizierte DataSources für Writer/Authz/Audit. M3-Grundgerüst:

```java
// Strukturbeispiel; konkrete Imports/Classpath beim realen Build prüfen.
@Bean(destroyMethod = "shutdown")
CayenneRuntime managementRuntime(
        @Qualifier("managementWriterDataSource") DataSource source) {
    return CayenneRuntime.of()
        .addConfig("cayenne/cayenne-management.xml")
        .defaultDataNode(source)
        .build();
}
```

API: `org.apache.cayenne.runtime.CayenneRuntime`, Artefakt `org.apache.cayenne:cayenne:5.0-M3`. M3-DataNodes programmatisch, keine Credentials im DataMap-/Projekt-XML. DataSource-Lebenszyklus korrekt schliessen.

cdbimport/cgen derselben M3-Version gegen das isolierte generierte Fachschema. Audit-, PostGIS-, Keycloak- und Superset-Tabellen nicht versehentlich importieren. DataMaps versioniert; generierte Basisklassen `_Dataset` etc. getrennt von handgeschriebenen Unterklassen. cgen überschreibt keine Fachlogik. Zweiter Generatorlauf semantisch reproduzierbar.

### 3.2 Kurzlebige Kontexte und aktuelle Rechte

Neuer ObjectContext pro Kommando, nie Singleton oder Browsersitzungsobjekt. Query-/Shared-Snapshot-Caches für veränderliche Managementdaten zunächst deaktivieren beziehungsweise nachweislich umgehen. M3-Konfigurations-API prüfen, keine entfernten Setter verwenden.

Autorisierung verwendet gezielt **frische parametrisierte JDBC-Leseabfragen** über `di_authz`. Admin schreibt weiterhin mit Cayenne. Dieser schmale Lesepfad vermeidet eine unsichtbare veraltete ORM-Berechtigungssicht. Kein zweites ORM.

M3 loggt SQL-Bindings über `cayenne-sql`: Produktkonfiguration muss vertrauliche Parameter-/Freitexte nicht unkontrolliert protokollieren. Token, Secrets, vollständige Principalprofile und Begründungen nicht in rohe Debugausgaben oder Reviewlogs kopieren.

## 4. Klassen- und Methodenverträge für Transaktionen

| Typ | Pflichtvertrag |
|---|---|
| `ActorContext` | immutable issuer, subject, kind, optional interne Principal-OID; keine Tokens; von verifizierter Identität erzeugt |
| `CommandContext` | commandId, serverseitige requestId, actionCode, optionale reason; keine freie Actorwahl |
| `AuditedUnitOfWork` | `<T> T execute(ActorContext, CommandContext, Function<ObjectContext,T>)` |
| `AuditContextWriter` | `void bind(ObjectContext, ActorContext, CommandContext)` |
| `AggregateWriteGuard` | `lockDataset(ctx, oid, expectedVersion)`, `lockRequest(...)`; liest aktuelle Revision unter FOR UPDATE |
| `CommandReceiptRepository` | `findOrReserve(ctx, actor, commandId, action, payloadHash)`, `complete(ctx,resultRef)` soweit nötig |
| `CayenneMappingVerifier` | `verifyRequiredEntities(runtime)`, `verifyPhysicalMapping(connection, profile)` |

Transaktionsvertrag:

```text
CayenneRuntime.performInTransaction:
  frischen ObjectContext anlegen
  transaktionslokalen Actor über Cayenne-Query auf derselben Connection setzen
  Aggregate in konsistenter Reihenfolge sperren / expectedVersion prüfen
  aktuelle Zuständigkeit innerhalb dieser Transaktion prüfen
  Fachänderungen und fachliche Entscheide erzeugen
  context.commitChanges()
  äusseren Commit erfolgreich abschliessen
ERST DANN HTTP-Erfolg zurückgeben
```

Actor setzen sinngemäss mit gebundenen Werten:

```sql
SELECT set_config('di.actor_issuer', ?, true),
       set_config('di.actor_subject', ?, true),
       set_config('di.actor_kind', ?, true),
       set_config('di.request_id', ?, true),
       set_config('di.command_id', ?, true),
       set_config('di.action', ?, true);
```

Das ist der SQL-Vertrag, nicht die Behauptung, jeder Cayenne-Querytyp verwende JDBC-`?`. Die tatsächlich unterstützte gebundene SQLSelect-/SQLExec-Syntax verwenden.

**Verbotene Abkürzungen:** Actor in einer unabhängigen `dataSource.getConnection()` setzen; `set_config` im Auto-Commit vor dem späteren ORM-Commit; nur `@Transactional` annotieren und gemeinsame Connection voraussetzen. M3-SELECTs sind nicht automatisch transaktional. Beweis über Backend-PID/Transaktion und echten Trigger erforderlich.

Fehler nach `context.commitChanges()` aber vor dem äusseren Commit muss alles zurückrollen. Exceptions nicht in der Hülle verschlucken. Nach Rollback Context verwerfen, nicht weiterverwenden. Keine Actorleckage zwischen wiederverwendeten Poolconnections; Test mit Poolgrösse1 und zwei Personen plus Schreibversuch ohne Actor.

### 4.1 Konkurrenz und Wiederholung

UI trägt expectedVersion. `FOR UPDATE` liest aktuelle Aggregatezeile, vergleicht Revision **vor** Mutation; veraltete Form =409. Technisches row_version durch klaren einzigen Mechanismus erhöhen, nicht gleichzeitig widersprüchlich durch ORM und Trigger. Bearbeitete Child-/Themenbeziehungen müssen die zugehörige Formularrevision invalidieren.

Requestentscheid sperrt Request und Dataset in dokumentierter einheitlicher Reihenfolge. Zwei parallele Entscheide dürfen nicht zwei unterschiedliche Grants erzeugen. Idempotency-Key an Actor, Aktion und Payloadhash binden. Derselbe Schlüssel mit anderem Payload =409. Receipt und Fachmutation in derselben Transaktion, kein asynchrones Erfolgsversprechen.

Keine neue globale Lockplattform. Kleine echte Parallelprobe für Entscheidung und Formularupdate genügt.

## 5. Audit: Datenvertrag und Trigger

### 5.1 Zentrale Tabelle

```text
audit.row_change
  change_id                 bigint (identity/sequence)
  recorded_at               timestamptz
  transaction_id            text
  request_id, command_id    uuid
  action_code               text
  actor_kind                text
  actor_issuer              text
  actor_subject             text
  actor_principal_oid       text nullable
  database_user             text        # session_user
  schema_name, table_name   text
  model_element             text nullable
  schema_revision           text
  object_oid                text nullable
  technical_key             jsonb
  aggregate_dataset_oid     text nullable
  operation                 I | U | D
  old_values, new_values    jsonb nullable
  changed_columns           text[]
```

Kein FK mit Delete-Cascade auf gelöschte Fachobjekte oder Principals. Erstregistrierung kennt verifizierten Actor schon vor Anlage seines Principalobjekts. Fachliche Zuordnung/Root-Dataset soll auch bei Beziehungstabellen erhalten bleiben. Wo keine Datasetzuordnung existiert, z.B. Principal-Membership, als eigenes Verwaltungsereignis korrekt kennzeichnen statt willkürlich einem Dataset zuordnen.

Indizes zunächst auf Dataset+Zeit, commandId und Objektkennung. Keine vorausschauende Partitionierungsplattform. Tabelle ist privat und kein öffentlicher XTF-Exportinhalt.

### 5.2 Funktionen

`audit.require_context()`:
- prüft nichtleere/formgültige transaktionslokale Actor-/Request-/Commandwerte;
- fehlender Kontext blockiert relevante DML; keine still anonyme Fallback-Autorenschaft;
- feste technische Dienste ebenfalls explizit kennzeichnen.

`audit.stamp_row()` als BEFORE INSERT/UPDATE:
- kontrollierte t_createdate/t_lastchange; Createdate beim Update erhalten;
- t_user technische DBkennung/kurze abgesprochene ID, volle Identität separat. Feldlänge prüfen, nichts still abschneiden;
- row_version bei wirklicher fachlicher Änderung erhöhen;
- no-op nicht durch eigene Stempel in eine künstliche Änderungsserie verwandeln.

`audit.log_row_change()` als AFTER INSERT/UPDATE/DELETE FOR EACH ROW:
- OLD/NEW in JSONB, nach anderen BEFORE-Änderungen final gespeicherte Werte;
- INSERT old=null, DELETE new=null, UPDATE beide;
- Redaction kontrolliert, changed_columns ohne Geheimniswerte;
- gemeinsame commandId verbindet mehrere Zeilen;
- keine Rekursion auf Audittabelle;
- Auditfehler führt zum Rollback auch der Fachmutation.

Die Funktionen sind kontrolliert SECURITY DEFINER mit `di_audit_owner`, festem `search_path=pg_catalog,pg_temp`, qualifizierten Objektnamen, restriktiven Aufrufrechten. Keine beliebigen SQL-Kommandos als Funktionsargument. App darf Audit nicht direkt ändern/löschen und Trigger nicht deaktivieren. Writer besitzt nicht die Fachtabellen.

Separate Schutzfunktionen verhindern UPDATE/DELETE unveränderlicher AccessDecision/CatalogAction und unerlaubte Umdeutung von Grantbasis. Widerruf ist zulässige einmalige Beendigung, kein DELETE.

TRUNCATE und DDL sind nicht durch I/U/D-Rowtrigger abgedeckt: Laufzeitkonten dürfen sie nicht ausführen. Migrationen separat dokumentieren und Abdeckung nachher prüfen. SELECT-/Download-/Loginversuche sind andere Protokolle. Rollbackte Versuche sind keine dauerhaft gespeicherten row_change-Einträge.

### 5.3 Kleiner externer Installer

Metaattribute konfigurieren die Abdeckung; Trigger protokollieren zur Laufzeit. Keine Änderung an ili2db. Klassen:

| Typ | Methoden |
|---|---|
| `IliMappingRepository` | `readMetaAttributes(connection)`, `resolveTables(element)`, `resolveColumn(attribute)`, `readDependentTables(element)` |
| `AuditPolicyResolver` | `resolve(mapping, meta, explicitOverrides)` → vollständige Liste |
| `AuditTablePolicy` | physischer Name, Modellklasse, PK/OID-Spalten, Parentbezug, redacted columns, Schutzart |
| `AuditInstaller` | `plan(connection, policies)`, `apply(connection, plan)` idempotent |
| `AuditCoverageVerifier` | `verify(connection, expectedPolicies)` gegen pg_catalog |
| `AuditSetupCommand` | explizite CLI `--plan`, `--apply`, `--verify`; kein Webstartup-DDL |

`--createMetaInfo` plus tatsächliche Klassen-/Attributmappings verwenden. Klassen sind nicht immer 1:1 Tabellen. Assoziationen/BAG-/STRUCTURE-Hilfstabellen einschliessen. Aufgelöstes `db/audit-policy.json` prüfen/versionieren. Noch nicht automatisch unterstützter Mappingfall darf eine explizite geprüfte Zuordnung bekommen; keine stille Lücke und kein allgemeines Toolprojekt.

Coverage prüft vollständige Sollmenge, richtige Funktion, Timing, Events, enabled-Status und Redaction. Ein fehlender Trigger muss Test/Setup abbrechen. Ausschlüsse nur für tatsächliche System-/Metatabellen mit Begründung, nicht für Grants/Entscheide/Memberships.

### 5.4 Vertrauens- und Revisionsgrenzen

PostgreSQL-GUCs sind kein kryptografischer Identitätsnachweis. Wer Writercredentials hat, könnte sie selbst setzen. Deshalb serverseitige Authentifizierung, minimale interne Zugänge und zusätzlich `session_user` protokollieren. Superuser/Owner können Datenbankhistorie manipulieren; keine absolute Manipulationssicherheit behaupten.

Keine Tokens, Passwörter oder S3-Secrets im Fachbestand; notwendige Redaction testen. Auditansicht nur im passenden Zuständigkeitsbereich. Kein automatisches Purging im MVP; Aufbewahrung/Löschung später fachlich festlegen, nicht pauschal „nie löschen“ als Gesetz behaupten. Ein isolierter Backup-/Restore-Test bleibt eigene Betriebsprüfung, keine vollständige historische Zustandsrekonstruktion.

## 6. Öffentlicher SQL-Lesekontrakt

Normale Views, explizite Spaltenlisten:

- `api_public.datasets`: published Roots, sichere gemeinsame Metadaten, kind/accessLevel.
- `api_public.issues`: published Issues unter published Root.
- `api_public.versions`: available Versionen sichtbarer Ausgaben, sichere technische Angaben.
- `api_public.distributions`: available Distributionen verfügbarer Versionen, ID/Format/Filename/Grösse/kontrollierter Downloadpfad.
- zugehörige Offices/Themen/Keywords/Attributdefinitionen.

Keine Grant-/Principal-/Audit-/Origin-/Objektkeydaten. Keine Basistabellenrechte für Public auch nicht als schneller Mapper-Workaround. View-Eigentümer kontrolliert, PUBLIC-Rechte entziehen. Sodata verwendet gebundene JDBC-Abfragen/DTOs, keine schreibbaren Admin-Cayenne-Entitäten.

## 7. Pflichtnachweise

Die IDs stehen in TEST_PLAN. MA-B muss insbesondere zeigen: echte ili2pg/Cayenne-Keys und Beziehungen; Actor auf derselben Connection; Poolisolation; äusserer Rollback; I/U/D und Relationshipaudit; no-op/Redaction; immutable Entscheide; verbotene Audit-/Schema-/TRUNCATE-Zugriffe; Publicsicht erlaubt, echte Basistabellen gesperrt; fehlender Trigger erkannt; Setup/Re-run/Restore bewahren Zustand.
