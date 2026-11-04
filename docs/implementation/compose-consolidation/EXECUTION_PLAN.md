# MA-F – Ein gemeinsamer Docker-Compose-Stack

**Verbindlicher Folgeauftrag für Codex · Revision 1.0 · 4. November 2026**  
**Implementierung:** Codex. **Review nach jeder Teilphase:** OpenCode 2.x mit DeepSeek Flash 1017 über den vorhandenen DeepSeek-Zugang.  
**Status:** Spezifikation; keine in diesem Auftrag bereits ausgeführte Konsolidierung.

> Nicht die Anwendungen neu entwickeln: Die vorhandene Management-/Access-Implementierung in den gemeinsamen Dev-Stack integrieren. Im regulären lokalen Betrieb gibt es ein Compose-Projekt, einen Container pro dauerhaftem Dienst und genau einen PostgreSQL-16/PostGIS-Server. Keine HA-Topologie und keine parallele Python-Orchestrierung.

## 0. Geltung, Quellen und Arbeitsbereich

Arbeitsverzeichnis ist der gemeinsame Elternordner der sechs bestehenden `dateninfrastruktur-*`-Repos, **kein zusätzliches Git-Repository**. `STACK` bezeichnet `dateninfrastruktur-dev-stack`, `ADMIN` das Repo `dateninfrastruktur-admin`, `PUBLIC` das Repo `dateninfrastruktur-sodata`, `TOPICS` das Themenrepo. Die Jenkins-Repos bleiben eigenständige Geschwister.

Dieser Auftrag ergänzt die funktional implementierten Phasen MA-0 bis MA-E. Er ersetzt für die **reguläre Laufzeit** ausdrücklich deren Zwei-Instanzen-Topologie, separate Management-Infrastruktur und `docker run`-Startpfade. Die fachlichen Modelle, Auditregeln, Anträge, Entscheide, Autorisierungsregeln und Download-Sicherheitsverträge bleiben erhalten. Historische Prüfberichte sind historische Nachweise und werden nicht rückwirkend umgeschrieben.

Normative Kapitel dieses Gesamtauftrags:

1. `EXECUTION_PLAN.md` – Zielbetrieb, Umsetzung und Phasengates.
2. `SPEC_MIGRATION.md` – Übernahme, Identitäten, Datenerhaltung, Umschaltung und Rückfall.
3. `TEST_PLAN.md` – gezielte Prüfungen und Regeln für Delta-Reviews.
4. Rollenbezogen `CODEX_STARTPROMPT.md` oder `OPENCODE_REVIEW_PROMPT.md`.
5. `AGENTS_ERGAENZUNG.md` – eng begrenzte Aktualisierung der aktiven Einstiegspfade.

`SOURCES.md` trennt geprüfte Quellen von Entwurfsentscheidungen. Alle hier neu vorgeschlagenen Skripte, Methoden und Profile sind **Implementierungsverträge**, keine Behauptung, sie existierten bereits.

### 0.1 Untersuchte Ausgangslage

| Repo/Quelle | Untersuchter Stand | Relevanter Befund |
|---|---|---|
| STACK | `465d7c4f7302037cdddd69e20139822e68b8cdfe` | MA-E dokumentiert; `compose.yaml` weiterhin Grundinstallation |
| ADMIN | `7986d67330fd6a304d98d2c4e73aa38d139bde4a` | Merge enthält zusätzlich LICENSE; geprüfte MA-E-Produktbasis `29c00b0c5b65115cc541ed6086ec6e54a938c870` |
| PUBLIC | MA-E-Produktbasis `20d94f5fbb9259f446f7ac0b22dd0e72b2d22ca6` | DB-Katalog und geschützte Downloadlinks vorhanden |
| `STACK/compose.yaml` | Blob `9a57e3dbd60545d97a7b16792114e7e4e7ecb0c5` | PostgreSQL `16.10-alpine`; Sodata noch `manifest`; kein Admin-Service |
| `ADMIN/scripts/managed_runtime.py` | aktueller gelesener Quellstand | Eigene `docker run`-Container, zwei Gateways/Admins/Portale, zusätzliche Garage/Keycloak |
| `ADMIN/scripts/management_db.py` | aktueller gelesener Quellstand | Eigenes PostgreSQL/PostGIS und starke Bindung an Container-ID, Label und Runtimepfad |
| `ADMIN/docs/schema-lifecycle.md` | aktueller gelesener Quellstand | Dokumentiert tatsächliches Testimage PG 16.9/PostGIS 3.5.2; Schema/Audit/Ownerverträge |

Quellenlektüre und frühere Reviewberichte ersetzen keine neue Laufzeitprüfung. Lokale HEADs, Dirty State, Images und Datenstände in F0 feststellen. Nichts auf diese historischen SHAs zurücksetzen. Ein nicht im Remote sichtbarer lokaler ClickHouse-Lader bleibt Nutzerarbeit und wird erhalten.

