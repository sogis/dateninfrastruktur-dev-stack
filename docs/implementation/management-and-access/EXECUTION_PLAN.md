# Phase 2 – Management, Metadaten, Audit und geschützte Downloads

**Verbindlicher Gesamtauftrag für Codex · Revision 1.0 · 4. November 2026**  
**Implementierung:** Codex. **Unabhängige Prüfung:** OpenCode **2.x**, **DeepSeek Flash 1017 über die vorhandene DeepSeek-API-Verbindung**, nach jeder Phase.  
**Status:** Spezifikation, keine hier bereits implementierte oder laufzeitgeprüfte Software.

> Ein Gesamtauftrag, mehrere blockierende Gates: **implementieren → gezielt testen → lokal committen → autonom unabhängig prüfen → erst nach `ABGENOMMEN` weiter**. Bei Nacharbeit nur den tatsächlich betroffenen Wirkungsbereich erneut testen. Keine künstliche Volltestpflicht, aber auch kein Übernehmen alter Belege für geänderte Sicherheitsverträge.

## 0. Geltung und Einstieg

Dies ist die vereinbarte Management-/Access-Etappe **2-0 und 2A–2E**. Sie ist **nicht** der ältere CSV-/ClickHouse-Ladeauftrag `schritt-2-datenladen` mit `S2-P0` bis `S2-P4`. Dessen Implementierung und Historisierung erhalten. Neue eindeutige Arbeits-IDs: **MA-0, MA-A, MA-B, MA-C, MA-D, MA-E**. MA-E enthält den abschliessenden zusammenhängenden Integrationstest; kein doppeltes identisches Schlussreview.

Arbeitsbereich ist der gemeinsame Elternordner der Repos. Kürzel:

- `STACK` = `dateninfrastruktur-dev-stack`.
- `PUBLIC` = `dateninfrastruktur-sodata`.
- `ADMIN` = neues oder bereits vorhandenes `dateninfrastruktur-admin`.
- `TOPICS` = `dateninfrastruktur-themenrepo`.
- `PLAN` = `STACK/docs/implementation/management-and-access`.

Die Workspace-`AGENTS.md` muss für diese Etappe aktualisiert sein; [AGENTS.workspace.md](AGENTS.workspace.md) ist die Vorlage. **Codex arbeitet vom gemeinsamen Elternordner**, OpenCode wird ausschliesslich als unabhängiger Reviewer gestartet. Workspace-/Repo-AGENTS ausdrücklich lesen, dann diesen Plan sowie **vollständig**:

1. [SPEC_MODELS.md](SPEC_MODELS.md) – Klassen, Attribute, Beziehungen und Invarianten.
2. [SPEC_PERSISTENCE_AUDIT.md](SPEC_PERSISTENCE_AUDIT.md) – ili2pg, Cayenne, Transaktionen und Audit.
3. [SPEC_APPLICATIONS_GATEWAY.md](SPEC_APPLICATIONS_GATEWAY.md) – Fachservices, Controller, Authentifizierung, HTTP und Dateien.
4. [TEST_PLAN.md](TEST_PLAN.md) – Phasenpflichten und risikobasierte Delta-Prüfung.
5. [CODEX_STARTPROMPT.md](CODEX_STARTPROMPT.md) und [OPENCODE_REVIEW_PROMPT.md](OPENCODE_REVIEW_PROMPT.md).

Das ist gemeinsam **eine** Spezifikation. Quellen in [SOURCES.md](SOURCES.md); gezielte Agentenregel-Ergänzung in [AGENTS_ERGAENZUNG.md](AGENTS_ERGAENZUNG.md). Ergänzungsdateien sind keine optionalen Lesehinweise.

### 0.1 Beobachtete Ausgangslage

