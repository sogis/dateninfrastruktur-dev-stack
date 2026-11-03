# Herkunft und Übernahme

Stand: 2. November 2026. Alle Zielrepos wurden aus den im Auftrag genannten
Git-Commits übernommen. Die Quellarbeitsbäume wurden nicht verändert; die
Übernahme erfolgte mit `git archive <commit>` in temporäre Verzeichnisse und
anschliessender gezielter Kopie.

## Quellen und Zielstände

| Zielrepo | Quelle | Verwendeter Quellcommit | Übernommener Umfang |
|---|---|---|---|
| `dateninfrastruktur-dev-stack` | `https://github.com/sogis/datenportal-dev-stack` | `915db871f777c98324c795649eabe0135d4f7165` | Compose, Start-/Testskripte, Garage-/APISIX-/Jenkins-Konfiguration, Bootstrap, Publication-Validator |
| `dateninfrastruktur-sodata` | `https://github.com/sogis/datenportal-sodata` | `9db0920e58613ece3bccf5e024199c016705d5de` | vollständige Anwendung, Gradle-/Maven-Wrapper, Dockerfile, Tests, Dokumentation |
| `dateninfrastruktur-jenkins-dev` | `https://github.com/sogis/datenportal-jenkins-dev` | `af1fb9d201835da879a86d01a1d547276822fcd8` | Dockerfile, Build-/Runtime-Skripte, Offline-Bundle, JCasC, `plugins.txt`, Tests, Java-17-Runtime |
| `dateninfrastruktur-jenkins-gretl-plugin` | `https://github.com/sogis/datenportal-jenkins-gretl-plugin` | `07e465e5432c405bdc5cbdebc2911c1eb61e1ded` | Maven-Plugin, Quellen, Jelly/JS/CSS, Tests, Lizenzhinweise |
| `dateninfrastruktur-themenrepo` | `https://github.com/sogis/datenportal-themenrepo` | `fc87ff0b259818d112400778219ee35b88ce6c32` | Organisationen, Datensätze, Scanner-YAML, Shared Gradle/Jenkinsfile, INTERLIS-Modelle, Publikationslogik |

Der Quellarbeitsbaum von `datenportal-dev-stack` lag zum Zeitpunkt der
Bestandsaufnahme auf dem Branch `s3-aws` und enthielt uncommittete Änderungen.
Diese wurden **nicht** verwendet. Massgeblich ist ausschliesslich der oben
genannte Commit. Die übrigen vier Quellrepos standen auf den genannten Commits
und waren sauber.

## Ausschlüsse

Folgende Pfade und Inhaltstypen wurden beim Kopieren ausgeschlossen:

- `.git/` und jede Quell-Git-Historie,
- die Quell-`AGENTS.md` (die bereits abgelegten Ziel-AGENTS bleiben erhalten),
- `jenkins-home/` des Jenkins-Dev-Quellrepos, einschliesslich aller
  Laufzeit-, Job-, Plugin- und Secret-Dateien,
- echte `.env`-Dateien, Laufzeitverzeichnisse, Volumes, Caches und
  Buildausgaben (`build/`, `target/`, `.gradle/`, `node_modules/`,
  `.runtime/`),
- der frühere Datenblatt-Editor und die separate Dokumentationswebsite
  einschliesslich ihrer Compose-Dateien, aktiven Dienste, Routen und
  Startpfade,
- veraltete Registry-/Editor-/Docs-Testskripte, die an die entfernten Dienste
  oder alte Images gebunden waren.

Nicht ausgeschlossen wurden Lizenzen, Gradle-/Maven-Wrapper, Lockdateien,
erforderliche Buildkonfiguration, Quellen, Tests und fachliche
INTERLIS-/XTF-Dateien.

## Gezielte Anpassungen

### `dateninfrastruktur-dev-stack`

- Eigenständiger Compose-Name `dateninfrastruktur-dev-stack`, neue
  Loopback-Ports und eigene Named Volumes.
- Lokale Images werden ausschliesslich aus den neuen Geschwisterrepos gebaut;
  `PLUGIN_SOURCE=local` ist der Standard. `--registry-only` ist deaktiviert.
- Neue Dienste PostgreSQL, ClickHouse, Keycloak und Superset mit festen
  Releases, Init-Skripten und getrennten Zugängen.
- APISIX-Routen für Editor und Dokumentation entfernt; private Bucket-Route
  explizit gesperrt.
- Garage initialisiert zusätzlich den privaten Bucket
  `ch.so.dateninfrastruktur.private` mit einem synthetischen Testobjekt.
- Jenkins-JCasC nutzt ein lokal erzeugtes Admin-Passwort; Git-Writeback und
  externe Benachrichtigungen bleiben aus.
- Neue Prüfskripte für JDBC, Superset-Treiber, Keycloak, PostgreSQL,
  ClickHouse-Rechte, private Storage-Wege, Isolation und Wiederanlauf.

### `dateninfrastruktur-sodata`

- Repository- und Anzeigenamen angepasst; Gradle-Projektname, Dockerfile-COPY-
  Pfade und Laufzeit-App-Name auf `dateninfrastruktur-sodata` umgestellt.
- Laufzeit-Image auf `jvm-runtime` festgelegt.
- Laufzeit-Images `ubi9/openjdk-25-runtime` und `ubi9/ubi-minimal` auf
  Digests gepinnt, damit kein `latest`-Tag im Startpfad verbleibt.
- Explore wird im Stack über `DATENINFRASTRUKTUR_EXPLORE_ENABLED=false` deaktiviert.

### `dateninfrastruktur-jenkins-dev`

- Standardpfade für Plugin und Themenrepo auf die neuen Geschwisterrepos
  umgestellt; `PLUGIN_SOURCE=local` ist der Standard.
- `jenkins-home/` wird nicht übernommen und ist im Ziel vollständig ignoriert.
- Das Offline-Bundle akzeptiert eine `.git`-Datei einer Git-Arbeitskopie
  (Worktree) als gültige Git-Arbeitskopie.
- Image-/Label-Namen auf `dateninfrastruktur-jenkins` umgestellt; die
  technische Plugin-ID und die JCasC-Verträge bleiben unverändert.

### `dateninfrastruktur-jenkins-gretl-plugin`

- Repository-URL und SCM-Angaben in `pom.xml` auf das neue GitHub-Repo
  umgestellt.
- Technische Plugin-ID und Maven-Artefakt auf
  `jenkins-gretl-dateninfrastruktur-plugin` umgestellt; HPI-/JPI-Dateiname und
  Jelly-Assetpfade wurden mitgeändert. Java-Paket
  `ch.so.agi.jenkins.gretldatenportal`, JCasC-Symbol und Pipeline-Schritt
  bleiben unverändert.

### `dateninfrastruktur-themenrepo`

- Keine fachlichen IDs, Modellnamen oder Scanner-YAML-Dateinamen geändert.
- Aktive Schreib-, Reload- und Git-Ziele bleiben lokal beziehungsweise
  deaktiviert; die Publikation läuft über den neuen Jenkins-Stack in den
  lokalen Garage-Bucket.

## Lizenzen

Die bereits abgelegten `LICENSE`-Dateien der fünf Zielrepos bleiben unverändert
erhalten. Zusätzlich liegt in jedem Zielrepo die aus dem jeweiligen Quellcommit
übernommene Lizenz als `LICENSE.upstream`. Damit bleiben sowohl der
Ziel-Copyrightvermerk als auch der Upstream-Copyrightvermerk erhalten. Herkunft
und Quell-URL sind in diesem Dokument und im Kandidatenmanifest festgehalten.
