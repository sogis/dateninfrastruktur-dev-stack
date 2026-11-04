# AGENTS.md – Dateninfrastruktur-Arbeitsbereich

## 1. Geltung und Projektstruktur

Dieser Ordner ist der **gemeinsame Arbeitsbereich** und Einstiegspunkt für **Codex**. Er ist **kein eigenes Git-Repository**. Gitoperationen werden stets im jeweiligen Unterrepository ausgeführt (`git -C <repo> ...`); niemals ein Git-Repository im Mutterordner initialisieren oder fremde Änderungen gesammelt committen.

Zum Arbeitsbereich gehören die bestehenden, eigenständigen Produktrepositories:

- `dateninfrastruktur-dev-stack`
- `dateninfrastruktur-sodata`
- `dateninfrastruktur-jenkins-dev`
- `dateninfrastruktur-jenkins-gretl-plugin`
- `dateninfrastruktur-themenrepo`

**`dateninfrastruktur-admin`** ist das bereits vorhandene sechste Geschwisterrepository. Prüfe vor einer Neuerstellung, ob es lokal bereits existiert und ob ein Remote konfiguriert ist; weder überschreiben noch ein zweites Repository anlegen.

Ältere `datenportal-*`-Repositories sind allenfalls **lesende Quellen**, keine Produktziele dieses Auftrags. Andere im Mutterordner enthaltene Projekte werden nicht ungefragt geändert.

## 2. Aktueller Auftrag und Quellenhierarchie

**Aktiver Folgeauftrag:** Compose-Konsolidierung **MA-F0 bis MA-F4**. Die abgenommenen MA-0–E-Verträge bleiben fachlich gültig; deren separate Zwei-Instanzen-Laufzeit ist historisch, kein Betriebsziel.

Verbindlicher Einstieg:

1. `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/EXECUTION_PLAN.md`
2. `.../SPEC_MIGRATION.md`
3. `.../TEST_PLAN.md`
4. Rollenbezogen `.../CODEX_STARTPROMPT.md` **oder** `.../OPENCODE_REVIEW_PROMPT.md`
5. `.../AGENTS_ERGAENZUNG.md` sowie die jeweiligen `AGENTS.md` der betroffenen Repositories.

Die `...` in den Punkten 2–5 stehen ausschliesslich für das zuvor vollständig ausgeschriebene Verzeichnis `dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/`.

Ein normaler Start in Codex setzt **nicht** automatisch einen Auftrag in Gang: der konkrete Benutzer-/Startprompt aktiviert die Durchführung. Die obigen Dateien sind der vereinbarte Vertrag für diesen Auftrag. Bei echtem Widerspruch **vor** produktiven Änderungen die spezifischen Anforderungen prüfen, nicht still abschwächen.

Die Dokumente unter `docs/implementation/grundinstallation/` und `docs/implementation/schritt-2-datenladen/` bleiben **historisch beziehungsweise für ihre eigenständigen Aufträge** erhalten. Ihre ehemaligen Umfangsausschlüsse (z. B. «kein SSO», «kein Freigabeprozess», «nur Grundinstallation»), G01–G24-Gates und Ablagepfade gelten **nicht als globale Beschränkungen** für MA-F. Die laufende ClickHouse-Ladeimplementierung nicht zurücksetzen, umbenennen oder ungefragt wiederholen. Falls eine Repository-`AGENTS.md` die alten Grenzen als allgemeingültig darstellt, aktualisiere sie im Rahmen von MA-F0 **gezielt**, ohne alte Dokumente umzuschreiben.

## 3. Rollen und Review – nicht verwechseln

- **Codex** ist der alleinige Implementierungsagent für diesen Auftrag. Er darf innerhalb des vereinbarten Scopes Produktcode, Modelle, Migrationen, Tests und Dokumentation ändern und lokale Commits je Repository erstellen.
- **OpenCode 2.x mit DeepSeek Flash 1017 über die vorhandene DeepSeek-API-Konfiguration** ist der **unabhängige Reviewer**. Codex startet nach **jeder** Phase autonom eine neue OpenCode-Sitzung an einem genau festgelegten, isolierten Multi-Repo-Kandidaten. Kein manueller Wechsel des Benutzers zwischen Implementierung und Review als Normalfall.
- Der Reviewer liest Implementierung und Anforderungen, führt **selbst** geeignete Tests sowie eine eigene Gegenprobe aus und prüft Code **und** Zielerreichung. Er ändert **keine** Produktdateien, Testverträge, Prompts oder Anforderungen und erstellt keine Produktcommits.
- Nur `ABGENOMMEN` am aktuellen Quell-SHA-Satz mit überprüfbarem Test-/Modellnachweis öffnet die nächste Phase. Bei `NACHARBEIT` korrigiert **Codex**, committed neue Änderungen und startet ein erneutes unabhängiges Review. Bei echter Undurchführbarkeit `NICHT_PRUEFBAR`, kein erfundenes PASS.
- **Risikobasiert testen:** Nach Korrekturen nur den reproduzierenden Fall, wahrscheinlich betroffene Verträge und die kleinste sinnvolle Regression erneut prüfen. Erfolgreiche unveränderte Nachweise dürfen mit begründeter Gültigkeit übernommen werden; Änderungen an Authentisierung, Autorisierung, Datenbankschema, Transaktionen oder Gateway brauchen entsprechend breitere gezielte Prüfungen.