### 0.2 Was ausdrücklich NICHT beauftragt ist

Keine HA, Replikation, zweite Admin-/Portal-/Gatewayinstanz, Kubernetes/OpenShift, neues IAM, Casbin-Policyverteilung, eigenes Lua-Autorisierungsplugin, zusätzliche dauerhafte Datenbank, neue Modelle, neues Dashboard, persönliche ClickHouse-Rechteprojektion oder Versions-Grossmigration von Boot/Cayenne. Keine vollständige Überarbeitung sämtlicher Fachtests. Keine Löschung alter Volumes oder Auditdaten, um den Aufbau zu vereinfachen.

Die alten `datenportal-*`-Repos sind keine Änderungsziele. Die Bearbeitung der **ausdrücklich identifizierten eigenen lokalen Dateninfrastrukturinstanz** ist für die kontrollierte Übernahme erlaubt; fremde Projekte bleiben tabu. Die frühere Testisolationsregel ist kein Grund, erneut eine dauerhafte Parallelumgebung als Ergebnis zu liefern.

## 1. Verbindlicher Zielzustand

### 1.1 Genau ein reguläres Compose-Projekt

Die dauerhaften Dienste stehen deklarativ in **`STACK/compose.yaml`**. Normales Projekt: `dateninfrastruktur-dev-stack`, weiterhin überschreibbar für isolierte Tests. Keine weitere handgeschriebene Management-Compose-Topologie und kein Generator, der neben Compose noch selbst Container startet.

| Service | Anzahl im Normalbetrieb | Aufgabe |
|---|---:|---|
| `postgres` | 1 | PG16 mit verfügbarer PostGIS-Erweiterung; drei Anwendungsdatenbanken |
| `keycloak` | 1 | Ein Identitätsdienst; Persistenz in `postgres/keycloak` |
| `garage` | 1 | Bestehender S3-Dienst; bestehende und übernommene Buckets |
| `origin` | 1 | Interner read-only Datei-Origin für verwaltete Downloads; vorhandenes rclone verwenden |
| `gateway` | 1 | APISIX, OIDC, `forward-auth`, Routing zu Portal/Admin/Jenkins |
| `sodata` | 1 | Öffentlicher Katalog, Datenquelle PostgreSQL |
| `admin` | 1 | Administration, Self-Service und interne Authorization API |
| `jenkins` | 1 | Vorhandene GRETL-/Jobfunktion, Daten und Plugin erhalten |
| `clickhouse` | 1 | Vorhandener Analyseserver mit unverändertem Datenbestand |
| `superset` | 1 | Vorhandene BI-Anwendung; Metadaten in `postgres/superset` |

Das sind **zehn dauerhafte Services**. Einmalige Setup-/Migrations-/Operatorjobs dürfen zusätzliche Container kurzzeitig verwenden, müssen aber ebenfalls als Services/Profile in Compose definiert und nach Ausführung beendet sein. Keine zweite Webanwendung als „Initializer“ verstecken. Alle Services tragen echte von Compose erzeugte Projekt-/Servicelabels; manuell gesetzte Labels an `docker run`-Containern sind kein Ersatz.

Kein `container_name`, keine `*-a`/`*-b`-Varianten, kein HA-Profil als Vorsorge. Compose verwaltet Namen und DNS. Für Tests darf dieselbe Topologie unter einem isolierten Projektnamen mit eigenen Volumes und Ports starten. Das ist Testisolation, kein zweiter dauerhafter Nutzerstack. Nach dem Test eigene Ressourcen bereinigen.

### 1.2 Eine PostgreSQL-Instanz ist ausdrücklich gewollt

```text
postgres (PostgreSQL 16 + PostGIS-Binaries)
├── keycloak                      – Keycloak-Rolle
├── superset                      – Superset-Rolle
└── dateninfrastruktur_management  – di_owner/di_audit_owner/di_migrator,
                                    di_writer/di_authz/di_public/di_audit_reader
```

PostGIS ist eine PostgreSQL-Erweiterung, kein separater Datenbankserver. Sie wird nur in den Datenbanken aktiviert, die sie tatsächlich benötigen. Für Management wird der bestehende ili2pg-Vertrag einschliesslich PostGIS und `uuid-ossp` erhalten; Keycloak und Superset verwenden normale PostgreSQL-Tabellen. Separate Datenbanken und Konten bleiben zwingend. Kein gemeinsames Superuserkonto für Anwendungen. Keine unnötigen Extensions in `template1`; bei Neuanlage saubere Templates verwenden.

