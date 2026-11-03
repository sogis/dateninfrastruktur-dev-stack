# Änderungen am Auftragspaket

## Paket v2 / Auftragsrevision 1.1 – 2. November 2026

Diese Revision ergänzt die Ablage- und Agentenregeln. Sie ändert weder die Architektur noch die Phasen P0–P3, die 24 Abnahmekriterien oder die gewünschte Modellkombination inhaltlich. G23 konkretisiert die Dokumentations- und Kandidatenintegrität.

- Verbindlicher Dokumentationspfad: `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/`.
- Gemeinsamer Workspace mit fünf eigenständigen Repos; keine neue übergeordnete Git-Historie.
- Eine Workspace-AGENTS.md und fünf kurze Repo-AGENTS.md, rollenverträglich für Implementierung und unabhängiges Review.
- Versionierbare Workspace-Vorlage unter `templates/AGENTS.workspace.md`; die aktive Datei liegt im gemeinsamen Elternordner.
- Explizite Leseaufträge in beiden Startprompts; keine vorausgesetzte automatische Erkennung über Git-Grenzen.
- Schutz bereits abgelegter AGENTS-/Auftragsdateien beim späteren Kopieren aus den Quellrepos.
- Feste Pfade für Phasenberichte, Kandidatenmanifeste und getrennte unabhängige Reviewläufe.
- Trennung zwischen geprüftem Produktstand und späterem Nachweiscommit, damit versionierte Berichte keine Manifest-Selbstreferenz erzeugen.
- Beispielmanifest auf Schema 2 erweitert: relativer Pfadbezug, Anweisungsdatei-Hashes und Abgrenzung der Nachweisunterbäume.
- Leere Phasen-/Reviewberichtvorlagen; CLI-Beispiele verwenden den tatsächlichen Dokumentationspfad ab Workspace.

Die bestehenden Quellcommits, Software-Versionsvorgaben und technischen Aussagen des früheren Auftrags wurden für diese redaktionelle Ergänzung übernommen, nicht erneut auf Aktualität geprüft. Neu abgeglichen wurde die OpenCode-V2-Dokumentation zu AGENTS-Dateien und Berechtigungsgrenzen. Es wurde keine Infrastruktur implementiert und kein unabhängiges Laufzeitreview durchgeführt.

Primärquellen für die neuen Toolhinweise:

- [OpenCode V2 – Instructions](https://opencode.ai/v2/docs/instructions/)
- [OpenCode V2 – Permissions](https://opencode.ai/v2/docs/permissions/)

## Auftragsrevision 1.2 – 3. November 2026

Diese Revision ändert ausschliesslich die technische Identität des
projektspezifischen Jenkins-Plugins auf Wunsch des Auftraggebers:

- Maven-Artefakt und Jenkins-Plugin-ID: `jenkins-gretl-dateninfrastruktur-plugin`
- HPI/JPI-Dateiname und Jenkins-Assetpfade entsprechend angepasst
- alte Koordinate `jenkins-gretl-datenportal-plugin` wird nicht weiterverwendet
  und ihr fehlerhaft veröffentlichter Snapshot wird entfernt
- JCasC-Symbol `gretlDatenportalJobs`, Pipeline-Schritt
  `prepareDatenportalWorkspace`, Java-Paket und fachliche Verträge bleiben
  unverändert

Der technische Funktionsumfang, die Phasen und die Abnahmekriterien G01–G24
bleiben inhaltlich unverändert.

## Auftragsrevision 1.3 – 3. November 2026

Auf Wunsch des Auftraggebers wurde der aktive Namensraum weiter bereinigt:

- `DATENPORTAL_*` → `DATENINFRASTRUKTUR_*` in Dev-Stack, Sodata, Jenkins-Dev und
  Themenrepo
- Sodata-/Gradle-Konfiguration `datenportal.*` → `dateninfrastruktur.*`
- Gradle-/App-Artefakt `datenportal-sodata` → `dateninfrastruktur-sodata`
- Build-Properties `datenportal.plugin.*`, `datenportal.repository.*` und
  `datenportal.offline.seed.*` → `dateninfrastruktur.*`

Java-Pakete, JCasC-Symbol, Pipeline-Schritt, Seedjob, Pipeline-Lock,
Scannerdateien, Containerpfade und fachliche IDs bleiben unverändert. Der
Funktionsumfang und die Abnahmekriterien G01–G24 bleiben inhaltlich gleich.