## 4. Sicherheit und Arbeitsbereichsgrenzen

- Lokalen Ist-Zustand, Git-HEADs, Dirty Trees, Remotes, vorhandene Ports/Volumes und Benutzerarbeit feststellen. Bestehende Änderungen und Secrets erhalten. Kein `rsync --delete`, kein ungezieltes `docker system prune`, kein `down -v` der Nutzerinstanz und keine globale Docker-/Dateisystembereinigung.
- Kein Remote-Push, Merge, Release oder produktiver S3-Write, sofern nicht separat ausdrücklich beauftragt. Keine fremden externen Reloads/Produktionsänderungen.
- Review: eigenständige Checkouts/Worktrees und getrennte Laufzeitressourcen mit **isolierten Ports, Volumes, schreibbaren Hostpfaden und Testcredentials**. Nur für die Phase benötigte Dienste starten. Keine Original-`.env` oder Geheimnisse in Review-Handoffs, Logs, Git oder Modellkontext kopieren.
- Die Workspace-`AGENTS.md` liegt ausserhalb der Git-Repositories. Für jedes Review ihren **Inhalt/Hash als expliziten, unveränderlichen Bestandteil des Handoffs** erfassen und im isolierten Reviewarbeitsbereich bereitstellen. Sie ist allein kein technischer Schreibschutz.
- Produktive Dateizugriffe und Berechtigungsentscheidungen niemals aus einem gecachten Benutzerrecht ableiten. Für die Management-/Access-Etappe gilt der vollständige Sicherheitsvertrag der SPEC-Dateien.

## 5. Ablage, Phasen und Bericht

Aktiver Planungs- und Berichtsordner:

`dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/`

Eine `WORK_QUEUE.md` führt die Phasen. Requests und bereinigte Abnahmen liegen im dort vorgesehenen `review/`-Bereich; konkrete Kandidatenhände, Handoffs, Rohlogs und Testressourcen in ignorierten `.runtime/compose-review/`-Verzeichnissen. Historische Grundinstallationsberichte und bereits bestehende Ladebelege niemals rückwirkend überschreiben.

Die Modelle müssen aus INTERLIS durch **ili2pg** nach PostgreSQL gelangen; die neue Admin-Anwendung verwendet **Apache Cayenne**, nicht Hibernate. Sodata liest die freigegebene DB-Katalogsicht. APISIX benutzt `forward-auth` zur Java-Authorization-API, **kein** eigenes Lua-Plugin, kein direkter APISIX→PostgreSQL-Zugriff und keine generierten Casbin-Dateien. Fachliche Berechtigungen gelten für den ganzen logischen Datensatz.

## 6. Pflege dieser Datei

Diese Datei ist die **workspaceweite Arbeitsregel**, nicht die vollständige Fachspezifikation. Bei neuen, ausdrücklich beauftragten Etappen nur die Abschnitte zum aktuellen Auftrag und Einstieg aktualisieren; allgemeine Sicherheits- und Multi-Repo-Regeln behalten. Historische Arbeitsanweisungen bleiben in ihren Dokumentationsordnern bestehen, sind aber nicht gleichzeitig aktive globale Aufträge. Globale Codex-/OpenCode-Accounts, Berechtigungen und Providerkonfigurationen nicht ungefragt verändern.

## Aktiver Folgeauftrag: Compose-Konsolidierung MA-F

MA-F verwendet eine kanonische compose.yaml, einen PG16/PostGIS-Server für
Keycloak/Superset/Management und genau eine Instanz je Dauer-Service. Kein HA.
Die frühere APISIX/Jenkins-Netzwerkraumkopplung und separate MA-Orchestrierung
werden kontrolliert abgelöst; Modelle, Audit und aktuelle Autorisierung bleiben.

Die eindeutig inventarisierte eigene lokale Dateninfrastruktur darf nach
geprüfter Migration konsolidiert werden. Fremde Projekte und uncommittete
Nutzerarbeit bleiben geschützt. Keine pauschale Volumelöschung. Vor Retire auch
Schreibschichtdaten sichern; Secrets ausschliesslich programmatisch/private Pfade.
Reviewer verwenden isolierte Composeprojekte, keine Nutzersecrets/-dumps.
Nur betroffene Verträge nach Korrekturen neu prüfen. Historische Belege erhalten.
Die tatsächliche aktive Workspace-Datei wird für Reviews in
compose-consolidation/templates/AGENTS.workspace.current.md versioniert/gehasht.
