# EXECUTION_PLAN – MA-G: Storage, CSV-Anlieferung und Publikation

**Normativer Gesamtauftrag · 05.11.2026 · Revision 1.0**  
Die Anwendung wird im vorhandenen lokalen Compose-Verbund weiterentwickelt. Klassen-/Methodennamen in den Detailkapiteln sind konkrete Verantwortlichkeitsvorschläge; Umbenennungen sind zulässig, fehlende Verantwortlichkeiten oder abgeschwächte Verträge nicht. Bestehende geeignete Implementierungen wiederverwenden. Kein künstliches Framework und keine Klasse ohne reale Aufgabe.

## 1. Auftrag und Erfolgskriterium

Die bisherigen Storage-/Publikationsaltlasten werden **ersetzt**, nicht kompatibel weitergeführt. Zusätzlich entsteht ein durchgängiger CSV-only-Lieferweg mit zentraler fachlicher Autorisierung. Keine automatische Öffnung beliebiger GRETL-Skripte für Lieferanten.

Abnahmeziel:

> Eine berechtigte Person liefert CSV über das neue Jenkins-Plugin. Unberechtigte Personen und manipulierte Parameter erzeugen keine wirksame Lieferung. Nach tatsächlicher INTERLIS-/CsvValidator-Prüfung stehen ein neuer vollständiger Datenstand in ClickHouse und die zugehörigen Dateien im einzigen privaten Bucket bereit. PostgreSQL hält Metadaten, Lieferprovenienz und gültigen Veröffentlichungsstand; Admin/Sodata/Downloadberechtigungen funktionieren unverändert nach Rechteentzug und Containerneuerstellung. Der aktive Code benötigt weder alte Publikationsmodelle noch Teams-YAML, zweite Buckets oder Manifestreloads.

Die Löschfreigabe betrifft **den bisherigen Inhalt des identifizierten lokalen Entwicklungsbuckets `ch.so.daten`**. Sie ist keine Freigabe zum Löschen produktiver S3-Buckets, kompletter Garage-Volumes, fremder Projekte, PostgreSQL-Fach-/Auditdaten oder beliebiger Jenkins-Jobs.

## 2. Verbindliche Architekturentscheidungen

| ID | Entscheidung |
|---|---|
| A01 | Ein vorhandenes Compose-Projekt; die zehn Dauer-Services aus MA-F bleiben je einmal. Kein zweiter Runner-Stack, keine A/B-Instanzen, kein HA-Profil. Kurzlebige definierte Tools/Testcontainer sind zulässig. |
| A02 | Ein PG16/PostGIS-Server mit getrennten Datenbanken für Keycloak, Superset und Management. INTERLIS → unverändertes ili2pg → PostgreSQL; Cayenne für Fachpersistenz. Kein JPA/Hibernate. |
| A03 | Ein privater Bucket `ch.so.daten`; fachlich `open` und `restricted` ausschliesslich in PostgreSQL. Keine `public/`-/`private/`-Klassifikation im Speicher. |
| A04 | APISIX bleibt bei `openid-connect` + `forward-auth` zur Java-API. Kein Lua-Autorisierungsplugin, keine Casbin-Policyverteilung, kein APISIX→PG. Dateiübertragung bleibt beim internen rclone-Origin. |
| A05 | Genau ein technischer Jenkins-CSV-Pipelinejob und ein parametrisierbarer GRETL-CSV-Verarbeitungsweg für alle MVP-Datensätze. Keine Jobs pro Office/Dataset. |
| A06 | Lieferberechtigungen liegen in PG. Keycloak liefert Identität, nicht automatisch fachliche Rechte. Teams-Dateien und fachliche Jenkins-Matrix-ACL-Synchronisation entfallen. |
| A07 | Lieferrecht ist vom Lesen, Metadatenändern, Veröffentlichen und Verwalten anderer Lieferanten getrennt. Rechte gelten für den logischen Dataset; Ausgaben erben den Umfang. |
| A08 | Der gemeinsame Job bekommt nur einen serverseitig gebundenen Auftrag. Kein Benutzer darf über direkte Build-API, Replay, frei gewählte Parametersätze, Skripte oder Storage-Keys den Dispatcher umgehen. |
| A09 | CSV-only gilt für den **Input**. Standardoutputs sind vollständiges CSV, XLSX und Parquet; keine XTF-Metadatenanlieferung. Vorhandene interoperable Formate/Validierung bleiben, der alte Katalogtransport entfällt. |
| A10 | Replace und append erzeugen neue unveränderliche vollständige Snapshots. Eine Wiederholung desselben Auftrags erzeugt keine zweite Version und keinen doppelten Append. |
| A11 | Keine gemeinsame Transaktion über PG/ClickHouse/S3 behaupten. Private Stagingobjekte, expliziter Veröffentlichungspunkt, idempotente Abschlussoperation und kontrollierte ClickHouse-Projektion. |
| A12 | Entzug von `submit_data` wirkt bei neuen Aufträgen und vor dem verbindlichen Abschluss bereits laufender Aufträge. Publizierte Daten werden dadurch nicht rückwirkend gelöscht. |
| A13 | Keine API-Kompatibilitätsschicht, keine Aliasparameter, kein Legacy-Modus, kein automatischer Fallback. Einmalige Upgradeoperationen sind nicht Bestandteil des normalen Starts. |
| A14 | Beibehalten werden die fachliche Leserechtsverwaltung und die generische Auditierung. „Tabula rasa“ betrifft unnötige Architektur, nicht die Vernichtung nachvollziehbarer Entscheidungen. |