**Imagewahl:** Vorhandene PG16/PostGIS-Familie bevorzugen, z.B. das bereits verwendete `ghcr.io/baosystems/postgis:16-3.5`. Einen tatsächlich verfügbaren, kompatiblen Manifest-/Plattformdigest in F0 festlegen. Die dokumentierte MA-Version **16.9 ist älter als die Foundation-Version 16.10**: den alten Digest nicht blind als Ziel erzwingen. Ziel-Minor muss mindestens so neu sein wie die tatsächlich vorhandenen beiden Quellen, und die benötigte PostGIS-Version muss verfügbar sein. Keine erfundene aktuelle Tag-/Digestangabe und kein Majorwechsel auf PG17/18/19. Falls nötig ein kleiner abgeleiteter PG16/PostGIS-Build; kein dauerhaft zweiter PG-Container als Ausweichlösung.

Native Hostarchitektur prüfen (insbesondere macOS arm64). Kein stilles Erzwingen von `linux/amd64`. Versionsauswahl als einmaliger, nachvollziehbarer Kompatibilitätsentscheid; keine wiederholten ungepinnten Updates während MA-F.

Ein gemeinsamer Server ist keine harte Mandantenisolierung und kein HA-Nachweis. Diese Betriebsgrenze ist für den lokalen MVP akzeptiert.

### 1.3 Was übernommen und was nicht verändert wird

Modelle, Cayenne-DataMap, fachliche Services und Auditmechanismus aus MA-A–E wiederverwenden. Kein Reimport der Fachmodelle in befüllte Managementschemas. Native/JVM-Optionen nicht löschen; JVM bleibt geprüfter Standard. Der Original-ClickHouse-Datenbestand, seine Zugangsdaten, Superset-Daten/SECRET_KEY sowie Jenkins-Home bleiben erhalten.

Die rclone-Funktion bleibt **ein** vorhandener Transferbaustein. Keine neue S3-HTTP-Implementierung nur wegen der Konsolidierung. Sodata/Admin streamen weiterhin keine Fachdaten. APISIX fragt die Java-Authorization-API, nicht PostgreSQL direkt.

## 2. Repository- und Dateizuständigkeiten

| Ort | Konkrete Änderungen |
|---|---|
| STACK | Einzige aktive Laufzeitdefinition, Images/Builds, Konfiguration, Secrets, Lifecycle, Übernahmewerkzeuge und Integrationstests |
| ADMIN | Anwendungsimage und ausführbarer Tool-Modus; Schema-/Auditwerkzeuge auf expliziten DB-Zugang entkoppeln; alte Orchestrierung abbauen |
| PUBLIC | Bestehendes JVM-Image/DB-Konfiguration passend anbinden; nur notwendige Port-/Pfad-/Buildkorrekturen |
| TOPICS | Nur wenn alter lokaler Reload-/Manifestaufruf einen gezielten Adapter benötigt; kein neuer Publisher |
| Jenkins-Repos | Nur bei nachgewiesen benötigter Image-/Konfigurationskorrektur; Pluginvertrag erhalten |

Vorgeschlagene Zielstruktur (vorhandene passende Dateien erweitern):

```text
STACK/
  compose.yaml                       # alle normalen Services und Toolprofile
  .env.example                       # keine echten Geheimnisse
  services/apisix/config.yaml
  services/apisix/routes.template.*  # stabile Regeln, keine Personenrechte
  services/origin/                   # read-only WebDAV-Konfiguration
  services/postgres/init/
  services/keycloak/                 # deklarativer Soll-Client, kein Realm-Reset
  scripts/init.sh
  scripts/up.sh
  scripts/stop.sh
  scripts/down.sh
  scripts/restart.sh
  scripts/status.sh
  scripts/logs.sh
  scripts/management/                # nur delegierende Kompatibilität, keine zweite Laufzeit
  scripts/compose_runtime.py         # optional: ein kleiner gemeinsamer Compose-Zugriff
  scripts/consolidation.py           # inventarisieren/planen/übernehmen/verifizieren/retire
  scripts/test-consolidation.sh
  .runtime/<project>/                # privat; aktive Konfig/Secrets/Übernahmejournale
  docs/operations.md
  docs/migration-ma-f.md
  docs/implementation/compose-consolidation/
ADMIN/
  Dockerfile                         # build, jvm-runtime; optional eigener tooling-Target
  scripts/...                        # Fachsetup kennt JDBC/PG-Ziel, keine Containererzeugung
```

Nicht jede Verantwortung benötigt ein Modul. Maximal wenige gemeinsame Hilfsdateien; kein neues Deploymentframework. Containerorchestrierung gehört nach STACK. Anwendungsspezifische Schema-/Auditlogik bleibt in ADMIN.

## 3. Deklarative Laufzeit und reproduzierbare Images

### 3.1 Compose statt selbst gebauter Orchestrierung

Alle normalen Start-/Stop-/Statuspfade verwenden dieselbe Compose-Datei, dieselbe explizite ENV-Datei, denselben Projektnamen und denselben Runtimepfad. Gemeinsamen Wrapper verwenden, statt Parameter an zahlreichen Stellen anders aufzulösen.

Verboten im aktiven Betrieb:

