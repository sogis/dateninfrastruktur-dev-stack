# Verbindlicher Arbeitsauftrag: lokale Grundinstallation Dateninfrastruktur

Stand: 3. November 2026. Dokumentrevision 1.2: Das projektspezifische Jenkins-Plugin wurde auf Wunsch des Auftraggebers von `jenkins-gretl-datenportal-plugin` in `jenkins-gretl-dateninfrastruktur-plugin` umbenannt. Maven-Artefakt, Jenkins-Plugin-ID, HPI/JPI und Assetpfade wurden gemeinsam angepasst; die alte Maven-Snapshot-Koordinate wird entfernt. Der technische Funktionsumfang bleibt unverändert. Revision 1.1 (2. November 2026) ergänzte Ablage, AGENTS.md und Reviewnachweise. Auftraggeber: AGI Kanton Solothurn. Umsetzungswerkzeug: OpenCode. Implementierung: DeepSeek Flash über die DeepSeek-API. Unabhängiges Review: Qwen 3.8 27b über Infomaniak, mit vor Ort aufgelöster exakter Modellkennung.

## 0. Arbeitsbereich, Ablage und Agentenhinweise

### 0.1 Verbindliche Verzeichnisstruktur

Alle fünf Zielrepos liegen als Geschwister in einem gemeinsamen Arbeitsverzeichnis. `workspace` ist ein Beispielname, kein vorgeschriebener absoluter Pfad. Öffne vorzugsweise dieses gemeinsame Verzeichnis in OpenCode. Der Ordner selbst ist **kein zusätzliches Git-Repository**; jedes Zielrepo behält seine eigene Historie und seine Remotes.

```text
workspace/
├── AGENTS.md
├── dateninfrastruktur-dev-stack/
│   ├── AGENTS.md
│   ├── README.md                         # vom Agenten erstellte Betriebsanleitung
│   └── docs/implementation/grundinstallation/
│       ├── README.md                     # Anleitung zu diesem Auftragspaket
│       ├── AUFTRAG_GRUNDINSTALLATION.md
│       ├── START_IMPLEMENTIERUNG.md
│       ├── START_REVIEW.md
│       ├── candidate-manifest.example.json
│       ├── AENDERUNGEN.md
│       ├── templates/
│       │   ├── AGENTS.workspace.md
│       │   ├── PHASENBERICHT.template.md
│       │   └── REVIEWBERICHT.template.md
│       ├── reports/                      # Phasenberichte und Implementierungsbelege
│       ├── candidates/<candidate-id>/     # festgeschriebene Kandidatenmanifeste
│       └── review/<candidate-id>/<run-id>/ # unabhängige Prüfberichte und Belege
├── dateninfrastruktur-sodata/AGENTS.md
├── dateninfrastruktur-jenkins-dev/AGENTS.md
├── dateninfrastruktur-jenkins-gretl-plugin/AGENTS.md
└── dateninfrastruktur-themenrepo/AGENTS.md
```

Die Dateien dieses Auftragspakets liegen ausschliesslich im genannten Dokumentationsordner. Seine `README.md` darf **nicht** die Betriebs-`README.md` im Repo-Root ersetzen. Die Unterordner für konkrete Kandidaten und Reviewläufe entstehen erst beim tatsächlichen Handoff beziehungsweise Review.

Bezeichne im Folgenden das gemeinsame Arbeitsverzeichnis als `WORKSPACE_ROOT` und den Dokumentationsordner als `DOCS_DIR`. `DOCS_DIR` ist immer `WORKSPACE_ROOT/dateninfrastruktur-dev-stack/docs/implementation/grundinstallation`. Shellkommandos erhalten einen ausdrücklich angegebenen Arbeitsordner. Relative Pfade im Kandidatenmanifest werden gemäss `path_base` gegen `WORKSPACE_ROOT` aufgelöst, nicht gegen den tief verschachtelten Manifestordner.

Bei Start direkt in einem Zielrepo: ermittle den gemeinsamen Elternordner und bestätige den Zugriff auf die benötigten Schwesterrepos. Ändere dafür keine globalen OpenCode-Einstellungen. Bereits vorhandene Arbeitsstände bleiben erhalten.

### 0.2 AGENTS.md: gemeinsame Regeln und repositoriespezifische Ergänzungen

Es gibt eine `AGENTS.md` im Arbeitsverzeichnis und jeweils eine im Root der fünf Zielrepos. Die gemeinsame Datei nennt den Auftrag, die erlaubten Zielrepos, Umfangsgrenzen und sichere Arbeitsweise. Die Repo-Dateien ergänzen nur ihren Verantwortungsbereich und wichtige Integrationsfallen. Sie ersetzen weder den vollständigen Auftrag noch die Startprompts.

Die aktive Arbeitsbereichsdatei liegt ausserhalb der fünf Git-Repos. Ihre versionierbare Vorlage ist `DOCS_DIR/templates/AGENTS.workspace.md`. Halte Vorlage und aktive Datei inhaltlich gleich; führe vorhandene Nutzerregeln zuerst kontrolliert zusammen. Die fünf Repo-Dateien werden in ihrem jeweiligen Repo versioniert. Kein neues übergeordnetes Git-Repo, keine Submodule und keine Symlinks sind hierfür erforderlich.

**Vor der Arbeit ausdrücklich lesen:** die gemeinsame `AGENTS.md` (ersatzweise die versionierte Vorlage), diesen Auftrag vollständig, den rollenbezogenen Startprompt und die `AGENTS.md` jedes betroffenen Zielrepos. Verlasse dich bei mehreren Git-Repos nicht darauf, dass OpenCode alle Dateien automatisch lädt oder ein Link den verlinkten Inhalt einliest. Die Referenzen sind Leseaufträge. Notiere im P0-Bericht beziehungsweise Reviewbericht die gelesenen Pfade und die tatsächliche OpenCode-/Modellkennung.

Die AGENTS-Dateien sind für beide Rollen formuliert: Ein Implementierungsauftrag erlaubt die vorgesehenen Änderungen; ein Reviewauftrag erlaubt Lesen, Bauen und Testen, aber keine Reparatur von Produktdateien. Ohne ausdrücklichen Implementierungsauftrag startet ein Reviewer keine Implementierungsarbeit. Die Modellwahl erfolgt in der jeweiligen Sitzung; AGENTS.md wechselt weder Anbieter noch Modell und ersetzt keine technischen Berechtigungen.

Die Dateien müssen widerspruchsfrei sein. Der gemeinsame Auftrag definiert Umfang und Abnahme; Repo-Hinweise ergänzen ihn. Bei einem echten Konflikt dokumentiere ihn und ändere keine Anforderungen, um ihn still aufzulösen. Übernommene Quellrepo-Anweisungen zuerst als Referenz prüfen und nur passende Konventionen übernehmen. Sie dürfen diese Zielregeln nicht unbemerkt überschreiben. Änderungen an Prüfregeln nach Kandidatenfestlegung erfordern einen neuen Kandidaten.

### 0.3 Versionierung und sensible Laufzeitdaten

Versioniere Auftrag, Prompts, AGENTS-Dateien, Vorlagen sowie die geheimnisfreien Phasenberichte im Dev-Stack beziehungsweise dem jeweils zugehörigen Repo. Fertige Kandidaten- und Reviewunterlagen können nach Abschluss als gesonderter Nachweiscommit im Dev-Stack versioniert werden; Abschnitt 8 legt fest, wie dabei Selbstreferenzen und Änderungen am Prüfgegenstand vermieden werden.