### 2.1 Bewusste Konkretisierungen für diesen Auftrag

- **Lieferantenverwaltung:** Zwei kleine Capabilities `submit_data` und `manage_submitters`. Die zweite ist nötig, damit Datenverantwortliche Lieferrechte in Admin vergeben können, ohne dadurch `publish`, `manage_metadata` oder `manage_access` zu erhalten. Keine allgemeine Rollen-Designeroberfläche. Initiale Zuweisung von `manage_submitters` über einen expliziten technischen Bootstrap.
- **Publikation:** Automatisch nur bei `published` Dataset, publizierter Ausgabe, aktivierter CSV-Anlieferung und ausdrücklich durch `publish` berechtigter Person eingeschalteter automatischer Publikation. Für nicht eingerichtete Datensätze keine Annahme mit stiller Veröffentlichung. Der MVP braucht keinen zusätzlichen Freigabeworkflow pro CSV.
- **Neue Ausgaben:** Im MVP wählt die liefernde Person eine bestehende Ausgabe. Neue Ausgaben werden in Admin angelegt; keine frei eingegebenen Jahreswerte, die implizit Katalogobjekte schaffen.
- **Technische Aufträge:** `di_ingest` verwaltet Submission, Execution, Checkpoints und Provenienz. Das ist kein neues universelles Workflowmodell. Die fachliche Berechtigung und die Veröffentlichungseinstellungen bleiben ausdrücklich in INTERLIS.
- **ClickHouse-Leserechte:** Keine automatische Vergabe an Lieferanten, Foundation-Reader oder Superset. Neue Datenbanken bleiben für gewöhnliche Konten gesperrt. Positivnachweise nutzen technische bzw. testweise eng berechtigte Konten. Persönliches SQL-Rechtemapping bleibt eine Folgephase.
- **Eine API, zwei Identitätstypen:** Synchrone Benutzeraktionen benötigen verifizierten Benutzer-Access-Token; Hintergrundaktionen eine separate ausführende Serviceidentität plus gebundene Execution. Kein gespeichertes Benutzer-JWT als Langzeitauftrag.

## 3. Zielbild und Datenwege

```text
Browser ── OIDC ──> Jenkins-Anlieferungsplugin
                         │ Benutzer-Token + interner Dienstnachweis
                         ▼
                  Admin Ingestion API ──> PostgreSQL
                         │ bindender Lieferauftrag
                         ▼
                genau ein Jenkins-CSV-Job
                         │ festes GRETL-Skript + unveränderlicher Plan
                         ├─> echte CsvValidator-Prüfung
                         ├─> ClickHouse: neuer privater vollständiger Snapshot
                         ├─> ch.so.daten: private Dateien
                         └─> Admin: verifizierte Ergebnisbelege / Commit

Sodata ── lesende Views ──> PostgreSQL
Client ──> APISIX ── forward-auth ──> Admin ──> PostgreSQL
             └─ bei Erlaubnis ──> rclone Origin ──> ch.so.daten/downloads
```

Der Origin muss im tatsächlichen Compose-Upstream stehen; kein Diagramm und kein Test darf ihn versehentlich durch direkten anonymen S3-Abruf ersetzen. Eingangsdateien und Prüfberichte unter `ingestion/` sind nicht über den Download-Origin erreichbar.

## 4. Ausgangsstand und Versionsvertrag

