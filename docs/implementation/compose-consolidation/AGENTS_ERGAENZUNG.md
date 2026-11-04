# AGENTS-Ergänzung für MA-F

Vorhandene Workspace-/Repo-AGENTS erhalten und **gezielt** ergänzen. Keine blanket Überschreibung und kein weiterer Workspace-Gitbaum. Alte historische Reviewunterlagen nicht verändern.

Folgenden sinngemässen Block in die aktive Workspace-AGENTS und in STACK/AGENTS aufnehmen; betroffene ADMIN-/PUBLIC-AGENTS verweisen darauf:

```markdown
## Aktiver Folgeauftrag: Compose-Konsolidierung MA-F

Wenn der Sitzungsauftrag MA-F betrifft, lies vollständig:
- dateninfrastruktur-dev-stack/docs/implementation/compose-consolidation/EXECUTION_PLAN.md
- SPEC_MIGRATION.md und TEST_PLAN.md in diesem Ordner
- rollenbezogen CODEX_STARTPROMPT.md oder OPENCODE_REVIEW_PROMPT.md.

Codex implementiert, OpenCode 2.x mit DeepSeek Flash 1017 prüft autonom nach
jeder Teilphase. Keine Produktänderungen durch den Reviewer.

MA-F ersetzt nur die damaligen Betriebsentscheidungen für separate MA-Laufzeit,
zwei Instanzen und APISIX in Jenkins' Netzwerkraum. Der neue Normalbetrieb
verwendet eine compose.yaml, einen PG16/PostGIS-Server und je eine Instanz
aller Dauer-Services. Kein HA. Fachliche MA-A–E-Verträge bleiben gültig.

Die eindeutig inventarisierte eigene lokale Dateninfrastruktur darf nach
geprüfter Migration konsolidiert werden. Fremde Projekte/Volumes und
uncommittete Nutzerarbeit bleiben geschützt. Keine pauschale Volumelöschung.
Secrets nur programmatisch über private Pfade, niemals in Logs/Chat/Git.

Reviewer verwenden eigene Checkouts/Composeprojekte und keine Nutzersecrets.
Nur betroffene Tests nach Korrekturen wiederholen. Historische Reviews nicht
als Nachweis für veränderte Betriebspfade umdeuten.
```

Insbesondere alte Formulierungen „folge derselben Gateway-/Jenkins-Netzwerktopologie“, „alle Nutzerquellen bleiben unverändert“ oder „immer zwei Instanzen“ als auf den damaligen Auftrag beschränkt kennzeichnen. Nicht die Sicherheitsregeln für fremde Instanzen aufheben.

Die Workspace-Datei liegt ausserhalb eines Repos. Eine Kopie des **tatsächlich aktiven** Inhalts als `templates/AGENTS.workspace.current.md` im neuen Auftragsordner versionieren und im Reviewhandoff hashen. Keine unpassende starre Vorlage über lokale Nutzervorgaben legen. Alte Grundinstallations-/Managementkopien als historische Vorlage stehen lassen.