| Quelle | Untersucht / Bedeutung |
|---|---|
| `sogis/dateninfrastruktur-dev-stack` | `be32c293a5af0d3138395b64e2a73d40ec0f6542`: lokale Grundinstallation, APISIX/Garage/rclone, Keycloak/Superset/PostgreSQL/ClickHouse und technische Prüfungen |
| `sogis/dateninfrastruktur-sodata` | `7eff0b138c23524ac522231ce312d4c6659635dc`: Boot 4.1.0, Java 25, JTE/HTMX, XTF/DuckDB-Snapshot, Lucene |
| `sogis/dateninfrastruktur-themenrepo` | zuletzt untersuchter Stand `7d99ceec0e392a5f12b602c0840c4762c7213fba`; lokalen neueren Ladecode feststellen |
| Adminrepo | Bei Recherche nicht abrufbar (404); daraus nicht auf einen leeren lokalen Ordner schliessen |
| Katalogmodelle und `stdcols.sql` | Inhaltliche Grundlage, keine zwingende physische Rückwärtskompatibilität der neuen Modelle |

Quelllektüre ist keine Laufzeitabnahme. In MA-0 aktuelle lokale HEADs/Dirty Trees prüfen, neue sinnvolle Änderungen erhalten und nicht auf diese historischen SHAs zurücksetzen. Bestehende Namespace-Bereinigungen erhalten, insbesondere `DATENINFRASTRUKTUR_*` und die neue Jenkins-Plugin-ID. Historische Nachweise nicht rückwirkend umschreiben.

### 0.2 Verbindliche Architektur

1. PostgreSQL ist führend für Katalog, Zugriffsstatus, Identitätsreferenzen, Zuständigkeiten, Anträge und Entscheide.
2. Fachmodell: INTERLIS 2.4 → unverändertes ili2pg → PostgreSQL; Admin-Persistenz mit Apache Cayenne, **kein Hibernate/JPA**.
3. Neue Familie `SO_AGI_DataInfrastructure_*`. Keine obligatorischen Datasheet-/PublishedCatalog-Nachfolger. Öffentliche Views sind keine zweite Datenhaltung.
4. Zwei Anwendungen: Sodata als weitgehend lesendes Portal; Admin für Verwaltung und Selbstbedienung. Authorization API zunächst abgegrenztes Package im Admin-Backend.
5. Berechtigungen hängen **ausschliesslich am ganzen fachlichen Datensatz**. Ausgaben, Datenstände und Dateien haben keine eigenen Benutzer-ACLs.
6. `AccessLevel = open | restricted`. Redaktionelle Veröffentlichung und technische Auslieferbarkeit sind davon getrennt.
7. Neue verwaltete Dateien privat in S3; Öffentlichkeit wird am Downloadzugang entschieden. Dateipfade müssen beim Statuswechsel nicht wechseln.
8. **APISIX `forward-auth` → Java Authorization API → PostgreSQL**. Kein Lua-Authz-Plugin, keine Casbin-Policydatei, keine DB-Verbindung aus APISIX.
9. Dateiübertragung durch internen Origin, vorläufig rclone. Admin/Sodata streamen keine Fachdaten.
10. Generische PostgreSQL-Audittrigger plus fachlich modellierte Entscheide. Audit-Installation ausserhalb von ili2db, optional gesteuert durch vorhandene Modellmetainformationen.
11. Eine nach dem Commit neu begonnene Autorisierungsprüfung liest aktuelle Daten vom PostgreSQL-Primärsystem. Keine Permission-Caches; laufende Downloads werden nicht rückwirkend beendet.
12. Jede Phase muss am konkreten Quellstand getestet und autonom unabhängig abgenommen werden.

### 0.3 Nichtziele

Keine persönliche ClickHouse-/Superset-Rollensynchronisation, neuen Dashboards, Datenwerkstatt, Agentic BI, AIO-/LDAP-Produktionsanbindung, GDI-weite IAM-Plattform, OpenShift-Manifeste, Registry-Releases, Event Sourcing oder vollständige temporale Datenbank. Kein neues generisches ili2db-/Auditprodukt. Keine vorsorglichen Redis/Kafka/etcd-Dienste.

