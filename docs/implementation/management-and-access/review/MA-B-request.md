# Reviewrequest MA-B

## Ausgangspunkt

- ADMIN base: `8cde32c04e32259b148eda553edd60c936f76abd`
- STACK base: `fd249186b302aa3147ebfe445767a502eab3b826`
- PUBLIC base: `8349be8aba4036ca0bb56e89cb62398e34404a5e`

MA-0 und MA-A sind unabhängig akzeptiert; bereinigte Berichte im review-Ordner,
Rohbindungen MA-0/20261104T141858Z und MA-A/20261104T143229Z. Kein übernommener
statt neu ausgeführter MA-B-Pflichtcheck. Fremde unversionierte historische
Nachweise im STACK bleiben unverändert und werden nicht ins Review kopiert.

## Änderungen / Zielverträge

Stock-ili2pg5.5.2 erzeugt echtes UUID-Fachschema in eigenem nativen PG16/PostGIS.
Mappingprofil und tatsächliche Klassen-/Attribut-/Default-/Metamappings sind
versioniert. Cayenne Runtime/Gradle-cdbimport/cgen jeweils5.0-M3. Kontrollierte
UUID-Typnormalisierung und schmaler PkGenerator auf tatsächlicher ili2db-Sequenz
beheben reproduzierte M3-Abbildungsprobleme. Ein zweiter cdbimport/cgen ist
byte-identisch; generierte Basisklassen bleiben von Unterklassen getrennt.

Explizite zusätzliche Migrationen/rollengetrennte Konten, readonly Publicviews,
aktuelle Startup-/Readinessprüfung und gebundener Schema-/Mappingfingerprint.
Setup-Re-run erhält Credentials/Daten und verweigert unbekannte Schemata statt
Neuimport. Anwendungsstart führt kein DDL aus und prüft sein eingeschränktes
Writerkonto; Authz verwendet ein separates readonly-Konto.

AuditedUnitOfWork/AuditContextWriter: neuer Context, explizite äussere Cayenne-
Transaktion, SQLExec-Actorbindung auf derselben Connection, Commit erst vor
Rückgabe. Shared-Snapshot-Cache aus. Echte UTC-Abbildung und Test mit abweichender
PG-Sessionzeitzone; row_version-Guard mit FOR UPDATE und Stale-Konflikt.

Generischer externer Auditinstaller über reale ili2db-Mappings:16 Fachtabellen,
alle eingebetteten Assoziationen und definierte Redaction. BEFORE-Stempel,
AFTER-I/U/D inklusive command/request/vollem Actor und session_user. No-op,
immutable Entscheide/Grantbasis/Principalidentität, kontrollierter Revoke,
Parent-/Zeit-/Scope-/Dateinamenschecks. Childänderungen invalidieren Rootrevision.
Public sieht ausschliesslich sichere explizite Viewspalten, keine Basistabellen,
Grants/Audit/Origin- oder Objektkeys.

Kleine STACK-Dispatcher für Setup/Phasentests. Runner übernimmt nun explizite
vollständige base-SHAs aus dem Request in den Handoff und prüft deren Vorfahren-
beziehung. Kein globaler OpenCode-/Accountwechsel.

## Neu ausgeführte Testauswahl

Hauptkommando aus STACK: `./scripts/management/test.sh --phase MA-B`.
Äquivalent aus ADMIN: `python3 scripts/test_persistence_all.py` sowie
`python3 scripts/compatibility.py`. Runnerregression aus STACK:
`python3 scripts/management/test_review_gate.py`.