- `docker run`, `docker create`, `docker network create` als Ersatz für Compose;
- `network_mode: service:jenkins` für APISIX;
- Host-JAR-Mount als einziger Auslieferungsweg für Admin/Sodata;
- automatisch erzeugte zufällige Hostports bei jedem Normalstart;
- Verwaltung normaler Dienste über gespeicherte Container-IDs in ADMIN/.runtime;
- PostgreSQL- oder Keycloak-Neuanlage als Nebenwirkung eines Tests/Imports;
- künstliche Compose-Labels für bestehende Einzelcontainer.

Lesende Docker-Inventur und gezielte `docker cp/exec/stop/rm`-Operationen **an identifizierten Legacyquellen während der Migration** sind zulässig. Sie dürfen nicht als neuer regulärer Lifecycle weiterleben. Temporäre Zielwerkzeuge werden über `docker compose run --rm` gestartet.

### 3.2 Eigenes Admin-Image

`admin` erhält einen echten, reproduzierbaren Imagebuild aus ADMIN, passend zum bereits vorhandenen Sodata-Image. Java25, Spring Boot/Cayenne und Locks bleiben im vorhandenen Stand. Multi-stage oder gleichwertiger Build; genau das erwartete Boot-JAR kopieren, nicht `next(glob('*.jar'))`. Runtime ohne privilegierte Setupcredentials, ohne Docker-Socket und ohne schreibendes Quellrepo-Mount.

Auch Setup-/Operatorbefehle müssen nach einem frischen Checkout mit Docker/Compose ausführbar sein. Kein neuer zwingender Host-Java25-/pg_dump-/rclone-Buildpfad für den Normalbetrieb. Ein schmaler Tooling-Target oder Compose-Toolservice darf JDK/ili2pg/PG16-Client/rclone/Python enthalten. Bestehende Toolpins und Hashprüfung übernehmen. Webimages müssen diese Werkzeuge nicht enthalten.

Unveränderte Jenkins-/Superset-Builds wiederverwenden. Source/Image-ID nachvollziehbar; keine Phantom-Registryimages. Testbuilds dürfen nicht die Images einer laufenden Nutzerinstanz unter demselben `:local`-Tag überschreiben. Projekt-/Commit-bezogene Tags oder belegte Image-IDs verwenden.

### 3.3 Lifecycle-Vertrag

```text
init        → fehlende Konfig erzeugen, vorhandene Secrets/UUIDs erhalten
setup       → ausdrücklich leere DB/fehlende eigene Rollen einrichten oder Bestand prüfen
migrate     → ausdrücklich geplante Bestandsübernahme; nie implizit aus up
up          → validieren, benötigte Images bauen/verwenden, Compose starten
stop        → Container stoppen, Daten unverändert behalten
down        → nur eigene Compose-Container/Netze entfernen, keine Volumes
restart     → dieselbe Umgebung; keine Seeds, Rechteänderungen oder neue Identitäten
status/logs → dieselbe Umgebung und stabile URLs; keine Secrets
```

Nach explizitem Erstsetup muss auch `docker compose --env-file <env> up -d --wait` mit dem kanonischen File funktionieren. Wrapper dürfen Schema-/Konfigvorbereitung vereinfachen, aber keine unsichtbare zweite Topologie erzeugen. `up.sh --skip-build` erhalten; veraltete Schalter ehrlich dokumentieren oder vor Änderungen ablehnen.

Keine `--force-recreate`-Pflicht bei jedem Start. Bei geändertem Image/Konfiguration müssen normale Compose-Recreation und `up --build` wirksam sein. Setupjobs getrennt, `restart: "no"`, Profil `setup`/`tools` oder bewusst deklarierte idempotente Initialisierung. Sie dürfen keine laufenden Anwendungen mit Schema-Ownercredentials starten.

Healthchecks vorhanden, korrektes `service_healthy`/`service_completed_successfully`, aber keine zyklische Abhängigkeit. Leerer zulässiger DB-Katalog darf starten. Sodata benötigt weder Jenkins noch `current.json` noch einen erfolgreichen Publikationsjob zum Start. APISIX-Health muss ohne komplette externe OIDC-Redirectfolge funktionieren. Ein späterer DB-/Authz-Ausfall verweigert Downloads trotzdem.

## 4. Ein Netzwerk und eindeutige URLs

APISIX erhält seinen eigenen Compose-Netzwerkraum und bindet selbst den Loopback-Hostport. Jenkins ist intern über `jenkins:8080` erreichbar. Alle bisherigen `127.0.0.1:8080`-Upstreams und mit Jenkins geteilten Ports gezielt ersetzen.

Standardendpunkte (vorhandene Portvariablen erhalten):