Nicht alle Metadatenfelder benötigen bereits einen komfortablen Editor; vorhandene Informationen dürfen jedoch nicht verlorengehen. Keine neue vollständige DCAT-Exportpipeline. Alte Rohartefakte im DB-Modus nicht als aktuelle öffentliche DB-Sicht ausgeben. Der bestehende ClickHouse-Lader wird nicht neu implementiert.

## 1. Verbindliche Versionen und frühe Kompatibilitätsprüfung

| Baustein | Vorgabe |
|---|---|
| Spring Boot | **4.1.2**, laut offizieller Projekt-/Releaseseite aktuell stabile GA am 4.11.2026. In MA-0 nochmals prüfen; eine nachweislich neuere offizielle GA darf begründet gewählt werden. Danach exakt pinnen. Keine RC/M/SNAPSHOT. |
| Apache Cayenne | **5.0-M3**, explizit gewünschter veröffentlichter Alpha/Milestone. Runtime/Buildtools gleicher Version. |
| Java | **25** für Admin/Sodata, passend zur bestehenden Anwendung. Cayenne 5-M3 verlangt mindestens Java 21. Bestehender GRETL-/Java-17-Kontext bleibt unangetastet. |
| Build/Abhängigkeiten | Passenden vorhandenen Gradle Wrapper verwenden. Spring Security, JDBC und Jackson über Boot-BOM. Kein alter Spring-/Jackson-Stack als unbeabsichtigte Transitivabhängigkeit. |
| PostgreSQL | Hauptversion 16 beibehalten, neue Management-Datenbank mit eigenen Konten. PostGIS-Voraussetzung von ili2pg konkret prüfen. |
| ili2pg/ili2c/ilivalidator | Kompatible tatsächlich verfügbare Releases und Hashes in MA-0 pinnen. Keine erfundenen Versionsnummern. |
| APISIX/Keycloak/Garage/rclone | Vorhandene Versionen beibehalten; konkrete Plugin-/HTTP-Verträge am laufenden Image prüfen. |

Cayenne 5-M3 verwendet `org.apache.cayenne.runtime.CayenneRuntime`; DataNodes werden programmatisch zugeordnet. CommitLog gehört inzwischen zum Kern. Kein unbesehenes 4.2-Rezept mit `ServerRuntime`, alten XML-DataNodes und separatem `cayenne-commitlog` übernehmen. Siehe Primärquellen und Persistenzvertrag.

MA-0 führt einen **kleinen** Boot/Cayenne/PostgreSQL-Spike durch: Runtime startet, eine Transaktion setzt einen lokalen Actorwert und schreibt/liest über Cayenne. Die vollständige Modellabbildung folgt in MA-B. Ein belegter M3-Blocker wird zuerst gezielt bearbeitet. Ein Wechsel auf 4.2.3 ist nur nach reproduzierbarem M3-Problem und unabhängiger Prüfung zulässig, nicht aus Gewohnheit. Keine stille Ersetzung durch Hibernate.

JVM ist der verpflichtende lokale Startweg. Vorhandene Native-Buildoptionen nicht entfernen. Native-Kompatibilität nicht ungeprüft behaupten. Ein gezielter Native-Smoke bei verfügbarer Toolchain ist sinnvoll; keine Native-Vollmatrix nach jedem fachlichen Fix und keine heimliche zweite Architektur bei einer Native-Grenze.

## 2. Repositories und Paketgrenzen

| Repo | Aufgabe |
|---|---|
| ADMIN | Modelle, DB-Setup/Migration, Cayenne-Mapping, Auditinstaller, Fachservices, Admin-/Self-Service-Oberfläche, Authorization API, Legacyimport |
| PUBLIC | DB-Katalogadapter, Suche/Detailseiten, vorhandene Darstellung erhalten, Links auf Selbstbedienung/Downloads |
| STACK | Compose, technische Konten, OIDC/APISIX/Origin, Tests, autonome Reviewausführung, zentrale Anweisung |
| TOPICS | Nur nötiger Anschluss bereits vorhandener Daten-/Metadatenartefakte; keine zweite schreibende Metadatenquelle |
| Jenkins-Repos | Nur falls ein gemeinsamer Aufruf tatsächlich angepasst werden muss; kein vorsorglicher Umbau |

