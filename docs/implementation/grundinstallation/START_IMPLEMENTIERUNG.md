# Startprompt: Implementierung mit OpenCode und DeepSeek Flash

Verwende diesen Text in einer OpenCode-Sitzung mit dem bereits eingerichteten DeepSeek-Flash-Modell über die DeepSeek-API. Öffne den gemeinsamen Elternordner der fünf Zielrepos. Der Auftrag liegt unter `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/AUFTRAG_GRUNDINSTALLATION.md`. Die Dateien unter diesem Dokumentationsordner ersetzen nicht die Betriebs-README im Repo-Root.

---

Du bist der Implementierungsagent für die lokale Grundinstallation unserer Dateninfrastruktur. Setze den beigefügten Arbeitsauftrag vollständig um. Das Ergebnis wird von einem zweiten Agenten mit dem vom Nutzer bezeichneten Qwen 3.8 27b über Infomaniak unabhängig geprüft.

## Arbeitsverzeichnis und Anweisungen

Setze für deine Arbeit `WORKSPACE_ROOT` auf den tatsächlich geöffneten gemeinsamen Arbeitsordner und `DOCS_DIR` auf dessen Unterordner `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation`. Lies die dortige README, `WORKSPACE_ROOT/AGENTS.md`, die fünf Repo-AGENTS und den vollständigen Auftrag ausdrücklich. Fehlt die Arbeitsbereichsdatei, lies zuerst die versionierte Vorlage `DOCS_DIR/templates/AGENTS.workspace.md`; eine vorhandene Datei nicht blind überschreiben.

Bei Start aus einem einzelnen Repo müssen der Auftrag und alle benötigten Schwesterrepos trotzdem erreichbar sein. Nutze bei Git- und Buildkommandos jeweils das richtige Repo als Arbeitsverzeichnis. Kein übergeordnetes Git-Repo anlegen. Protokolliere im P0-Bericht die gelesenen Anweisungsdateien und die tatsächlichen absoluten Arbeitsordner.

## Auftrag

1. Lies `DOCS_DIR/AUFTRAG_GRUNDINSTALLATION.md` vollständig. Behandle dessen Abnahmekriterien G01–G24 als gemeinsamen Vertrag. Verändere Anforderungen oder Testbedeutung nicht, um einen fehlschlagenden Aufbau als erfolgreich auszugeben.
2. Prüfe die vorhandene Arbeitsumgebung, Quellen, Zielrepos, Docker/Compose und native Architektur. Verwende die im Auftrag festgehaltenen Quellstände. Erhalte uncommittete Nutzerarbeit und bestehende Repos. Eine fehlende lokale Zielstruktur darfst du selbst anlegen.
3. Erfasse die tatsächlich verwendete OpenCode-Version und vollständige Provider-/Modellkennung. Verwende den vorhandenen DeepSeek-Zugang. Keine globalen Accountänderungen, keine Credential-Exporte und kein Ersatzmodell. Normale Modellwahl und vorhandene Anmeldung genügen.
4. Arbeite die Phasen P0 bis P3 ab. Kopiere und ändere gezielt. Baue die eigentliche Grundinstallation und führe ihre Integrationstests aus. Liefere nicht nur einen Plan oder ungestartete Compose-Dateien.
5. Führe Quellen-/Kopiernachweis, begründete Legacy-Namen und Versionsinventar mit. Dokumentiere entscheidende Anpassungen mit Zweck und überprüfbarer Wirkung.
6. Erzeuge einen konkret benannten Kandidatenstand für alle fünf Repos, Belege und ein ausgefülltes Manifest nach `DOCS_DIR/candidate-manifest.example.json` unter `DOCS_DIR/candidates/<candidate-id>/candidate-manifest.json`. Bei uncommittierten Produktänderungen reichen HEAD-SHAs nicht aus; erfasse den tatsächlichen Datei-/Diff-Stand.

## Ablage und Übergabe

Pflege `DOCS_DIR/reports/P0.md` bis `P3.md` anhand von `templates/PHASENBERICHT.template.md`; kleine bereinigte Belege liegen unter `reports/evidence/<phase>/<run-id>/`. Den Root-README des Dev-Stacks als Betriebsanleitung erstellen, die Paket-README im Dokumentationsordner erhalten. Beim Kopieren der Quellen weder diese Auftragsdateien noch die bereits vorhandenen Repo-AGENTS überschreiben.

Vor dem Handoff Produktstand, Phasenberichte und Anweisungen festschreiben. Erst danach das Kandidatenmanifest und gegebenenfalls Datei-Manifeste unter `candidates/<candidate-id>/` erzeugen. Es nennt die vorherigen Kandidatencommits/-Hashes und die SHA256 der sechs AGENTS-Dateien, des Auftrags und der Startprompts. Es erfasst sich nicht selbst als Produktdatei. Nutze relative Manifestpfade ab `WORKSPACE_ROOT` gemäss `path_base`.

Das unabhängige Review schreibt nach `DOCS_DIR/review/<candidate-id>/<run-id>/REVIEW.md` und `evidence/`. Diese Unterlagen nicht vorab als bestanden ausfüllen. Manifest nach Handoff nicht ändern. Fertige, bereinigte Nachweise nach dem Review separat committen, ohne den Manifestbezug auf den geprüften Produktstand umzuschreiben. Abschnitt 8.1 des Auftrags ist dafür verbindlich.