Secrets, rohe Terminalmitschnitte, lokale Datenbankdaten, Volumes und unbereinigte Toolausgaben gehören nicht unter `docs/`. Verwende dafür einen im jeweiligen Zielrepo ignorierten, instanzspezifischen Pfad, beispielsweise `dateninfrastruktur-dev-stack/.runtime/<instanz>/`, oder einen ausdrücklich ausgewiesenen temporären Pfad. Übernimm nur gezielt geprüfte, geheimnisfreie Nachweise in die Dokumentation. Führe vorhandene `.gitignore`-Regeln ergänzend weiter; ersetze sie nicht pauschal.

## 1. Ziel und Umfang

Erstelle einen lokal mit Docker Compose startbaren technischen Unterbau für die neue Dateninfrastruktur. Kopiere die unten genannten Quellen in eigenständige `dateninfrastruktur-*`-Repos. Passe den übernommenen Code nur an, soweit das für den getrennten, lauffähigen Aufbau nötig ist. Ergänze die Standardkomponenten ClickHouse, Keycloak, PostgreSQL und Superset.

Die ursprünglichen `datenportal-*`-Repos dienen als Quellen und werden nicht verändert. Der neue Stack muss neben einem bestehenden Datenportal-Stack betrieben werden können. Ein erfolgreicher Abschluss besteht aus funktionierender Grundinstallation, dokumentierter Bedienung, ausführbaren Prüfungen und unabhängigem Review des konkreten Quellstands.

### 1.1 Ergebnis dieser Etappe

- Eigene Compose-Projektgrenze mit eigenen Images, Ports, Netzwerken, Volumes und lokalen Geheimnissen.
- Garage, öffentlicher S3-Browser/rclone, APISIX, Jenkins/GRETL und Sodata aus der vorhandenen Architektur.
- Ein gültiger lokal erzeugter initialer Veröffentlichungsstand. Eine Veröffentlichung ohne gelieferte Fachdaten ist zulässig.
- ClickHouse mit persistentem Speicher, technischen Testkonten und kleinen synthetischen Testtabellen.
- Erreichbarer JDBC-Zugang für DBeaver, samt nachvollziehbarem JDBC-Test und Verbindungsanleitung.
- Keycloak mit eigenem Realm und erfundenen Identitäten als Vorbereitung für die nächste Etappe.
- PostgreSQL für die getrennten Metadatenbanken von Keycloak und Superset.
- Superset mit lokalem Administrator, persistenten Metadaten und einer tatsächlich funktionierenden ClickHouse-Verbindung.
- Technischer Nachweis, dass ein privates Testobjekt nicht über den öffentlichen Downloadweg erreichbar ist.

### 1.2 Spätere Etappen

Diese Etappe implementiert noch keinen Portal-Freigabeprozess, keine Rollenprojektion nach ClickHouse/Superset und keine AIO-/AD-/LDAP-Anbindung. Sodata bleibt im übernommenen Funktionsumfang ohne neuen Benutzerlogin. Keycloak wird noch nicht als OIDC-Login in Sodata, Jenkins oder Superset integriert. Insbesondere wird keine Verbindung zwischen Keycloak-Login und JDBC-Authentifizierung behauptet.

Fachliche CSV-Anlieferung nach ClickHouse, Historisierung, Pilotdaten-Dashboards, Self-Service, Datenwerkstatt und Agentic BI werden später gebaut. Der bestehende GRETL-/INTERLIS-/DuckDB-Publikationsvertrag des Portals bleibt für dessen Bootstrap erhalten. Das macht DuckDB nicht zur gewählten zentralen Abfrageschicht; diese ist ClickHouse.

Keine zusätzlichen Dienste wie Trino, Kafka, eigener LDAP-Server, OpenFGA, Iceberg-Katalog, CloudBeaver oder Celery/Redis allein vorsorglich einführen. Keine OpenShift-Manifeste oder Registry-Publikation in dieser Etappe. Ein kleines synthetisches Superset-Testdataset ist zulässig; ein fachliches Dashboard wird noch nicht verlangt.

## 2. Quellen und Zielrepos

Diese Quellstände wurden für den Auftrag untersucht. Verwende sie als dokumentierte Ausgangsbasis. Prüfe ihre Verfügbarkeit zu Beginn. Weicht der tatsächlich gewünschte lokale Stand ab, dokumentiere die Abweichung und ihre Auswirkungen; verwende nicht unbemerkt wechselnde Branchstände oder uncommittete Änderungen als Vorlage.

| Quellrepo unter `github.com/sogis` | Geprüfter Commit | Neues Zielrepo |
|---|---|---|
| `datenportal-dev-stack` | `915db871f777c98324c795649eabe0135d4f7165` | `dateninfrastruktur-dev-stack` |
| `datenportal-sodata` | `9db0920e58613ece3bccf5e024199c016705d5de` | `dateninfrastruktur-sodata` |
| `datenportal-jenkins-dev` | `af1fb9d201835da879a86d01a1d547276822fcd8` | `dateninfrastruktur-jenkins-dev` |
| `datenportal-jenkins-gretl-plugin` | `07e465e5432c405bdc5cbdebc2911c1eb61e1ded` | `dateninfrastruktur-jenkins-gretl-plugin` |
| `datenportal-themenrepo` | `fc87ff0b259818d112400778219ee35b88ce6c32` | `dateninfrastruktur-themenrepo` |

Die Zielrepos liegen vorzugsweise als Geschwisterverzeichnisse im gemeinsamen Arbeitsbereich. Fehlen lokale Zielrepos, darfst du sie initialisieren. Vorhandene Zielrepos, Remotes und Nutzerdaten bleiben erhalten. Keine alten Remotes umbiegen, keine fremden Arbeitsbäume bereinigen und kein `git push --mirror` verwenden. GitHub-Repos werden vom Auftraggeber angelegt; ein automatischer Remote-Push ist hier nicht erforderlich.

Der Datenblatteditor und die separate Dokumentationswebsite gehören nicht zum Pflichtumfang. Entferne ihre Startabhängigkeiten konsistent aus dem neuen Stack. Dafür müssen keine weiteren Repos kopiert werden. Stack-README und technische Dokumentation liegen im neuen Dev-Stack.

### 2.1 Saubere Übernahme

1. Erfasse Ausgangszustand und Quellcommit, ohne vorhandene Quellrepos zu verändern. Arbeite bei Bedarf mit separaten Quell-Checkouts.
2. Übernimm die benötigten Dateien des festgelegten Git-Baums mit nachvollziehbarer Kopierliste. Erhalte Lizenzen, Copyrightvermerke und Provenienz. Die Zielrepos erhalten eine eigene Git-Historie mit Verweis auf die Quelle.
3. Schliesse `.git`, echte `.env`-Dateien, Zugangsdaten, Laufzeitvolumes, Buildausgaben, Caches und besonders `jenkins-home/` aus. Templates wie `.env.example` sowie Gradle-/Maven-Wrapper und notwendige Lockdateien bleiben erhalten. Prüfe Ausschlüsse nach Pfad und Inhaltstyp, nicht durch pauschales Löschen aller JARs oder aller versteckten Dateien.
4. **Im Jenkins-dev-Quellrepo ist `jenkins-home/` getrackt.** Daher ist ein ungefilterter Export aller getrackten Dateien ebenso ungeeignet wie das Kopieren des gesamten Verzeichnisses. Übernimm weder diesen Laufzeitzustand noch dessen alte Git-Historie. Lies oder exportiere keine enthaltenen Schlüsselwerte.
5. Ergänze passende `.gitignore`-Regeln im Ziel und dokumentiere kopierte sowie bewusst ausgelassene Pfade. Prüfe am Ende, dass die ursprünglichen Quellarbeitsbäume unverändert geblieben sind.
6. Die Zielrepos sind durch die vorab abgelegten `AGENTS.md`- und Auftragsdateien möglicherweise bereits nicht leer. Das ist kein Fehler und kein Grund, die Zielverzeichnisse neu anzulegen oder zu löschen. Erhalte diese Dateien samt bereits vorhandener Nutzerarbeit. Kein `rsync --delete`, kein ungeprüftes Überschreiben vorhandener `AGENTS.md`, keine Quell-Anweisungsdateien ungeprüft aktivieren. Neue und alte README-Dateien nach ihrem Ablageort unterscheiden.