Der belegte Ausgangspunkt ist MA-F, siehe [SOURCES.md](SOURCES.md). Bekannt sind u.a. `DeliveryRegistrationService`, `AuthorityService`, `AuditedUnitOfWork`, `CatalogAction`, die DB-Sodata-Sichten, `compose_runtime.py`, `setup-compose.py` und der vorhandene Reviewrunner. Im bisherigen Plugin sind Organisationsjob-Generator, Teams-YAML und separate Jenkins-Testbenutzer noch aktiv. Diese werden nicht weiter ausgebaut.

Die Gesprächshistorie erwähnt einen S2-Ladeauftrag. **Ein früherer Auftrag ist kein Nachweis vorhandenen Codes.** MA-G0 muss lokale Branches, uncommittierte Nutzerarbeit und die konkreten Implementierungen prüfen. Ein tatsächlich vorhandener CsvValidator-/ClickHouse-Baustein wird integriert. Eine nur beschriebene Komponente wird nicht als fertig vorausgesetzt. Keine fremde Brancharbeit überschreiben und keine zweite Loaderbibliothek nur wegen einer abweichenden Repoablage erstellen.

| Komponente | Vorgabe |
|---|---|
| Admin / Sodata | Bestehende Spring-Boot-4.1.2-/Java-25-Basis und Cayenne 5.0-M3 beibehalten, sofern MA-G0 den tatsächlichen Stand bestätigt. Kein beiläufiges Frameworkupgrade. |
| Jenkins / Plugin | Bestehende Jenkins-LTS-/Java-21-Basis; passende konkrete `oic-auth`-Version in G0 prüfen und pinnen. Plugin-POM/BOM, Runtime und JCasC müssen zusammenpassen. Keine ungeprüfte `latest`-Abhängigkeit. |
| GRETL | Vorhandene getestete GRETL-/Java-17-Ausführung und CsvValidator verwenden. Keine Migration auf gretl-runtime oder Hop als Nebenauftrag. |
| PG / Garage / APISIX / rclone / CH | MA-F-Pins beibehalten; benötigte Verhaltensweisen am echten Image prüfen. Keine Engine-/Majorwechsel. |
| INTERLIS Tools | Bereits gepinnte ili2pg/ili2c/ilivalidator-Versionen und Modellabhängigkeiten nutzen; Tooländerungen nur bei belegtem Blocker. |
| OpenCode | Tatsächlich installierte 2.x-CLI, bestehender DeepSeek-Zugang, Modell-ID nachweislich `deepseek/deepseek-flash` für Flash 1017 oder belegte entsprechende Providerkennung; kein stiller Modellwechsel. |

Ein notwendiger Versionswechsel wird als eng begründete Entscheidung mit Betroffenheitsprüfung dokumentiert. Kein Erzwingen einer nicht belegten Bibliotheks-API. In G0 insbesondere OIDC-Tokenzugriff aus einer echten Jenkins-Sitzung sowie ein realer CsvValidator-Lauf prüfen.

## 5. Repositoryverantwortlichkeiten

| Kürzel / Repo | Verantwortung |
|---|---|
| STACK – `dateninfrastruktur-dev-stack` | Einzige Compose-Laufzeit; Storage-/Keycloak-/Jenkins-Konfiguration, sichere Umstellung, Integrationstests, zentrale Spezifikationen und Reviewrunner. |
| ADMIN – `dateninfrastruktur-admin` | Fachmodelle, Schemaevolution, Lieferrechte, Submission-/Execution-API, Veröffentlichung und Provenienz. Keine Containerorchestrierung. |
| PUBLIC – `dateninfrastruktur-sodata` | Ausschliesslich DB-Katalog; Link zur Anlieferung, verfügbare Versionen/Downloads. Keine Writercredentials. |
| PLUGIN – `dateninfrastruktur-jenkins-gretl-plugin` | Schlanke Anlieferungsoberfläche, sichere OIDC-Weitergabe, Upload/Dispatch, ein Job, Status ohne Rohlogzugriff. |
| JENKINS – `dateninfrastruktur-jenkins-dev` | Reproduzierbares Jenkinsimage samt geprüftem Plugin/OIDC, feste GRETL-Toolchain, JCasC und offline/online Buildvertrag. |
| TOPICS – `dateninfrastruktur-themenrepo` | Ein generischer CSV-Workflow, geprüfte INTERLIS-Datenmodelle und deklarative CSV-Verträge. Keine Personen-/Team-/Job-ACL-Verwaltung, kein lebender Metadatenkatalog. |