Genau ein neues Anwendungsrepo ADMIN. Modellquelle zunächst `ADMIN/models`, keine dritte Anwendung und kein Shared-Repo nur für Entitäten. Sodata verwendet einen stabilen SQL-Lesekontrakt und muss keine schreibbaren Cayenne-Entitäten aus dem Adminprojekt importieren.

```text
ADMIN/
  models/                               # zwei ILI-Modelle, XTF-Fixtures, Invarianten
  db/mapping-profile.json                # Pins, Optionen, Modellhashes
  db/migrations/                        # Zusatzconstraints, Views, Audit
  db/audit-policy.json                  # konkret aufgelöste Auditabdeckung
  src/main/resources/cayenne/
  src/main/java/ch/so/agi/dateninfrastruktur/admin/
    config/ identity/ catalog/ access/ audit/ persistence/ authorization/ web/ tools/
  src/test/... 
  docs/management-operations.md
  docs/schema-lifecycle.md
PUBLIC/
  .../catalog/query/                    # neuer JDBC-/DTO-Lesepfad
  ... bestehende Controller/ViewModels/Templates gezielt anpassen
STACK/
  services/management/
  services/apisix/
  scripts/management/
  docs/implementation/management-and-access/
  .runtime/management-review/           # ignorierte isolierte Kandidaten/Rohbelege
```

Das sind Zielpfade, keine Behauptung, sie existierten bereits. Methodenverträge der Begleitdateien sind konkrete Verantwortlichkeiten. Kein Interface/Factory/DAO pro Ein-Zeilen-Funktion ohne echten Bedarf.

## 3. Phasen und Gates

### MA-0 – Bestand, Versionen und autonome Reviewkette

Liefern: tatsächliche Repo-/Toolstände und minimal aktualisierte AGENTS; Adminrepo sicher initialisieren; Boot/Cayenne-Spike; kleine ili2pg/Postgres-Probe zur Extensionfrage; konkrete Versionen; vorhandenen OpenCode-Reviewrunner aus dem Ladeauftrag wiederverwenden oder minimal ergänzen. Eine `WORK_QUEUE.md`, maximal eine kurze `DECISIONS.md` für echte Abweichungen.

Tests `M00–M02`: vorhandene benötigte Dienste gezielt erreichbar, tatsächliche Modellexekution mit Lese-/Shellwerkzeugen, falscher SHA oder fehlender Reviewreport öffnet kein Gate. Kein kompletter Foundation-Rebuild. **Erst autonome Abnahme, dann MA-A.**

### MA-A – INTERLIS-Modelle und valide Beispieldaten

Liefern: zwei neue Modelle gemäss SPEC_MODELS; stabile UUIDs, eindeutiger Rechteanker, Serien ohne Metadatenkopien, Principal/Gruppen, Zuständigkeiten, Anträge, immutable Entscheide und beendbare Grants. Wenige Audit-Metaattribute, kleine positive/negative XTF-Fixtures. Zuständigkeit für jede Invariante: Modellvalidator, DB-Constraint oder Service.

Tests `M03–M06`: echte Kompilation/Validierung, Geschäftsabläufe darstellbar, Invalidfälle richtig abgelehnt. Reviewer prüft Code/Modelle und eine eigene Gegenprobe. Noch kein grosser UI-Bau.

### MA-B – PostgreSQL, Cayenne und Audit

Liefern: Management-DB/Least-Privilege-Konten; ili2pg-Schema; PK/OID-/Beziehungsabbildung mit Cayenne; ergänzende kontrollierte Migrationen; öffentliche Views; Actor-Transaktionshülle; generische Audittrigger, Coverageprüfung und minimaler externer Installer. Echter technischer Import-/Bootstrapakteur, Schutz unveränderlicher Entscheide.