| URL/Port | Ziel |
|---|---|
| `http://localhost:${GATEWAY_PORT:-18081}/` | Sodata im DB-Modus |
| `/management` | Adminverwaltung mit OIDC |
| `/access/*` | Self-Service im Admin-Backend |
| `/downloads/*` | OIDC optional + forward-auth + privater Origin |
| `/oidc/callback` | deklarierter OIDC-Rückweg |
| `/jenkins/*`, `/anlieferung` | vorhandener Jenkins-Pfad/Weiterleitung |
| `http://localhost:${KEYCLOAK_PORT:-18080}` | einziger kanonischer Keycloak-Origin |
| `http://localhost:${SUPERSET_PORT:-18088}` | bestehender Superset-Zugang |
| ClickHouse 18123/19000, konfigurierbar | bestehender SQL-Zugang |

Normal keine Hostports für PostgreSQL, Admin, Sodata oder Origin. S3/Website-/Admin-/RPC-Endpunkte nicht als unkontrollierter Dateibezug veröffentlichen; Operatoren verwenden interne Compose-Tools. Ein bewusst benötigter lokaler S3-Debugport ist opt-in und darf keine anonyme Website oder ACL-Umgehung eröffnen; kein Pflichtbestandteil.

`localhost` und `127.0.0.1` nicht abwechselnd als fachlich gleicher OIDC-Issuer behandeln. Externe Issuer-/Callback-URLs stabil halten, interne Discovery/JWKS/Backchannel-Adressen separat konfigurieren. Ziel-Keycloak verwendet PostgreSQL (`KC_DB=postgres`) und den gemeinsamen Service. Keine zweite H2-/dev-file-Identitätsdatenbank. `start-dev` darf für lokalen HTTP-Betrieb bleiben, aber nicht als Ersatz für persistentes PostgreSQL.

Die bisherigen zwei Gateway-Origins werden auf **einen** aktiven Origin reduziert. Historische Quellissuer benötigen die kontrollierte Übernahme in `SPEC_MIGRATION.md`, nicht eine erweiterte Allowlist beliebiger Tokenissuer. Alttokens/Sessions dürfen beim expliziten Cutover ungültig werden; danach neuer Login.

## 5. Gateway, Origin und Legacy-Publikation

### 5.1 Vorhandene MA-E-Sicherheitslogik erhalten

Die wirksamen Routen aus `managed_runtime.routes(...)` in statische versionierte Templates unter STACK überführen; ausschliesslich technische Werte beim Init rendern. Keine dynamische Casbin-/Policy-Konfiguration, kein Lua-Autorisierungsplugin. Berechtigungsänderungen bleiben reine DB-Änderungen.

Unverändert zu prüfen: rohe kanonische URI vor Normalisierung; verifizierter Access-Token; `X-DI-Gateway-Credential`; `allow_degradation=false`; Fehler 503 statt Freigabe; Entfernen von Credentials vor Origin; GET/HEAD/Range/ETag; keine Directorylistings/ZIP/Methoden-Bypässe; `Cache-Control: no-store`; keine direkte öffentliche `/internal/*`-/Actuator-/Admin-API-Route. Nicht mit einer simplen neuen Reverse-Proxy-Regel die bereits getestete Schutzkette ersetzen.

Origin bleibt ein interner `rclone serve webdav` mit vorhandenem Read-only-/Baseurl-/Directory-/Cachevertrag. Genau ein verwalteter Root, derzeit `di-managed-private/downloads`. Ein eigener lesender Storagekey, kein Admin-/Schreibschlüssel. Keine Benutzer-JWTs am S3-Origin. Keine experimentellen Origin-Beobachter (`origin-p…`) im normalen Deployment; solche Werkzeuge sind test-only und kurzlebig.

### 5.2 Alte öffentliche Auslieferung nicht als Bypass mitnehmen

Der alte `s3-browser` entfällt als normaler Service. Buckets und Objekte dürfen im gemeinsamen Garage erhalten bleiben; Bucketzahl ist nicht Containerzahl. Die Schutzklasse hängt nicht am physischen Bucket.

Standardmässig keine pauschale anonyme Weiterleitung von `/ch.so.daten/*`, `/s3/*` oder alten MA-Demorouten auf verwaltete Daten. Alte kontrollierte Distributionen, die übernommen werden, benötigen den bestehenden Alias-/Objekt-Inventurcheck: ein erratbarer Altlink darf keine neue `restricted`-Regel umgehen. Private Buckets bleiben ohne Websitefreigabe. Keine externen echten öffentlichen Originale verändern oder deren Vertraulichkeit behaupten.

Der noch vorhandene alte Public-Bucket ist **Legacybestand**, nicht die Livequelle des DB-Portals. Historische Metadaten-/Dateiobjekte dürfen erhalten bleiben; ein bewusst weiterhin öffentlicher Legacyzugang müsste einzeln inventarisiert und ausdrücklich freigegeben sein. Ohne diesen Nachweis default deny, nicht „zur Kompatibilität alles öffentlich“. Das Abschalten eines alten Zugangs als dokumentierte Betriebsänderung ausweisen, keine heimliche Datenlöschung.

### 5.3 Jenkins bleibt eingebunden, aber kein falscher DB-Publisher

