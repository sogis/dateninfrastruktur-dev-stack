# Workspace-/Repo-Anweisungen für MA-G

Codex öffnet weiterhin den **gemeinsamen Mutterordner**. Dort liegt eine übergreifende `AGENTS.md`; jedes der sechs Repos kann ergänzen. Keine neue übergeordnete `.git`, keine ungefilterte Ersetzung der vorhandenen Anweisungen. Eigene Nutzervorgaben erhalten.

## Gezielter aktiver Block

Folgenden sinngemässen Block in die Workspace-AGENTS und STACK-AGENTS integrieren; ADMIN/PUBLIC/PLUGIN/JENKINS/TOPICS verweisen darauf:

```markdown
## Aktueller Auftrag MA-G: Storage und CSV-Anlieferung

Bei einem MA-G-Sitzungsauftrag lies vollständig:
dateninfrastruktur-dev-stack/docs/implementation/storage-and-delivery/README.md,
EXECUTION_PLAN.md, sämtliche SPEC-Dateien, TEST_PLAN.md und den rollenbezogenen
CODEX_STARTPROMPT.md oder OPENCODE_REVIEW_PROMPT.md.

Codex implementiert MA-G0..MA-G5. OpenCode 2.x mit DeepSeek Flash 1017 prüft
nach jeder Phase autonom unabhängig. Reviewer reparieren keine Produktdateien.
Nach Korrekturen werden nur betroffene Verträge und sinnvolle Regressionen neu
geprüft. Kein Gate ohne echten unabhängigen Test- und Codebeleg.

MA-G ersetzt alte Storage-/Publikations-/Teams-/Organisationsjobverträge.
API-Breaks sind erlaubt und Kompatibilitätscode ist ausdrücklich nicht gewünscht.
Ein privater Bucket ch.so.daten; ein generischer CSVjob; Fachrechte in PostgreSQL.
Ein Compose-Projekt mit einem PG16/PostGIS und je einer Instanz aller Dienste.
Kein HA, keine Backupautomatisierung, kein CI-Neubau, kein Spezialjobframework.

Der bisherige Inhalt des eindeutig identifizierten lokalen Entwicklungsbuckets
ch.so.daten darf nach geprüfter Vorbereitung einmalig gelöscht werden.
Referenzierte private Dateien, Fachrechte, Identitäten und Auditdaten bleiben
zu erhalten. Keine produktiven oder fremden S3-Instanzen/Volumes verändern.
Keine ungezielte Löschung von Jenkinsjobs, Nutzerarbeit oder Dockerressourcen.

Technische Personenrechte/Teams nicht mehr in YAML oder Jenkins-Jobs spiegeln.
Das Plugin fragt die Admin-API. Upload-/Jobparameter sind keine Autorisierung.
Normalstart enthält weder Purge, automatische Migration noch fachliche Seeds.
```

Alte Formulierungen „Plugin unverändert lassen“, „Legacy-Publisher/Manifest erhalten“, „nur fünf Zielrepos“ und alte Betriebspfade auf ihren damaligen Auftrag begrenzen. Bestehende Sicherheitsregeln für Fremdressourcen **nicht** aufheben.

Die **tatsächlich aktive** Workspace-AGENTS wird nach der gezielten Bearbeitung als `templates/AGENTS.workspace.current.md` im neuen Auftragsordner versioniert und im Handoff gehasht. Diese Datei nicht durch eine fiktive Vorlage ersetzen. Historische Review-AGENTS/Hashes bleiben unverändert.

Der Reviewer darf dieselben Anweisungen lesen, erhält daraus aber keine Implementierungsrechte. Das konkrete Rollenkapitel und der Sitzungsauftrag begrenzen seine Aktionen.