### 2.2 Namespace-Regel

Neue Namen benötigen die Repos, ihre lokalen Buildkontexte und Sibling-Pfade, selbst gebaute Images, aktive SCM-Zieladressen, Compose-Projektgrenzen, Volumes und die sichtbare Produktbezeichnung, soweit konfigurierbar. Die normalen Start- und Buildpfade dürfen nicht auf alte Datenportal-Anwendungsimages oder ein dort gebautes HPI zurückfallen.

Behalte technische Schnittstellennamen zunächst bei, wenn ihre Änderung keinen funktionalen Nutzen bringt. Erstelle dafür `docs/legacy-names.md` mit Name, Fundort, Zweck und Begründung. Die folgenden Namen sind erwartete Kandidaten:

| Beizubehaltender Vertrag | Abhängigkeiten |
|---|---|
| `jenkins-gretl-dateninfrastruktur-plugin` | Maven-Artefakt, Jenkins-Plugin-ID, HPI/JPI-Datei, Assetpfade |
| `ch.so.agi.jenkins.gretldatenportal` | Java-/Jelly-Zuordnung und Jenkins-Deskriptoren |
| `gretlDatenportalJobs` | JCasC-Symbol des Plugins |
| `prepareDatenportalWorkspace` | Pipeline-Schritt im Themenrepo |
| `gretl-datenportal-seed` | Seedjob und Bootstrap-Erwartung |
| `datenportal-topic-repository` | Gemeinsamer Pipeline-Lock |
| `gretl-datenportal-job.yaml`, `gretl-datenportal-defaults.yaml`, `gretl-datenportal-teams.yaml` | Scannervertrag |
| `/opt/datenportal`, `/var/jenkins_home/gretl-datenportal/topic-repo` | Containerinterne Arbeits- und Bundlepfade |
| `DATENPORTAL_*`, `datenportal.*` | Bestehende Konfigurationsschnittstellen |
| Sodata-Artefaktname `datenportal-sodata` | Gradle-Name und Dockerfile-COPY-Pfade |
| INTERLIS-Modellnamen und fachliche Metadaten-IDs | Fachliche Verträge und Referenzen |

Eine globale Textersetzung `datenportal` → `dateninfrastruktur` ist ausdrücklich ungeeignet. Der Review unterscheidet erlaubte Kompatibilitätsnamen und Quellenbelege von unerlaubten aktiven Verbindungen zum alten Stack.

## 3. Jenkins, GRETL und Portal übernehmen

### 3.1 Plugins und Image

Kopiere das eine eigene Jenkins-Plugin in `dateninfrastruktur-jenkins-gretl-plugin`. Kopiere das Image-/Runtime-Repo nach `dateninfrastruktur-jenkins-dev`. Letzteres ist kein zweites Jenkins-Plugin. GRETL selbst ist eine Gradle-Abhängigkeit und wird nicht eigens geforkt.

Übernimm die versionierte `plugins.txt` zunächst vollständig. Sie enthält am untersuchten Stand 77 Standardplugin-Einträge einschliesslich Bibliotheks- und transitiver Abhängigkeiten. Relevante Funktionen sind JCasC, Job DSL, Matrixrechte, Pipeline, Datei-Upload, Git/Credentials, YAML-Verarbeitung und Publikations-Locks. `email-ext` und `active-directory` dürfen als installierte Abhängigkeiten bestehen bleiben; externe Benachrichtigung und AD-Anmeldung sind im lokalen Stack nicht aktiv.

Setze im normalen neuen Buildpfad `PLUGIN_SOURCE=local`. Alle Defaultpfade für `PLUGIN_REPO` zeigen auf das neue Pluginrepo. Fehlt es oder scheitert sein Build, muss der Vorgang verständlich fehlschlagen. Kein stiller Download des alten projektspezifischen HPI von `jars.interlis.guru` und kein Rückgriff auf ein altes lokales Datenportal-Image.

Dokumentiere SHA256 des frisch gebauten HPI sowie des installierten JPI/HPI im gestarteten Jenkins. Bei unveränderter Übernahme des Artefakts müssen sie übereinstimmen. Die gleichbleibende Plugin-ID allein beweist die Herkunft nicht.

### 3.2 Lokaler Jenkins-Modus

Der Image-Default ist produktionsorientiert. Konfiguriere für den neuen Stack ausdrücklich:

```yaml
JENKINS_RUNTIME_MODE: dev
CASC_JENKINS_CONFIG: /opt/datenportal/casc/jenkins-stack.yaml
THEMEN_REPO_MODE: working-tree
THEMEN_REPO_PATH: /workspace/themenrepo
THEMEN_REPO_WRITE_BACK_ENABLED: "false"
```

Mounts verweisen auf die eigene JCasC-Datei und das neue Themenrepo. Nutze lokale Testkonten; kein AIO-Zugang wird benötigt. Jenkins-Teamrechte betreffen Anlieferung und Jobs und werden nicht als ClickHouse-Datenrechte ausgegeben. Git-Rückschreiben und externe E-Mails bleiben ausgeschaltet.

Behalte den bewährten Laufzeitaufbau bei: Jenkinsbasis am Quellstand `jenkins/jenkins:2.555.2-lts-jdk21`, Pluginbau mit Java 21/Maven, zusätzliche Java-17-Laufzeit für GRETL/Gradle. Prüfe das tatsächliche Buildskript statt Java-Annahmen aus älterer Dokumentation zu übernehmen.

Das bestehende `build-offline-bundle.sh` prüft auf ein `.git`-Verzeichnis im Themenrepo. Ein normal initialisiertes Zielrepo erfüllt dies. Falls isolierte Git-Worktrees verwendet werden, ist `.git` eine Datei: verbessere dann genau diese Prüfung auf eine gültige Git-Arbeitskopie und dokumentiere die minimale Kompatibilitätsänderung.

### 3.3 Themenrepo, Modelle und initiale Veröffentlichung

Das Themenrepo ist für den Bootstrap erforderlich. `bootstrap-publication.sh` übernimmt den vom Seed erstellten Themenrepo-Stand und führt den vorhandenen Task `initializePublication` mit lokaler S3-Veröffentlichung, ohne Git-Writeback und ohne externen Portalreload aus. Nutze diesen Weg.

Die erforderlichen Katalogmodelle liegen nicht vollständig als `shared/models` im Themenrepo. Der Runtime-Build lädt sie über `stagePublicationModels` anhand von `shared/gradle/publication-models.json`, prüft ihre SHA256 und legt sie unter `offline-bundle/models` ab. `DATENPORTAL_MODELS_DIR` verweist im Image darauf. Diesen Buildpfad erhalten.

Ein gültiger leerer Fachkatalog ist für diese Etappe ausreichend. Er darf die vorhandenen öffentlichen Metadaten des Themenrepos verwenden. Das Manifest darf entsprechend dem bestehenden Vertrag `catalog: null` enthalten; referenzierte Artefakte müssen existieren. Erzeuge eine echte lesbare `catalog.duckdb` über den vorhandenen Ablauf, keine Datei, die lediglich einen erwarteten Header vortäuscht.