Jenkins-Home, Plugin, Jobs und GRETL-Laufzeit erhalten. `/jenkins/` und `/anlieferung` prüfen. Host- und Containeradressen nach Auflösung des gemeinsamen Netzwerkraums anpassen.

Normalstart ruft **nicht mehr** `bootstrap-publication.sh` als Voraussetzung für Sodata auf. Alte Reload-Calls auf `/admin/catalog/reload` sind für den DB-Katalog nicht sinnvoll. Die vorhandene Legacy-Pipeline darf explizit Legacyartefakte erzeugen, aber nicht grün melden, den neuen DB-Katalog publiziert zu haben. Minimaler expliziter Schalter/Adapter: Legacyreload im DB-Betrieb auslassen oder den unpassenden Aufruf vor Verarbeitung eindeutig ablehnen. Keine breitflächige Neuimplementierung von GRETL-Jobs.

Ein vorhandener neuer ClickHouse-Ladepfad bleibt unverändert benutzbar. Seine Daten und privaten Archive nicht als Foundation-Testfixtures zurücksetzen. Fachliche Registrierung neuer Lieferungen in der Management-DB bleibt beim vorhandenen expliziten Operator-/Registrierungsvertrag; MA-F erfindet keinen zweiten Importworkflow.

## 6. Setupwerkzeuge von Legacycontainern entkoppeln

Die aktuelle Funktion `management_db.state()` akzeptiert nur einen konkreten MA-B-Container. `setup.py` kann einen solchen Container selbst erzeugen. Das muss für den neuen Standardweg aufgelöst werden.

Neue bzw. adaptierte, kleine Verantwortlichkeiten:

| Typ/Funktion | Vertrag |
|---|---|
| `ComposeContext.load(stackRoot, envFile, project, runtimeDir)` | Explizite Pfade laden/prüfen; keine globale `.env`; feste Defaultwerte, keine Secretrotation |
| `ComposeContext.command(args, input=None)` | Immer dasselbe `compose.yaml`, ENV, Projekt; Argumentliste statt Shellkonkatenation; Secret-redigierte Fehler |
| `RuntimeInventory.discover()` | Labels, IDs, Mounts, Versionen, State-Dateien lesend erfassen; keine DBcontainer anlegen |
| `RuntimeInventory.verifyOwnership(ref)` | Exakte ID + erwartete Labels + gespeicherter Kontext; fremde Ressource vor Mutation ablehnen |
| `DatabaseTarget.fromConfig(...)` | Zielhost/Port/DB/Konten aus expliziter Konfiguration; kein festes MA-B-Label oder Hostloopbackport |
| `setupManagement(target)` | Leere eigene DB initialisieren; bei Bestand Fingerprint/Mapping/Audit prüfen; kein Reimport/Drop |
| `verifyManagement(target)` | Nur lesend prüfen; bestehende `runtime_contract`-/Coverage-/Mappingprüfungen nutzen |
| `renderGateway(config, secrets)` | Stabile SINGLE-Instanzroute generieren; keine Fachrechte lesen; deterministisch, keine Geheimnisse loggen |
| `configureKeycloak(target, desiredClient)` | Bekannten Client idempotent ergänzen; fremde Clients/Benutzer/Passwörter nicht überschreiben |
| `activateDistribution(target, datasetId, expectedVersion, distributionId)` | Bestehenden Java-Operator mit explizitem privatem Speicherzugang aus Compose-Tools ausführen |
| `MigrationCoordinator` | Siehe separaten Migrationsvertrag; kleine nachvollziehbare Operationen, kein allgemeines Clusterwerkzeug |

Diese Namen sind Vorschläge, die Verantwortlichkeiten verbindlich. Funktionen statt Klassen sind in den bestehenden Python-Skripten vollkommen ausreichend. Keinen zusätzlichen JVM-Microservice bauen. SQL-Dateien, Modelle, Mapper und Auditimplementation nicht duplizieren.

Insbesondere dürfen `audit_setup.py`, `apply_constraints.py`, `verify_physical_mapping.py`, `upgrade_contract.py` und `contract_fingerprint.py` nicht über einen indirekten Import wieder ein Legacy-`docker run` auslösen. Normales Setup regeneriert keine versionierten Cayenne-Klassen. cdbimport/cgen bleibt expliziter Entwicklungs-/Vertragsprüfschritt mit kontrolliertem Toolzugang.

## 7. Persistenz und Secrets

Alle zustandsbehafteten Services verwenden benannte persistente Volumes in Compose. Keine anonymen Garage-/Keycloak-Volumes und keine alleinige Persistenz in der Container-Schreibschicht. Bestehende physische Volumenamen anhand der Inventur gezielt zuordnen; ein geänderter logischer Compose-Name darf nicht versehentlich einen leeren Bestand erzeugen.