## Besondere Punkte, die leicht übersehen werden

- Genau ein projektspezifisches Jenkins-Plugin wird kopiert; die normalen Jenkins-Plugins bleiben unveränderte Abhängigkeiten.
- Kein Quell-`jenkins-home`, keine alten Secrets, kein Klonen alter Runtime-Historie in die neuen Repos.
- `PLUGIN_SOURCE=local`; kein HPI-/Image-Fallback in den alten Namespace. Plugin-ID, JCasC-Symbol und Pipelineschritte zunächst kompatibel halten.
- Jenkins ausdrücklich im lokalen Modus; eigenes JCasC und neues Themenrepo; Git-Writeback aus.
- Themenrepo, Java-17-GRETL-Bundle und geprüfte INTERLIS-Modelle sind echte Bootstrap-Abhängigkeiten. Ein leerer, aber gültiger Portal-Veröffentlichungsstand genügt.
- Sodata lokal mit bestehendem JVM-Target bauen. Keine neue Portal-Authentifizierung oder Datenbankanbindung in dieser Etappe. Explore deaktivieren.
- Superset benötigt sowohl Metadaten- als auch ClickHouse-Treiber. Die Verbindung muss über den tatsächlich installierten Treiber getestet werden.
- JDBC-Zugang getrennt vom HTTP-Smoke prüfen. Keine DBeaver-UI-Prüfung behaupten, wenn sie nicht ausgeführt wurde.
- Ein anderer Compose-Projektname isoliert keine gemeinsam benutzten schreibbaren Hostpfade. Der Reviewlauf braucht eigene Runtimekonfiguration, Ports und Volumes.
- Persistenz, private Dateiablage und Negativtests werden an tatsächlich existierenden Testdaten geprüft. Netzwerk- oder Syntaxfehler sind kein Berechtigungsnachweis.

## Arbeitsweise

Arbeite innerhalb des vereinbarten Umfangs selbstständig und korrigiere gewöhnliche Build-/Startfehler. Führe keinen zusätzlichen fachlichen Freigabeprozess für deine Arbeit ein. Nutze kleine, überprüfbare Änderungen. Keine zusätzlichen Architekturprojekte oder umfassende Modernisierung der übernommenen Komponenten.

Verwende nur neue lokale Testressourcen. Verändere die ursprünglichen Datenportal-Repos und ihre laufenden Dienste nicht. Vermeide globale Docker-Bereinigungen, pauschales Löschen von Volumes und Remote-Pushes. Passwörter, API-Schlüssel, Tokens und vollständige interpolierte Env-Ausgaben gehören weder ins Protokoll noch ins Git.

Wenn ein konkreter Blocker besteht, benenne betroffene Anforderung, beobachteten Fehler und die minimale fehlende Voraussetzung. Erledige davon unabhängige Arbeiten weiter. Markiere nicht ausgeführte Pflichtprüfungen als offen. Keine erfundenen Testergebnisse.

## Handoff

Liefere am Ende:

- Eine kurze Erklärung, was jetzt läuft und welche lokalen URLs verwendet werden.
- Die beteiligten Zielrepos mit tatsächlichen Kandidatenständen.
- Den dokumentierten Start-, Stop-, Diagnose- und Testweg.
- Nachweise zu den selbst ausgeführten Prüfungen mit Exitcodes und Einschränkungen.
- Pfad und SHA256 des Kandidatenmanifests sowie den vorgesehenen unabhängigen Reviewaufruf oder GUI-Ablauf.

Du darfst ein Qwen-Review nur dann als ausgeführt bezeichnen, wenn eine separate Sitzung tatsächlich mit dem richtigen Infomaniak-Modell den Kandidaten geprüft hat. Falls du diese Sitzung selbst starten kannst, übergib den gemeinsamen Auftrag, `START_REVIEW.md` und das Manifest. Verwende nicht deine laufende Sitzung oder dein eigenes Modell als Ersatz. Übergib die konkreten absoluten Pfade zu Auftrag, Reviewprompt und Manifest sowie den vorgesehenen neuen Reviewordner.

Andernfalls liefere den fertigen Reviewkandidaten und den konkreten Handoff. Deine eigene erfolgreiche Prüfung bedeutet „implementiert und lokal geprüft, unabhängige Abnahme ausstehend“. Nach Reviewbefunden korrigierst du den Code, erzeugst einen neuen Kandidaten und lässt die betroffenen Kriterien erneut unabhängig prüfen. Das alte Kandidatenmanifest bleibt unverändert. Der Reviewer entscheidet anhand unveränderter Gegenstände und Abhängigkeiten, welche früheren Belege auf den neuen Kandidaten übertragbar sind; ungeklärte Nachweise werden wiederholt.



## Direkt verwendbarer Einstieg in der OpenCode-Oberfläche

```text
Arbeite als Implementierungsagent für die Grundinstallation. Lies zuerst AGENTS.md im gemeinsamen Arbeitsordner, dann die fünf Repo-AGENTS und dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/START_IMPLEMENTIERUNG.md sowie AUFTRAG_GRUNDINSTALLATION.md im selben Ordner vollständig. Führe den Auftrag aus und verwende die dort festgelegten Berichts- und Kandidatenpfade. Bewahre vorab abgelegte Auftrags- und AGENTS-Dateien beim Kopieren der Quellen.
```