Die GRETL-Abhängigkeiten verwenden am Quellstand `5.0.0-SNAPSHOT`. Deshalb reichen Git-SHAs für einen bitidentischen späteren Neubau nicht aus. Erfasse das aufgelöste Abhängigkeitsmanifest und SHA256 der gebündelten JARs, ohne hier eine neue GRETL-Release- oder Lock-Initiative zu beginnen. Ein erster Build darf Internet für offizielle Images, Maven/Gradle/Node-Abhängigkeiten und Modellquellen benötigen.

### 3.4 Sodata und Gateway

Baue Sodata aus dem neuen lokalen Repo. Nutze zunächst das vorhandene Dockerfile-Target `jvm-runtime`. Der geprüfte Dockerfile-Vertrag verwendet Java 25 und Node 22. Der Gradle-Artefaktname und die dazu passenden COPY-Pfade dürfen vorläufig erhalten bleiben. Kein neuer alternativer Anwendungsbuild und kein zusätzliches Nativeimage-Projekt.

Setze `DATENPORTAL_EXPLORE_ENABLED=false`, damit SQL-/R-Labfunktionen nicht Teil dieser Etappe werden. Erhalte den vorhandenen Katalog-, Manifest- und Readinessablauf. Implementiere hier keine neue Datenbankanbindung in Sodata; eine Portal-Datenbank kommt mit dem späteren Freigabeprozess hinzu.

Beachte die vorhandene Netzwerktopologie: Der APISIX-Service `downloads` verwendet `network_mode: service:jenkins`. Der Gateway-Port wird am Jenkins-Container veröffentlicht. Sodata bezieht das Manifest intern über `http://jenkins:${GARAGE_PUBLIC_PORT}/ch.so.daten/current.json`. Passe neue Portwerte durchgängig an; `localhost` in einem Container ist kein Ersatz für den anderen Dienst. Eine Netzwerkneugestaltung ist für die Kopie nicht erforderlich.

Entferne für Datenblatteditor und Dokumentationswebsite die Services, zwingenden `depends_on`-Einträge, Routen, lokalen Build-/Pull-Zweige, Startausgaben und zugehörigen Pflicht-Smokes konsistent. Prüfe besonders `compose.yaml`, `scripts/up.sh`, lokale Compose-Overrides, `services/apisix/apisix.yaml` und `scripts/smoke-test.sh`. Ein inaktives Profil hilft nicht, solange aktive Services davon abhängen.

Deaktiviere den bisherigen `--registry-only`-Pfad für diese Etappe mit verständlicher Meldung, falls er nicht vollständig auf neue verfügbare Images und SCM-Ziele umgestellt wird. Der reguläre Weg baut lokal. Erhalte die Sperren für administrative Sodata-/APISIX-Endpunkte am öffentlichen Gateway.

## 4. Vier Standardkomponenten ergänzen

Konfigurationen, kleine Images und Initialisierungsskripte für diese Standardsoftware liegen unter `services/` im neuen Dev-Stack. Dafür braucht es keine zusätzlichen Forks der Upstream-Projekte.

### 4.1 Versionswahl

Übernommene Komponenten zunächst auf den geprüften Quellversionen halten. Für neue Dienste verwende feste Releases mit aufgezeichnetem Registry-Digest und prüfe die Hostarchitektur. Geeignete Ausgangslinien sind ClickHouse 26.8 LTS, Keycloak 26.8.1, Superset 6.1.0 und PostgreSQL 16. Prüfe die tatsächlich verfügbaren Tags, Plattformen und Treiberkompatibilität. Wähle bei Bedarf einen kompatiblen Patchstand und begründe dies. Keine `latest`- oder `master`-Tags im abgenommenen Startpfad.

Ein Versionsinventar enthält die tatsächlich verwendeten vollständigen Tags, Digests/Build-IDs, CPU-Plattform und Python-/JDBC-Treiberversionen. Verändere nicht gleichzeitig die Architektur, nur weil eine neuere Hauptversion existiert. Lokale Eigenimages erhalten nachvollziehbare Quellrevisionen; lokale Image-IDs ersetzen dort nicht vorhandene Registry-Digests.

### 4.2 PostgreSQL

Eine Instanz mit persistentem eigenem Volume. Zwei getrennte Datenbanken und nicht privilegierte Anwendungsrollen: eine für Keycloak, eine für Superset. Gemeinsamer Cluster bedeutet keine gemeinsamen Anwendungszugänge. Die Rollen erhalten nur die notwendigen Rechte in ihrer jeweiligen Datenbank; testweise angelegte fremde Anwendungstabellen dürfen nicht lesbar sein. PostgreSQL hat standardmässig keinen veröffentlichten Hostport.

Initialisierung muss wiederholbar sein und vorhandene Daten erhalten. Keine Annahme, dass `/docker-entrypoint-initdb.d` auf einem bereits initialisierten Volume erneut läuft. Datenbankmigrationen der Anwendungen werden bewusst und fehlerprüfend ausgeführt.

### 4.3 Keycloak

Realm `dateninfrastruktur`; erfundene Benutzer `anna`, `ben`, `claudia` mit stabilen Benutzer-IDs. Verwende ausschliesslich lokale Testidentitäten und lokal erzeugte Passwörter. Keine Verbindung zum AIO und kein Identitätsimport erforderlich.

Prüfe Realm, aktivierte Benutzer, OIDC-Discovery und veröffentlichte Schlüssel. Realm und Benutzer müssen nach Container-Neuerstellung aus PostgreSQL wieder vorhanden sein. Ein vorhandener Realm-Import darf bei jedem Start keine neue Identitätswelt erzeugen oder vorhandene Benutzer zurücksetzen. Wiederanlaufverhalten ausdrücklich prüfen.

Dokumentiere die externe Basis- und Issuer-URL. In dieser Etappe sind noch keine OIDC-Anwendungsclients erforderlich. Für die spätere Integration ist festzuhalten, dass Browser und konsumierende Container eine konsistente Issuer-Konfiguration brauchen; verwende keine ungetestete Clientintegration nur, um SSO als erledigt zu markieren. Lokaler Keycloak-Devbetrieb ist hier zulässig.

### 4.4 ClickHouse

Eine lokale OSS-Instanz mit persistentem Daten- und Konfigurationszustand. Native Tabellen reichen; keine Cluster-/Keeper- oder Lakehouse-Installation.

Richte einen nur für Initialisierung/Administration verwendeten Zugang, einen technischen SQL-Testleser und einen technischen Superset-Leser ein. Diese Konten sind keine automatisch freigegebenen persönlichen Mitarbeiterkonten. Zugangsdaten werden lokal erzeugt. Kein anonym nutzbarer Defaultbenutzer mit umfassenden Rechten.

Eine minimale synthetische Tabelle, beispielsweise `foundation.smoke_metrics`, enthält drei deterministische Testzeilen. Eine zweite vorhandene Testtabelle dient als Negativkontrolle für fehlende Leserechte. Beide dürfen keine tatsächlichen nicht öffentlichen Daten enthalten. Testdateninitialisierung darf beim Wiederanlauf keine Zeilen vervielfachen oder nachträglich ergänzte Testzeilen löschen.

Die Leser dürfen die freigegebene Testtabelle abfragen, aber keine anderen Fachtabellen lesen, keine Daten verändern, kein DDL ausführen und keine Rechte vergeben. Profile und Quoten für diesen lokalen Test nachvollziehbar konfigurieren. Der Superset-Login verwendet niemals den ClickHouse-Administrator.