Ein einziger aktiver Runtimebereich unter `STACK/.runtime/<project>/`; Verwaltung nicht mehr teilweise in ADMIN/.runtime und teilweise STACK/.env. Migration liest alte private Zustandsdateien gezielt, übernimmt benötigte Werte in den neuen geschützten Bereich und markiert die alten Startpfade als retired. Originale als Rückfallbeleg behalten, nicht als weiter aktive Steuerung.

`.env`/Secrets nicht global neu erzeugen. Postgres-Rollenpasswörter, Keycloak-Clients, APISIX-Sessionsecret und Superset-`SECRET_KEY` erhalten oder bei technisch nötigem Wechsel ausdrücklich und konsistent migrieren. Keine Secretwerte in `docker compose config`-Logs, CLI-Argumenten, Reporten oder Agentenprompts. Vollständig interpolierte Konfiguration nur lokal geschützt verarbeiten; in Berichten Service-/Image-/Portlisten und Hashes.

Normalstart richtet keine fachlichen Demo-Grants, Datensätze oder Authorities ein. Neuanlage und Migration sind unterschiedliche Modi. Demo-Seeds und Passwort-Grant-Testclient sind explizit opt-in für isolierte Tests, nicht im Benutzerstart.

## 8. Teilphasen und Gates

### MA-F0 – Bestandsprüfung und konkreter Übernahmeplan

Liefern: aktuelle Repo-SHAs/Dirty State; Quell- und Ziellaufzeitinventur; Daten-/Volume-/Issuerzuordnung; festes PG16/PostGIS-Image; minimaler Compose-Zielentwurf; aktive AGENTS-Verweise; wiederverwendbarer autonomer Reviewweg. Höchstens ein kompakter Betriebsentscheid statt neuer Gesamtarchitektur.

Tests **F01–F03**: Eigentümer-/Zielverwechslung muss vor Mutation scheitern; reales Image auf Hostarchitektur mit drei isolierten Testdatenbanken/erforderlichen Extensions; Reviewrunner mit echter Toolausführung und negativer SHA-/Reportprobe. Keine funktionalen MA-A–E-Vollsuiten.

Gate: eindeutiger nichtdestruktiver Plan und unabhängiger Review. Bei mehreren unterschiedlichen befüllten Managementquellen nicht nach Namen/Datum raten; Integrationsarbeit auf Testbeständen weiterführen, Livequellenwahl als enger Blocker benennen.

### MA-F1 – Kanonischer Single-Instance-Compose-Stack

Liefern: `compose.yaml` als einzige Standardtopologie; neue Admin-/Toolimages; gemeinsamer PG16/PostGIS mit separaten Datenbanken/Rollen; ein Keycloak auf PostgreSQL; ein Garage/Origin/Gateway/Sodata/Admin; vorhandene Jenkins/ClickHouse/Superset integriert. Hostjar- und Container-ID-Abhängigkeiten auflösen. DB-Modus und statische MA-E-Gatewayregeln anschliessen.

Tests **F04–F08**: frischer Aufbau in isoliertem Compose-Projekt; genau zehn Dauerläufer; ein PG und korrekte DBrechte; DB-Katalog startet leer ohne XTF/Jenkins-Publikation; echtes Login/geschützter Download mit expliziter Testfixture; Jenkinsroute und Superset-ClickHouse-Verbindung. Build benötigt keinen zufälligen vorhandenen Host-JAR-Stand.

Gate: frischer Standardweg funktioniert; reine YAML-/Container-Healthprüfung reicht nicht. Noch keine Nutzerquellen entsorgen.

### MA-F2 – Bestandsübernahme und Rückfall proben

Liefern: Migrationsplan/-journal, PostgreSQL-Backup/Restore, Keycloak-Abgleich, Storagekopie/-verifikation, geprüfte Issuerzuordnung, konsistente Secrets und gezielter Rollback. Auf bereits bekannten Dateiverträgen aufbauen, kein generisches Datenmigrationsprodukt.

Tests **F09–F13**: zwei nichtleere Quellfixtures (Foundation und MA) in den einen Zielstack übernehmen; Daten/Grants/Audit/IDs/Dateibytes/Metadaten erhalten; Kollision ablehnen; Wiederholung nicht duplizieren; Fehler vor Cutover rückfallfähig; Secrets nicht verlieren; Quelle nach Snapshotänderung erkennen. Reviewer führt eigene Migrationsgegenprobe aus.

Gate: **wirklich restaurierter** Zielbestand und verifizierter Rückfall. Ein vorhandenes Dumpfile oder grünes `pg_restore --list` ist kein Restore-Nachweis.

### MA-F3 – Ein Betriebsweg, alte Orchestrierung stilllegen

Liefern: Root-`init/setup/up/stop/down/restart/status/logs` auf kanonisches Compose umstellen; alte `scripts/management/*` nur noch delegierend oder mit eindeutiger Ablöseinformation; `managed_runtime`/`identity_runtime` als aktive Containerorchestrierung entfernen. Aktive Tests ebenfalls auf gemeinsamen Compose-Unterbau umstellen; historischer Reviewtext bleibt erhalten. Ausführbare Legacycodes dürfen höchstens als explizite lesende Migrationshilfe bestehen.