Kein siebtes Produktrepo, kein neues Microservice-Deployment, kein übergeordnetes Git-Repo. Der gemeinsame Mutterordner ist Codex-Projekt und Workspace; die unabhängigen Reviews verwenden eigene Kopien derselben Geschwisterstruktur.

## 6. Reihenfolge und Phasengates

### MA-G0 – Bestand, Zielverträge und Risikoproben

Liefern: aktueller SHA-/Dirty-State aller sechs Repos; verbindliche Behalten/Entfernen-Zuordnung; konkrete Modelländerung; überprüfter CSV-Vertrag und OIDC-Tokenweg; Reviewrunner auf G-IDs erweitern; lesender lokaler Bucket-/DB-/Jenkins-Bestand. Eine `WORK_QUEUE.md`, eine kleine `DECISIONS.md` nur für reale Abweichungen, `BASELINE.md` ohne Secrets.

Keine produktiven Änderungen oder Bucketlöschung in dieser Phase. Kleine isolierte Spikes sind zulässig. G0 muss keine voll ausgebaute Pipeline erstellen. Pflichtnachweise G00–G04.

### MA-G1 – Ein privater Bucket und Entfernung des Storage-Legacys

Liefern: idempotentes Freshsetup mit drei technischen Storage-Identitäten; nur `ch.so.daten`; origin/operator mit festen kanonischen Pfaden; kein Defaultkey-Fallback; erneuter Start erweitert keine Rechte. Neue Catalog-Modellversion mit Entfernung von `storageProfile`/`legacyAccessUrl` und zugehörigem sicheren DB-Upgrade; Access-Modell nur erforderlichen Import umstellen, weitere Fachlogik folgt G2. Bestehende private Distributionen werden bytegleich übernommen. Der ausdrücklich freigegebene alte lokale Bucketinhalt wird einmalig entfernt, nie beim normalen Start.

Zunächst isolierter Übernahme-/Negativnachweis, unabhängiges Review, danach eng begrenzter lokaler Storagecutover. Noch kein neuer CSV-Job nötig. Pflichtnachweise G10–G19.

### MA-G2 – Fachmodell, Berechtigungen und Lieferauftrags-API

Liefern: `submit_data`, `manage_submitters`, CSV-Konfiguration je Dataset, Adminoberfläche und Bootstrap, `di_ingest`-Aufträge/Zustandsverträge, Zugriffsmatrix, Commit-/Widerrufssynchronisierung. Das Backend hat testbare Benutzer- und Executorendpunkte. Frische DB und Upgrade des vorhandenen Bestands funktionieren; Audit bleibt vollständig. Keine direkte UI-Grantvergabe ausserhalb des Fachvertrags.

Die neuen Modelle werden spätestens hier endgültig fachlich festgeschrieben; keine nachträglich anders belegte veröffentlichte Modellversion. Pflichtnachweise G20–G29.

### MA-G3 – Jenkins-OIDC, neues Plugin und generischer Job

Liefern: echter Keycloak-Codeflow, verifiziertes `iss/sub`, Upload, zentraler Auftrag, technische Jobausführung, Status und geschützte Berichte. Exakt ein verwalteter CSV-Job. Alte Seed-/Organisations-/Teamslogik und Parameter werden entfernt. Keine Lieferanten-Job/Build-Rechte. Alle Einstiegspfade einschliesslich Build-API/Replay/Artefakte prüfen.

Die Jobtechnik wird mit einem **ausdrücklich test-only** Probeprozessor geprüft. Dieser ist weder normale Pipelineoption noch ein vermeintlich publizierter Fachdatensatz; kein `MOCK_SUCCESS` im Produktstart. Echte fachliche Verarbeitung folgt G4. Pflichtnachweise G30–G39.

### MA-G4 – Echte generische CSV-Verarbeitung und Wiederanlauf

Liefern: fest versionierter CSV-Vertrag; CsvValidator; replace/append mit Gesamtzustandsprüfung; unveränderliche CH-Snapshots und Dateioutputs; Hash-/Zeilen-/Typbelege; PG-Veröffentlichung mit neuer Rechteprüfung; kontrollierte CH-View-Projektion; Retry ohne doppelte Version. Zwei repräsentative Datensätze mit mehreren Ständen, mindestens einer restricted. Keine automatische SQL-Leseberechtigung aus `submit_data` ableiten.

Gültige und fehlerhafte Daten tatsächlich durch GRETL/Jenkins ausführen. Pflichtnachweise G40–G49.

### MA-G5 – Fachpfad, endgültiger Cutover und Altlastenabnahme