Dokumentiere für DBeaver Host, Port, Datenbank, Treiber/Version, JDBC-URL und die lokale Stelle für Zugangsdaten. Prüfe den Zugang mit dem angegebenen JDBC-Treiber tatsächlich, etwa durch einen kleinen ausführbaren JDBC-Smoke. Der Standardweg nutzt den HTTP-Port 8123 des Containers, extern gemäss Porttabelle. Der native Port 9000 ist optional. Ein erfolgreicher HTTP-`SELECT 1` ersetzt keinen JDBC-Nachweis. Ein UI-Test von DBeaver ist zusätzlich möglich, aber keine Pflicht, wenn der dokumentierte JDBC-Pfad getestet wurde.

### 4.5 Superset

Erweitere das offizielle Releaseimage mit den nötigen exakt festgehaltenen Treibern: PostgreSQL für die Metadatenbank sowie `clickhouse-connect` für ClickHouse. Beachte, dass das schlanke Superset-Image auch für PostgreSQL nicht automatisch alle Treiber mitbringt. Installiere in die vom Image tatsächlich verwendete Python-Umgebung.

Initialisiere Metadatenbank, Rollen und lokalen Administrator idempotent. Ein bei der ersten Initialisierung erzeugter `SECRET_KEY` bleibt über Neustarts erhalten. Speichere die ClickHouse-Verbindung mit dem eingeschränkten technischen Superset-Konto. Ein Test muss über Supersets tatsächlich installierten SQLAlchemy-/ClickHouse-Treiber eine Abfrage ausführen; ein separater `curl` aus dem Container genügt dafür nicht.

Synchrone Abfragen genügen. Kein Redis, Celery Worker/Beat, Reporting-Browser oder E-Mail-Versand für diese Etappe. Keine öffentlichen Dashboards und keine automatische Benutzerregistrierung. Die Existenz eines Keycloak-Benutzers erzeugt noch keine Superset- oder ClickHouse-Rechte. Diese Grenze steht ausdrücklich im README.

## 5. Isolation, Konfiguration und lokale Daten

### 5.1 Vorgeschlagene Hostports

Diese Werte sind neue konfigurierbare Defaults; sie stammen nicht aus der alten Umgebung.

| Dienst | Bindung |
|---|---|
| Portal/Gateway/Jenkins | `127.0.0.1:18081` |
| Garage S3 API | `127.0.0.1:13900` |
| Keycloak | `127.0.0.1:18080` |
| Superset | `127.0.0.1:18088` |
| ClickHouse HTTP/JDBC | `127.0.0.1:18123` |
| ClickHouse Native, optional | `127.0.0.1:19000` |
| PostgreSQL | intern, kein Hostport |

Verwende standardmässig Compose-Projekt `dateninfrastruktur-dev-stack`. Alle Skripte beachten denselben konfigurierbaren Projektnamen, denselben Env-Dateipfad und dieselbe Compose-Dateiliste. Keine festen `container_name`- oder externen Volumennamen, die Instanzen kollidieren lassen. Hostports sind konfigurierbar; Containerports und interne URLs müssen dazu konsistent bleiben.

Der Reviewer kann einen zusätzlichen Projektnamen, eine eigene Env-Datei, eigene temporäre Laufzeitpfade und andere Hostports verwenden. Ein anderer Projektname allein isoliert keine festen Bind-Mounts. Generierte Geheimnisse, Garage-Konfigurationen und andere schreibbare Hostpfade müssen ebenfalls instanzspezifisch sein. Alternativ arbeitet der Reviewer aus vollständigen separaten Kandidaten-Checkouts mit eigenen lokalen Laufzeitverzeichnissen.

### 5.2 Geheimnisse und Zieladressen

Übernimm die vorhandene Initialisierung sinnvoll: lokale Zufallswerte, restriktive Dateirechte, ignorierte lokale Dateien und keine Geheimnisse in Git. Vorhandene Werte bei jedem Start wiederverwenden. Kein automatischer Secret-Reset, kein `set -x` um Zugangsdaten und keine vollständigen interpolierten Compose-Konfigurationen oder Container-Env-Ausgaben im Reviewprotokoll. Beim Persistenztest darf das Testprogramm Werte intern vergleichen; protokolliere nur das Vergleichsergebnis, keine Secret-Werte oder deren Hashes.

Alle aktiven S3-Schreib-, Manifest-, Reload- und SCM-Writeback-Ziele sind lokal beziehungsweise deaktiviert. Prüfe auch Defaults im Themenrepo und in optionalen Startpfaden. Öffentliche Downloadquellen für Buildabhängigkeiten und beschreibende Metadaten-URIs sind davon zu unterscheiden. Insbesondere keine Schreib- oder Reloadoperation gegen `ch.so.daten-test` oder einen bestehenden Datenportal-Dienst auslösen.

### 5.3 Öffentlicher und privater S3-Pfad

Der öffentliche lokale Bucket `ch.so.daten` darf in der eigenen Garage-Instanz bleiben. Sein Name erzeugt bei vollständig getrennter Instanz keine Kopplung zum alten Stack. Ein zusätzlicher Bucket `ch.so.dateninfrastruktur.private` enthält nur ein synthetisches Testobjekt mit eindeutiger Kennung.

Der öffentliche Browser/rclone erhält ausschliesslich Leserechte auf den öffentlichen Bucket. Für den privaten Bucket keine Websitefreigabe, keine Public-Route und keine Berechtigung für den öffentlichen Leseschlüssel einrichten. Die vorhandene Kombination aus authentifiziertem rclone-Zugriff und öffentlichem Gateway bedeutet: Ein S3-Objektattribut `private` allein schützt keine über diesen Weg ausgelieferte Datei.

Prüfe zuerst den erfolgreichen berechtigten Abruf des existierenden privaten Testobjekts. Prüfe anschliessend, dass weder anonymer S3-Zugriff, öffentlicher Leseschlüssel noch Gateway/Public-Browser dessen Inhalt liefern. HTTP-Status, Antwortinhalt und Zielpfad gemeinsam prüfen; ein 200 mit SPA-Fehlerseite oder ein 404 auf einer nie angelegten Datei ist kein belastbarer Nachweis.

Keine geschützten Datenzeilen oder privaten Testobjekte in öffentliche CSV-/Parquet-/DuckDB-Artefakte aufnehmen. Die spätere autorisierte Auslieferung privater Dateien ist noch nicht zu implementieren.

## 6. Arbeit in überprüfbaren Phasen

| Phase | Arbeit | Prüffähiger Zwischenstand |
|---|---|---|
| P0 | Quellen/Ziele, vorhandene Arbeitsstände, Tools, Architektur, OpenCode-Modelle und Versionswahl feststellen | Inventar, Kopierplan, konkrete Abweichungen/Blocker |
| P1 | Fünf Repos übernehmen; Namespace, lokale Builds, Jenkins-Modus, Gateway und Bootstrap anpassen | Alter Kern startet aus den neuen Quellen und erzeugt eine gültige lokale Veröffentlichung |
| P2 | PostgreSQL, Keycloak, ClickHouse und Superset ergänzen | Persistente Dienste, eingeschränkte technische Zugänge, echter JDBC- und Superset-Treibertest |
| P3 | Öffentlichen/privaten Speicher prüfen; frischen Start, Wiederanlauf und Isolation prüfen; Dokumentation und Reviewpaket vervollständigen | Vollständiger Kandidat mit den unten genannten Nachweisen |

Arbeite innerhalb dieses Umfangs selbstständig. Jeder Zwischenstand enthält seine tatsächlichen Prüfergebnisse. Pflege dazu `DOCS_DIR/reports/P0.md` bis `P3.md` gemäss der Phasenberichtvorlage. Bereits festgeschriebene Kandidaten und Reviewläufe werden nicht rückwirkend umgeschrieben. Zwischenreviews sind möglich; sie ersetzen die Abschlussabnahme nicht. Mache gewöhnliche Build- oder Konfigurationskorrekturen selbst. Halte nur bei einem echten Zugangshindernis, notwendiger destruktiver Änderung oder einer nicht erfüllbaren Anforderung an und beschreibe den konkreten Grund.