Tests **F14–F16**: Start/Stop und **Container-Neuerstellung** mit demselben Zustand; keine Defaultseeds; Wrapper führen dasselbe Projekt; statische und beobachtete Runtimeprüfung zeigt keine versteckte zweite Topologie; Scopeprüfung vor retire/rollback. Reviewer testet auf eigenen Quellen, nicht auf Nutzerdaten.

Nach unabhängiger Abnahme dieses Codes: den eindeutig geplanten lokalen Cutover ausführen, solange alle Eigentums-/Backup-/Zuordnungsprüfungen bestanden sind. Daten nur auf die bezeichnete eigene Zielinstanz übertragen. Ankündigen, welche eigenen Dienste kurz gestoppt werden; keine weiteren technischen Bestätigungen für bereits gedeckte sichere Schritte verlangen. Bei nicht auflösbaren Daten-/Identitätskonflikten nicht löschen oder raten: enger BLOCKED-MIGRATION-Status, andere Arbeiten abschliessen.

### MA-F4 – Konsolidierte Endabnahme

Liefern: repräsentativer Fachpfad **auf der normalen Compose-Topologie**, Quell-/Zielabgleich, endgültige Betriebsanleitung und bereinigte aktive Ressourcen. Vorhandenen letzten phasenrelevanten Befund fixen, nicht neue Funktionen beginnen.

Tests **F17–F20**: Katalogänderung → Antrag/Entscheid → geschützter Download → Entzug mit noch gültigem Token → Audit; eine HEAD/Range-/Headerprobe und Fail-Closed; Neustart/Recreate des gesamten Zielverbunds; Jenkins/ClickHouse/Superset-Sentinels unverändert; keine alten MA-/Origin-Probe-/Doppelcontainer mehr aktiv; Retire nur nach Backup.

Dieses Review ist der abschliessende MA-F-Integrationsreview. Keine zusätzliche identische Vollsuite. Lokale Datenübernahme separat als `LOCAL_CUTOVER_VERIFIED` oder präzise `PENDING/BLOCKED` ausweisen. Ein abgenommener Codekandidat allein beweist nicht, dass die Nutzerinstanz bereits umgestellt ist.

## 9. Autonome Reviews und risikobasierte Nacharbeit

Vorhandenen Reviewrunner wiederverwenden, auf `MA-F0` bis `MA-F4` und neue Spec-Hashes erweitern. Codex implementiert; **OpenCode 2.x / DeepSeek Flash 1017** prüft in frischer Sitzung, ohne Produktänderungen. Bestehenden DeepSeek-Provider nutzen, tatsächliche Modell-ID/Version erfassen. Keine erfundene API-ID, kein Wechsel zu Qwen/Codex-Selbstreview.

Jedes Gate: passende lokale Tests → lokale Commits aller betroffenen Repos → Handoff mit vollständigen SHAs/Anforderungshash → isolierte Geschwistercheckouts → Review mit eigenen Tests und mindestens einer eigenständigen Gegenprobe. Kein eigener HEAD-SHA im zu prüfenden Commit. Prüfergebnis muss exakt zum Kandidaten passen. Fehlende Pflichtausführung oder fehlendes Modell ist `NICHT_PRUEFBAR`, nicht PASS.

Fehlerkorrekturen: kleinster Fix mit reproduzierender Probe, neue SHAs, **Delta-Review**. Der Reviewer prüft den neuen Diff und führt neue/gefährdete Verträge selbst aus. Unveränderte frühere unabhängige Belege nur mit benannter Herkunft und begründeter Nichtbetroffenheit übernehmen. Keine Pflicht, nach einem README-Fix Keycloak, SQL und jeden Dateitest neu auszuführen. Umgekehrt kein alter Pass als Beweis für eine geänderte Gateway-, Migrations- oder Eigentümergrenze. Details in `TEST_PLAN.md`.

## 10. Abschlussdefinition

MA-F ist fachlich abgeschlossen, wenn die vereinbarten Code-/Test-/Review-Gates bestanden sind und der dokumentierte Standardstart tatsächlich **den einen integrierten Compose-Stack** startet. Die bestehende Nutzerinstanz gilt zusätzlich erst als bereinigt, wenn die geplante Übernahme und Stilllegung nachgewiesen ist.

Abzugeben: geändertes Compose, reproduzierbare Images/Tools, nachvollziehbare DB-/IdP-/Storageübernahme, konkrete stabile URLs, Ziel- und Rückfallmanifest, aktuelle README/AGENTS-Einstiege, knappe Phasenberichte, unabhängige Reviews und offener Status eventuell nicht migrierbarer Quellen. Keine Behauptung „fertig“, wenn wieder nur der isolierte Testharness funktioniert.