Liefern: vollständige Benutzerfolge im normalen Compose; Widerruf vor Jobstart und vor Commit; Parallelität verschiedener Datensätze; derselbe Dataset geordnet; Fehler/Wiederanlauf; Recreate; Entfernung aller alten aktiven Pfade und eigenen Altjobs/-konten. Abschlussinventur, Bedienungsdoku, ehrlicher Status der lokalen Umstellung.

Ein unabhängiger Endreview, kein zusätzlicher identischer Komplettlauf nach dessen Abnahme. Review auf eigenen Quellen; lokale Nutzerumstellung danach separat gezielt belegen. Pflichtnachweise G50–G59.

## 7. Was „Tabula rasa“ hier verbindlich bedeutet

Neue Ziel-API statt `v1`-/`legacy`-Flags neben alten Routen. Neue Pluginpakete dürfen alte Implementierungen ersetzen. Alte Klassen werden gelöscht, nicht nur ungenutzt mitgebaut. Kein `readResolve`, keine Aliascredentials, keine Wrapper für alte Jenkins-Schritte, kein Manifest-/XTF-Fallback. Kein pauschales Rename von `datenportal` über Fremdlizenzen, Klassenherkunft oder unveränderliche Reviewberichte.

Einmalige, eng begrenzte **Datenübernahme** ist keine dauerhafte Kompatibilität. Sie darf alte Namen lesen, darf nicht im normalen Start/Setup/Webimage enthalten sein und wird nach abgeschlossenem lokalem Cutover aus dem aktiven Toolprofil entfernt. Historie bleibt über Git und eingefrorene Nachweise erhalten. Den konkreten Löschkatalog beschreibt SPEC_CLEANUP_CUTOVER.

## 8. Übergreifende Implementierungsregeln

- Keine neuen Personenrechte in Tokens/Dateien cachen. Immutable Modell-/Artefakthashes dürfen gecacht werden.
- Keine Benutzer-JWTs, Refresh Tokens, Uploadbytes oder SQL-Bindings in Reports, Buildparametern oder Chat.
- Keine Benutzerkonten durch Namens-/E-Mailgleichheit migrieren. Belegte Keycloak-Subjects übernehmen.
- Kein allgemeiner Writerzugang an Browser; keine frei wählbare URL/S3-Key/SQL-/Groovyzeichenkette als Ausführungsplan.
- Keine langen PG-Transaktionen über Dateiübertragung/CsvValidator/CH-Loads. Abschlussprüfung und Fachcommit bilden eine kurze PG-Transaktion.
- Vorhandene Tests nicht löschen, um rot zu grün zu machen. Tests alter **entfernter** Produktverträge werden durch Tests des neuen Vertrags ersetzt und in der Retirement-Matrix begründet.
- Die normale Compose-Topologie ist die Integrationstesttopologie. Keine Python-Docker-Nebenwelt wie vor MA-F.

## 9. Revieworganisation

Vorhandene `scripts/management/review-phase.py`, `review_gate.py`, Reviewer-Agentdefinition und Gate-Tests wiederverwenden. Phasen-Mapping nach MA-G erweitern, neue Spec-Dateien einschliesslich JSON-Verträge hashen und alle sechs Repos aufnehmen. Kein hartcodierter alter MA-F-Request, kein Weiterprüfen gegen die alten `PHASE_CHECKS`.

Pro Phase: implementieren → gezielte Tests → lokaler Commit je betroffenem Repo → Request mit Base-SHAs → Handoff mit tatsächlichen Head-SHAs → neue unabhängige Sitzung. Der Handoff entsteht **nach** den Produktcommits. Eigenes Urteil von Codex ist nie das unabhängige Gate.

Nach Findings: kleinster tragfähiger Fix, Ursachenprobe, betroffene Nachbarn, neuer Kandidat und Delta-Review. Ein JSON-Formatfehler am Report erfordert keine fachliche Vollwiederholung; der Reviewer selbst korrigiert den Report, ohne Urteil/Belege umzudeuten. Keine Produktkorrektur durch den Reviewer.

## 10. Übergabe

Ein vollständiger Code- und Betriebsstand mit aktualisierter Root-README, Admin-/Jenkins-Anleitung, lokalem Cutoverbericht und Cleanup-Matrix. Schlussbericht getrennt nach: implementiert/getestet, unabhängig abgenommen, auf der lokalen Nutzerinstanz angewendet, noch echte Blocker. Keine Behauptung eines Livezustands allein aus synthetischen Tests.