### 6.1 Bedienung des Ergebnisses

Erhalte vorhandene passende Skripte und ergänze nur fehlende Fähigkeiten. Dokumentiere genau einen unterstützten lokalen Standardweg, mindestens für:

1. Voraussetzungen prüfen und lokale Konfiguration erstmalig erzeugen.
2. Eigene Images bauen und den Stack initialisieren/starten.
3. Status und relevante Logs anzeigen.
4. Technische Smokes und Negativtests ausführen.
5. Stoppen und erneut starten, ohne Volumes zu löschen.
6. Einen ausdrücklich ausgewählten temporären Reviewstack bereinigen.

Skripte propagieren Fehlercodes. Warten auf Readiness erfolgt mit Deadline und brauchbarer Diagnose, nicht mit blindem `sleep`. Ein normales Stoppen enthält kein `down -v`. Löschende Befehle sind auf eindeutig eigene temporäre Reviewressourcen zu begrenzen. Kein `docker system prune`.

Nutze native Hostarchitektur, wenn die Images und Builds sie unterstützen. Dokumentiere benötigte Docker-Ressourcen anhand des tatsächlichen Laufs. Keine globale Toolinstallation, erzwungene amd64-Emulation oder Änderung bestehender OpenCode-Accounts als beiläufige Voraussetzung.

## 7. Verbindliche Abnahmekriterien

Jedes Kriterium erhält im Review `PASS`, `FAIL` oder `BLOCKED`. Nicht ausgeführt bedeutet nicht bestanden. Prüfe mit kleinen sinnvollen Integrationstests; keine umfangreiche zusätzliche Testplattform aufbauen.

| ID | Nachweis |
|---|---|
| G01 | Alle fünf Zielrepos sind vorhanden; Quelle/Commit und Ausschlüsse sind dokumentiert; ursprüngliche Quellarbeitsbäume sind unverändert. |
| G02 | Keine übernommenen Runtimeverzeichnisse, Quell-Secrets oder alte Git-Historie mit `jenkins-home`; Lizenzen und erforderliche Builddateien sind erhalten. |
| G03 | Aktive Buildkontexte, SCM-Pfade, eigene Images, Mounts und Projektgrenzen zeigen auf die neue Umgebung; erlaubte Legacy-Namen sind begründet. Keine stillen alten Image-/HPI-Fallbacks. |
| G04 | Eigene Jenkins- und Sodata-Images wurden aus den Zielquellen gebaut; Image-IDs, Architektur, Quellstände und Plugin-Herkunft sind belegt. |
| G05 | Standardpluginliste ist nachvollziehbar übernommen; eigenes Plugin ist aktiv; gebauter und installierter HPI/JPI-Hash passen zusammen; JCasC lädt ohne unbekannte Symbole. |
| G06 | Jenkins läuft im lokalen Modus ohne AD; Seedjob erfolgreich; erwartete Jobs aus dem neuen Themenrepo vorhanden; Startformular und seine CSS-/JS-Ressourcen erreichbar. |
| G07 | GRETL-/Java-/Modellbundle vorhanden; initiale lokale Veröffentlichung erfolgreich; Manifestreferenzen und echte DuckDB-Datei gültig; Sodata lädt diesen Stand und wird bereit. |
| G08 | Nicht benötigte Editor-/Docs-Abhängigkeiten sind konsistent entfernt; Explore ist deaktiviert; administrative Gateway-Sperren bleiben wirksam. |
| G09 | Keine aktive Veröffentlichung, Git-Schreiboperation, Benachrichtigung oder Reloadoperation gegen die bestehende Umgebung; lokale Zieladressen sind nachgewiesen. |
| G10 | Vollständige neue Versionstags, aufgelöste Digests/Build-IDs, Treiberversionen und bekannte Snapshot-Einschränkungen sind dokumentiert. |
| G11 | Keycloak und Superset verwenden getrennte PostgreSQL-Datenbanken/-Rollen; keine Superuser-Anwendungszugänge; Negativtest auf fremde Testtabellen erfolgreich. |
| G12 | Keycloak-Realm, drei Demoidentitäten, Discovery und JWKS vorhanden; tatsächliche externe Issuer-URL dokumentiert. Keine erfundene SSO-Integration behauptet. |
| G13 | ClickHouse-SQL mit technischen Lesern erfolgreich; Zugriff auf vorhandene nicht freigegebene Testtabelle, INSERT, DDL und Rechtevergabe scheitern aus dem erwarteten Berechtigungsgrund. Anonymer/falscher Login erhält keine Testdaten. |
| G14 | Dokumentierter JDBC-Treiber und URL wurden vom Host beziehungsweise über den veröffentlichten Port tatsächlich geprüft; Anleitung für DBeaver vollständig. Begrenzung eines fehlenden UI-Tests offen benannt. |
| G15 | Superset initialisiert, Login funktioniert, Metadaten liegen in PostgreSQL; gespeicherte Verbindung fragt ClickHouse über den tatsächlichen Superset-Treiber mit eingeschränktem Konto ab. |
| G16 | Privates Testobjekt existiert und ist berechtigt lesbar; anonymer Zugriff, Public-Leseschlüssel und öffentlicher Gateway liefern den Inhalt nachweislich nicht. Öffentliche Artefakte enthalten es nicht. |
| G17 | Standard-Hostports sind nur an Loopback gebunden und konfigurierbar; PostgreSQL intern; Compose-, Volume- und schreibbare Hostpfade sind instanzspezifisch. |
| G18 | Frischer Start mit neuen, ausschliesslich eigenen Testvolumes läuft über den dokumentierten Standardweg ohne manuelle UI-Reparaturen durch. |
| G19 | Zweiter Start sowie Stoppen/Container-Neuerstellung mit denselben Volumes erhalten Secrets, Keycloak-IDs, Superset-Verbindung und eine nach der Initialisierung ergänzte ClickHouse-Testzeile; keine Seedduplikate. |
| G20 | Ein isolierter Reviewlauf mit anderem Projekt/Ports beeinflusst weder die Arbeitsinstanz noch einen vorhandenen Datenportal-Stack. Ressourcen vor/nach dem Lauf nachgewiesen. |
| G21 | Start-/Testskripte melden echte Fehler mit Exitcode; fehlende Pflichtabhängigkeiten oder Pluginquelle erzeugen keinen scheinbar erfolgreichen Ersatzstart. |
| G22 | README enthält Voraussetzungen, Start/Stop, URLs, Zugriff auf lokale Credentials ohne deren Veröffentlichung, JDBC-Anleitung, Grenzen, Diagnose und scoped Bereinigung. |
| G23 | Die Ablage entspricht Abschnitt 0/8.1. Kandidatenmanifest bezeichnet alle fünf Quellstände, Anweisungsdateien, Prüfkommandos und Modelle eindeutig; Nachweise sind vom Produktstand getrennt; Belege enthalten keine Geheimnisse; nach Reviewbeginn wurde der Prüfgegenstand nicht unbemerkt verändert. |
| G24 | Unabhängiger Qwen-Reviewer hat die relevanten Laufzeitprüfungen selbst ausgeführt und jeden Befund geklärt oder als offen markiert; Gesamtstatus folgt den Regeln in Abschnitt 8. |

Bei Autorisierungsnegativtests zunächst mit demselben gültigen Konto einen erlaubten Kontrollzugriff belegen. Bei Authentifizierungsnegativtests zuerst Erreichbarkeit, Zielpfad und vorhandene Testdaten mit einem gültigen Referenzkonto prüfen; anschliessend gezielt anonyme Anmeldung beziehungsweise falsche Zugangsdaten testen. Ein Netzwerkfehler, fehlender Treiber, SQL-Syntaxfehler oder eine nicht vorhandene Tabelle zählt nicht als korrekt verweigerter Zugriff.