Tests `M07–M13`: echte PostgreSQL-Integration, kein H2. Transaktion/Connection, Rollback, Actor-Poolleck, I/U/D und Assoziation, Audit-/Schema-/Public-Rechte, cgen und XTF-Roundtrip, idempotentes Setup. Ein begrenzter Backup/Restore-Smoke auf isolierten Beispieldaten.

### MA-C – Admin, Nutzer-Selbstbedienung und Autorisierungskern

Liefern: Boot/JTE/HTMX-Admin; kleiner Metadateneditor; `/access/*` für Selbstbedienung; OIDC mit geprüftem JWT; CSRF; Anfrage/Genehmigung/Ablehnung/direkte Vergabe/Entzug; Zuständigkeit je Dataset; Konkurrenzschutz und Idempotenz; Auditansicht. Authorization API funktioniert mit aktuellen DB-Entscheiden, Datei-Origin folgt in MA-E.

Tests `M14–M20`: tatsächlicher Browserlogin und ein durchgängiger Nutzerablauf, gezielte Service-/HTTP-Fehlerfälle. Unzuständige Person, manipuliertes Subject, doppelter Entscheid, veraltete Bearbeitung und CSRF scheitern nachvollziehbar. Nicht alle Browser und Felder kombinatorisch testen.

### MA-D – Sodata liest direkt PostgreSQL

Liefern: CatalogQueryService/DB-Adapter, öffentliche Views und eingeschränktes Konto; Suche/Filter/Pagination/Detailseiten/Serien erhalten; ausgewählte Legacy-Metadaten einmalig mit Konfliktbericht importieren. DB-Modus benötigt weder XTF/current.json noch DuckDB/Jenkins zum Start. Alte vollständige Katalogartefakt-Endpunkte im DB-Modus deaktivieren, sofern kein echter gefilterter Export implementiert ist. Links auf `/access/*`, keine Schreibrechte im Portal.

Tests `M21–M25`: sichtbare Daten/Facetten/Details korrekt, Drafts/Grants/Audit/storage intern verborgen, kein heimlicher Fallback auf alten Snapshot. Änderungen von Admin erscheinen ohne Reload auch auf zweiter Portalinstanz. Nur betroffene Katalog-/Template-Regressionen, keine unveränderte WebR-Gesamtsuite.

### MA-E – Private Downloads und Gesamtintegration

Liefern: APISIX-Standardplugins OIDC+forward-auth, feste interne Authorization API, privater S3-Origin, GET/HEAD/Range und kanonische Distribution-URLs. Übernommene öffentliche Pilotkopien/Altpfade unter eigener Kontrolle absichern. Sofortiger Grant-/Revoke-/open↔restricted-Effekt, fail closed und kein unkontrollierter Cache. Test mit zwei Gateway- und zwei Authorization-Instanzen gegen denselben PG-Primärbestand, ohne Kubernetesinstallation.

Tests `M26–M33`: reale Datei-Bytes und Negativpfade; zwei historische Dateirepräsentationen erben Datasetrecht; Rechteentzug mit demselben noch gültigen Token. Abschliessende kurze E2E-Folge: Metadaten ändern, Antrag, Freigabe, Download, Entzug, Audit, Neustart. **Das MA-E-Review ist der Abschlussreview**, keine identische Zusatzprüfung ohne neues Risiko.

## 4. Durchgängiges Abnahmebild

Anna findet restricted Metadaten anonym. Sie meldet sich an, beantragt READ. Claudia entscheidet im eigenen Zuständigkeitsbereich. Decision, Grant und Audit werden gemeinsam committet. Annas nächste Anfrage wird erlaubt, Bens verweigert. Claudia widerruft Annas Grant; derselbe Token erhält danach keine Datei mehr. Ben bekommt eine direkte Vergabe ohne fiktiven Antrag. Metadatenänderung erscheint im öffentlichen Portal. AccessLevel-Wechsel betrifft alle technisch verfügbaren Dateien dieses Datasets, ohne Verschieben im Storage. Kein ungeschützter alter lokaler URL-Weg darf dasselbe verwaltete Objekt umgehen.