| ID | Tatsächlicher Nachweis |
|---|---|
| M07 | reales ili2pg-Schema;16 Cayenne-Entitäten, drei verbundene Klassen mit shared ili2db-PKs/UUIDs; zweiter cdbimport/cgen byte-identisch; realer ili2pg-Export durch unabhängigen ilivalidator validiert, UUIDs/MTEXT erhalten; echter Bootstart mit DataMap und getrennten Konten |
| M08 | echte UOW/Trigger-Transaktions-ID, Actor und DBuser; Rollback nach nachweislich erfolgreichem ORM-Flush; Einerpool Anna/Ben plus Schreiben ohne Actor; neue Contexts; FOR UPDATE/Stale; UTC-Wert bei PG-Zeitzone Pacific/Auckland unverändert |
| M09 | I/U/D und Keyword-Beziehung, Membershipinsert, Old/New/Rootbezug auch bei Parent-vor-Child-Löschung; Anzeigenamenredaction; No-op ohne künstliche Revision; absichtlich unmöglicher Auditinsert rollt Fachmutation zurück |
| M10 | reale Publicsicht positiv, echte Basistabellen/Grants/Audit gesperrt; Writer ohne Auditread/-write, DDL/TRUNCATE/Owner-SET-ROLE; Authz ohne Writes/Antragsbegründungen; Decisionmutation/Grantumdeutung und Principalidentitätsaustausch verweigert; verwendetes Schema und aktueller Versionszeiger geschützt |
| M11 | Installer idempotent; deaktivierter Membershipaudittrigger erkannt; tatsächliche HTTP-Readiness200→503→200 ohne Restart |
| M12 | echte additive Revision über bereits vorhandenen ORM-UUID-/Auditdaten; bekannte Setup-/Installer-Re-runs behalten Daten/IDs/Audit; schema-Aufruf führt keinen Reimport aus |
| M13 | begrenzter realer pg_dump/pg_restore in separate DB; IDs/Audit und Publicviewrechte erhalten |

Rohbelege: ADMIN/.runtime/persistence-all.log sowie .runtime/management-db/step-*.log
und gesicherte JUnit-XML pro tatsächlich ausgeführtem Gradle-Testschritt.
Integrations-Testoutputs sind nicht wiederverwendbar; keine UP-TO-DATE-/Buildcache-
Abnahme bei externer DB. Fehlende/skippte/fehlgeschlagene angeforderte Klassen
stoppen den Harness. Kompatibilitätsregression nach Boot-/Persistenzintegration
läuft gezielt neu; im M07-Nachweis mitreferenzieren, keine fremde Pflicht-ID
statt M07–M13 ausgeben.

## Abhängigkeiten und Nichtbetroffenheiten

Actor/PK/Transaktionen/Schema/Privilegien haben breiten Persistenz-Wirkungsbereich;
daher frischer zusammenhängender MA-B-Lauf und Startup-/M01-Regressionsprobe.
M02-Gateregression plus tatsächliche base-/head-Bindung beim neuen Reviewstart.
Neue HTTPreadiness gehört zur Persistenz, kein vorgezogenes OIDC-/UI-Gate.

Die fachlichen ILI-Modelle bleiben seit MA-A unverändert; echter XTF-Export wird
hier trotzdem am neuen Mapping validiert. Noch keine Admin-UI, JWT-/CSRF-
Benutzerkette, Portal-DB-Umschaltung oder Datei-Origin-/Gatewayfreigabe. Keine
Keycloak-/Superset-/ClickHouse-/Foundation-Vollsuite, keine Nativezusage. Audit
ist keine Rechtszertifizierung und kein Schutz gegen DBowner/Superuser.

## Bekannte Grenzen und Übergabe

CLI-Setup/JVM-Start sind lokal als eigener abgegrenzter Runtimeweg implementiert.
Integration in die Browser-/Gatewaykette folgt MA-C bis MA-E. Bestehender
Nutzerstack, private .env und Ladebelege bleiben unverändert. Test startet nur
bei freiem eigenem Runtimebereich; vorhandene persönliche Instanzen werden
nicht automatisch entfernt. Der Reviewer verwendet neue eigene Runtimepfade,
Ports, Volumes und Testcredentials und wählt eine eigene relevante Gegenprobe.

Erst lokale Produktcommits, danach exakter SHA-/Hash-Handoff. Nur validiertes
unabhängiges ABGENOMMEN an diesem Kandidaten öffnet MA-C.