G19 prüft die eigenen Testressourcen; es darf keine fremde Nutzerinstanz gestoppt werden. Für G20 muss ein fehlender bereits laufender Altstack nicht eigens installiert werden: Dann belege getrennte Konfiguration/Ressourcen und einen parallelen zweiten Kandidatenstack. Kennzeichne ausdrücklich, ob tatsächlicher Parallelbetrieb mit dem Altstack geprüft wurde.

## 8. Handoff und unabhängiges Review

### 8.1 Verbindliche Ablage von Dokumentation und Nachweisen

Die folgenden Pfade sind relativ zum Root von `dateninfrastruktur-dev-stack`:

| Pfad | Inhalt und Pflege |
|---|---|
| `README.md` | Vom Implementierer erstellte ausführbare Betriebsanleitung; nicht mit der Paket-README verwechseln |
| `docs/provenance.md` | Quellen, Ausschlüsse, Anpassungen und Herkunft je Repo |
| `docs/legacy-names.md` | Begründete technische Kompatibilitätsnamen |
| `docs/foundation-status.md` | Technischer Stand und Grenzen beim Handoff; keine selbst ausgestellte unabhängige Abnahme |
| `docs/implementation/grundinstallation/` | Verbindlicher Auftrag, beide Startprompts, Beispielmanifest und Vorlagen |
| `docs/implementation/grundinstallation/reports/P0.md` bis `P3.md` | Phasenberichte des Implementierers mit tatsächlich ausgeführten Prüfungen |
| `docs/implementation/grundinstallation/reports/evidence/<phase>/<run-id>/` | Kleine, gezielt bereinigte Implementierungsbelege |
| `docs/implementation/grundinstallation/candidates/<candidate-id>/candidate-manifest.json` | Unveränderliches Manifest des konkret übergebenen Kandidaten |
| `docs/implementation/grundinstallation/candidates/<candidate-id>/snapshots/` | Bei Bedarf Datei-/Diff-Manifeste je Zielrepo, einschliesslich relevanter ungetrackter Produktdateien |
| `docs/implementation/grundinstallation/review/<candidate-id>/<run-id>/REVIEW.md` | Eigenständiger Bericht des Qwen-Reviewers |
| `docs/implementation/grundinstallation/review/<candidate-id>/<run-id>/evidence/` | Geheimnisfreie Belege dieses unabhängigen Reviewlaufs |

Verwende eindeutige Kennungen, beispielsweise `c001` und `r001`; ein neuer Kandidat oder Reviewlauf bekommt eine neue Kennung. Die Beispieldateien und Vorlagen sind keine Nachweise. Das Versionsinventar und die Abhängigkeitsmanifeste können unter `reports/evidence/` liegen und werden im Kandidatenmanifest eindeutig referenziert.

Ein Phasenbericht enthält Ziel, tatsächlichen Stand, betroffene Repos/Dateien, technische Entscheidungen, ausgeführte Kommandos **mit Arbeitsverzeichnis und Exitcode**, Ergebnisse, zugehörige G-IDs, Blocker und nächste Schritte. Ein Implementierungsstatus lautet etwa „lokal geprüft; unabhängige Abnahme ausstehend“. Nur ein tatsächlich durchgeführtes unabhängiges Review darf als solches dokumentiert werden.

#### Kandidatenstand ohne Selbstreferenz

1. **Vor dem Handoff:** Stelle Produktdateien, Anforderungen, Prompts, AGENTS-Dateien und die Implementierungsberichte fertig. Bevorzugt erhält jedes Zielrepo einen sauberen lokalen Kandidatencommit. Keine fremden Änderungen mitcommitten und kein Remote-Push. Ohne Commit dokumentierst du zusätzlich vollständige Datei-/Diff-Hashes einschliesslich relevanter ungetrackter Produktdateien.
2. **Danach:** Erzeuge `candidates/<candidate-id>/candidate-manifest.json` nach dem Beispiel. Es bezeichnet die gerade festgeschriebenen fünf Quellstände. `requirements.path` und alle repoübergreifenden relativen Manifestpfade beziehen sich auf `WORKSPACE_ROOT`. Erfasse zusätzlich Pfade und SHA256 der verwendeten Anweisungsdateien, insbesondere aller sechs aktiven AGENTS-Dateien und beider Startprompts. Hashes von Produkt-/Anweisungsdateien sind erlaubt; Hashes von Secrets bleiben verboten.
3. **Prüfgegenstand:** Zum Produktstand gehören auch Tests, `.gitignore`, Auftrags-/Prompt-/AGENTS-Dateien, Vorlagen und Phasenberichte. Nur die nachträglich erzeugten Unterbäume `candidates/<candidate-id>/` und `review/<candidate-id>/<run-id>/` sind Nachweisartefakte ausserhalb dieses Produktstands. Ihre Zuordnung wird im Manifest festgehalten; ältere Kandidaten- und Reviewunterbäume werden ebenso als Nachweise behandelt. Die `README.md`-Dateien direkt unter `candidates/` und `review/` bleiben Produktdokumentation. Niemals pauschal `docs/` oder alle ungetrackten Dateien aus der Prüfung ausschliessen.
4. **Während des Reviews:** Weder Manifest, Anforderungen, Anweisungen noch Produktdateien verändern. Der Reviewer schreibt ausschliesslich seinen neuen Reviewbericht und eigene Belege und nutzt eigene isolierte Laufzeit-/Builddaten. Er prüft den Produktstand vor und nach seinem Lauf. Ein durch neue Nachweisdateien nicht leerer `git status` ist erklärbar, aber kein Ersatz für den inhaltlichen Vergleich.
5. **Nach Abschluss:** Der Implementierer oder Auftraggeber kann das eingefrorene Manifest und die finalen geheimnisfreien Reviewunterlagen in einem **separaten Nachweiscommit** im Dev-Stack versionieren. Der Reviewer verändert hierfür selbst keine Produkt-Commits. Das Manifest wird nicht nachträglich auf den Nachweiscommit umgeschrieben: Es referenziert weiterhin genau den geprüften Produktstand. Im Reviewbericht stehen Manifest-SHA256 und Kandidatenkennung.
6. **Bei Korrekturen:** Produktänderungen ergeben neue Commits/Hashes und einen neuen Kandidaten. Frühere Manifestdateien und Berichte bleiben unverändert. Der Reviewer beurteilt erneut beziehungsweise begründet die zulässige Übernahme alter Belege nach Abschnitt 8.3.

Die aktive `WORKSPACE_ROOT/AGENTS.md` liegt ausserhalb der fünf Repos. Ihr Hash wird trotzdem im Manifest erfasst; die Vorlage unter `templates/AGENTS.workspace.md` ist versioniert. Bei einer isolierten Reviewkopie darf sich der absolute Workspacepfad ändern. Relative Pfade und Datei-Hashes müssen identisch auflösbar bleiben. Protokolliere die lokale Pfadzuordnung, statt das eingefrorene Manifest zu editieren.

### 8.2 Modell- und Sitzungsbindung

Ermittle die installierte OpenCode-Version und die tatsächlichen Provider-/Modellkennungen über die normale Oberfläche oder dokumentierte CLI. Bestehende Authentifizierung weiterverwenden. Keine API-Schlüssel in Projektdateien, Prompts, Kommandoausgaben oder Logs schreiben.