Eigene öffentliche Originaldaten im Internet können nicht zurückgeholt werden; Pilotkopien eindeutig als technische Demo kennzeichnen. Nicht behaupten, fremde S3-Originale seien durch die lokale Berechtigung geschützt.

## 5. Arbeitszyklus und Änderungen an abgenommenen Phasen

1. Betroffenen Vertrag bestimmen, klein implementieren, passende Tests.
2. Reviewrequest mit base-SHA, geändertem Umfang, Kommandos/Belegen erstellen – **ohne den eigenen noch nicht bekannten Commit-SHA**.
3. Produktcode/Tests/Request pro Repo lokal committen; fremde Änderungen auslassen.
4. Danach Handoff mit vollständigem Repo-SHA-Satz und Spec-/Requesthash erzeugen.
5. Codex startet frisches OpenCode-Review, wartet auf dessen Ende und prüft das strukturierte Ergebnis.
6. Nur `ABGENOMMEN` für denselben Kandidaten schliesst das Gate.

Nach Finding: reproduzierender Test, kleinster tragfähiger Fix, neue Commits. Vor Review eine Delta-Auswahl mit geänderten Funktionen, abhängigen Verträgen, neu auszuführenden Tests und begründet übertragbaren Belegen. Ein Modellfix in MA-C öffnet die **betroffenen** MA-A/B-Verträge, nicht automatisch alle vorherigen Tests. Ein geänderter Authz-SQL-Ausdruck verlangt frische Grant-/Gruppen-/Zeit-/Widerrufsproben, aber keine komplette Superset-Suite. Versions-/Pool-/Transaktionsänderungen haben breiteren Wirkungsbereich.

Der Reviewer kann Tests ergänzen und verwirft unbegründete Übertragungen. `NOT_REQUIRED` wegen Nichtbetroffenheit ist nicht `NOT_EXECUTED` bei fehlender Pflichtausführung. Kein Gate durch Überspringen, gelockerte Assertions oder einen willkürlich geänderten Erwartungswert öffnen.

## 6. Umsetzungshilfen, Betriebsgrenzen und Artefakte

Vorhandene Skripte wiederverwenden; ein Dispatcher mit Subcommands genügt. Zielverträge, noch zu implementieren:

```text
scripts/management/preflight.sh
scripts/management/setup.sh
scripts/management/up.sh
scripts/management/import-legacy.sh --dry-run|--apply <datei>
scripts/management/test.sh --phase MA-B [--selection <datei>]
scripts/management/review-phase.sh MA-B --request <pfad>
```

Standardstart erhält Nutzerarbeit, Daten, UUIDs, Secrets, Entscheide, Grants und Audit. Kein Demo-Reset bei jedem Start. Setup/Migration explizit; Anwendung verfügt nicht über DDL-/Ownerrechte. Alte Datenportal-Repos und echte externe Buckets nie verändern. Keine `docker system prune`, keine ungezielte Volumelöschung, keine globalen Accountänderungen. Review verwendet eigene Ports, Volumes, ENV und beschreibbare Hostpfade.

Dokumentation: Betriebs-README, Adminbedienung, Schema-/Audit-Lebenszyklus, Gateway/Identity/Origin-Vertrauensgrenzen und tatsächliche Diagnosekommandos. Versionsmanifest und bekannte Native-/Produktionsgrenzen. Rohlogs lokal, nur bereinigte Belege versionieren. Keine Tokens, Cookies, Passwörter, signierten URLs oder vollständig interpolierten Konfigurationen in Prompts/Logs.

**Erfolg:** eine fachliche Entscheidung, sofort aktuelle HTTP-Autorisierung, aktuelle Kataloganzeige, nachvollziehbare Geschäfts- und Datenbankänderung. Noch kein synchronisiertes persönliches ClickHouse-/Superset-Recht und keine rechtliche Zertifizierung der Revisionssicherheit.