Der Implementierungsagent ist DeepSeek Flash über die DeepSeek-API. Der Reviewagent ist das vom Nutzer bezeichnete Qwen 3.8 27b über Infomaniak. Wenn dessen Modellkennung nicht eindeutig verfügbar ist, dokumentiere dies als Reviewblocker. Kein stiller Modellwechsel. Ein kurzer funktionierender Lese-/Shell-Aufruf in der jeweiligen Sitzung muss zeigen, dass der Zugang als Coding-Agent verwendbar ist.

Eine neue Qwen-Sitzung erhält Auftrag, Reviewprompt und Kandidatenmanifest. Sie übernimmt nicht die Implementierungsunterhaltung als Autorität und verwendet keine Fortsetzungsoption auf deren Sitzung. Zusätzliche OpenCode-Agentenkonfiguration ist optional; falls erstellt, muss sie zur installierten Version passen und einen separat startbaren Reviewagenten erlauben.

### 8.3 Befugnisse und Entscheidung

Der Reviewer liest Produktdateien, führt Builds/Tests aus und schreibt eigene Belege. Buildcaches, temporäre Testdaten und ein eigener Compose-Testlauf sind erlaubt. Er verändert oder repariert keinen Produktcode und keine Produktkonfiguration. Vergleiche den Kandidaten vor und nach den Prüfungen. Eine OpenCode-Regel `edit: deny` ist kein Betriebssystem-Schreibschutz gegen Shellbefehle.

Für jeden Befund: betroffene Datei/Funktion, Anforderung, beobachtetes Verhalten, reproduzierbarer Prüfschritt, erwartetes Ergebnis und Schwere. Ein fehlender Nachweis wird nicht als erfundener Produktfehler ausgegeben; er kann die Abnahme dennoch blockieren.

- **PASS:** Alle Pflichtkriterien bestanden; keine offenen funktionsrelevanten Befunde. G24 wird durch den tatsächlichen unabhängigen Lauf abgeschlossen.
- **FAIL:** Mindestens eine Pflichtanforderung nachweislich verletzt.
- **BLOCKED:** Kein bereits festgestellter Fehler erklärt den Gesamtstatus, aber mindestens ein Pflichtnachweis ist wegen Umgebung, Zugang, Modell oder fehlendem Test nicht möglich.

Wenn sowohl Fehler als auch Blocker vorliegen, lautet der Gesamtstatus `FAIL`; Blocker bleiben separat sichtbar. `NOT RUN` darf als Detail vorkommen, zählt aber nicht als `PASS`. Nach Produktänderungen ein neues Kandidatenmanifest erzeugen und betroffene Prüfungen erneut unabhängig durchführen. Frühere Belege bleiben an ihren damaligen Kandidaten gebunden. Für nicht wiederholte Kriterien muss der Reviewer ausdrücklich belegen, dass der geprüfte Gegenstand und seine relevanten Abhängigkeiten unverändert sind und der alte Nachweis weiter anwendbar ist. Er referenziert dazu den früheren Kandidaten und Beleg. Ist diese Übertragbarkeit nicht nachweisbar, wird die Prüfung wiederholt.

## 9. Primärquellen und konkrete Einstiegspunkte

Die technischen Befunde sind aus folgenden Quellen abgeleitet. Prüfe bei Abweichungen die tatsächlich ausgecheckten Dateien. URLs zu alten Repos in diesem Quellenabschnitt sind Herkunftsnachweise, keine Laufzeitabhängigkeiten.

### Bestehender Stack

- [Dev-Stack README](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/README.md)
- [Compose](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/compose.yaml)
- [Startskript](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/scripts/up.sh)
- [Jenkins-Buildwrapper](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/scripts/build-jenkins-local.sh)
- [Bootstrap](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/scripts/bootstrap.py)
- [Initiale Veröffentlichung](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/scripts/bootstrap-publication.sh)
- [Lokales JCasC](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/services/jenkins/jenkins-stack.yaml)
- [APISIX-Routen](https://github.com/sogis/datenportal-dev-stack/blob/915db871f777c98324c795649eabe0135d4f7165/services/apisix/apisix.yaml)
- [Sodata Dockerfile](https://github.com/sogis/datenportal-sodata/blob/9db0920e58613ece3bccf5e024199c016705d5de/Dockerfile)
- [Sodata Konfiguration](https://github.com/sogis/datenportal-sodata/blob/9db0920e58613ece3bccf5e024199c016705d5de/src/main/resources/application.yml)

### Jenkins und Themenrepo

- [Plugin README und technische ID](https://github.com/sogis/datenportal-jenkins-gretl-plugin/blob/07e465e5432c405bdc5cbdebc2911c1eb61e1ded/README.md)
- [Plugin POM](https://github.com/sogis/datenportal-jenkins-gretl-plugin/blob/07e465e5432c405bdc5cbdebc2911c1eb61e1ded/pom.xml)
- [Standardplugins](https://github.com/sogis/datenportal-jenkins-dev/blob/af1fb9d201835da879a86d01a1d547276822fcd8/plugins.txt)
- [Jenkins Dockerfile](https://github.com/sogis/datenportal-jenkins-dev/blob/af1fb9d201835da879a86d01a1d547276822fcd8/Dockerfile)
- [Pluginquellwahl](https://github.com/sogis/datenportal-jenkins-dev/blob/af1fb9d201835da879a86d01a1d547276822fcd8/bin/prepare-image-context.sh)
- [Offline-Bundle](https://github.com/sogis/datenportal-jenkins-dev/blob/af1fb9d201835da879a86d01a1d547276822fcd8/bin/build-offline-bundle.sh)
- [Modellbereitstellung](https://github.com/sogis/datenportal-jenkins-dev/blob/af1fb9d201835da879a86d01a1d547276822fcd8/build.gradle)
- [Themenrepo Jenkinsfile](https://github.com/sogis/datenportal-themenrepo/blob/fc87ff0b259818d112400778219ee35b88ce6c32/shared/Jenkinsfile)
- [Themenrepo Initialisierung](https://github.com/sogis/datenportal-themenrepo/blob/fc87ff0b259818d112400778219ee35b88ce6c32/shared/gradle/datenportal-initialize.gradle)
- [GRETL-Abhängigkeiten](https://github.com/sogis/datenportal-themenrepo/blob/fc87ff0b259818d112400778219ee35b88ce6c32/shared/gradle/gradle-build.properties)
- [Modellmanifest](https://github.com/sogis/datenportal-themenrepo/blob/fc87ff0b259818d112400778219ee35b88ce6c32/shared/gradle/publication-models.json)

### Neue Standardkomponenten und Agenten

- [ClickHouse 26.8 LTS](https://presentations.clickhouse.com/2026-release-26.8/)
- [ClickHouse SQL-Zugriffsverwaltung](https://clickhouse.com/docs/operations/access-rights)
- [ClickHouse JDBC](https://clickhouse.com/docs/integrations/java/jdbc-v2)
- [Keycloak Datenbankkonfiguration](https://www.keycloak.org/server/db)
- [Keycloak 26.8.1](https://www.keycloak.org/2026/10/keycloak-2681-released)
- [Superset 6.1 Dockerimages und Treiber](https://superset.apache.org/admin-docs/6.1.0/installation/docker-builds/)
- [OpenCode CLI](https://opencode.ai/v2/docs/cli/commands/)
- [OpenCode Agenten](https://opencode.ai/v2/docs/agents/)
- [OpenCode V2: AGENTS.md, Geltungsbereich und Laden von Anweisungen](https://opencode.ai/v2/docs/instructions/)
- [OpenCode Berechtigungen](https://opencode.ai/v2/docs/permissions/)
- [DeepSeek API](https://api-docs.deepseek.com/)
- [Infomaniak Modellliste](https://developer.infomaniak.com/docs/api/get/2/ai/%7Bproduct_id%7D/openai/v1/models)
