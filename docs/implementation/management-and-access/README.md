# Management und Access – Gesamtauftrag für Codex

**Stand 4. November 2026.** Dieses Paket enthält Spezifikation und Arbeitsanweisungen, keine bereits implementierte Anwendung.

## Ziel

Neue INTERLIS-Modelle → PostgreSQL via ili2pg → Cayenne-Admin mit Audit → Sodata aus DB → tatsächlich geschützte Dateidownloads über APISIX forward-auth.

Berechtigungen gelten für den ganzen fachlichen Dataset. Neue Downloadchecks lesen den aktuellen PostgreSQL-Stand; Dateien werden von einem internen Origin aus S3 geliefert. Keine Casbin-Dateisynchronisation und kein eigenes Lua-Plugin.

## Dateien

| Datei | Zweck |
|---|---|
| [EXECUTION_PLAN.md](EXECUTION_PLAN.md) | Gesamtumfang, Versionen, Repos, Phasen, Gates |
| [SPEC_MODELS.md](SPEC_MODELS.md) | Fachklassen, Felder, Beziehungen, Constraints und Migration |
| [SPEC_PERSISTENCE_AUDIT.md](SPEC_PERSISTENCE_AUDIT.md) | Schema, Cayenne, Transaktionen, generisches Audit und externer Installer |
| [SPEC_APPLICATIONS_GATEWAY.md](SPEC_APPLICATIONS_GATEWAY.md) | Services/Methoden, UI-/HTTP-/OIDC-/Gateway-/Dateiverträge |
| [TEST_PLAN.md](TEST_PLAN.md) | gezielte Phasenprüfungen M00–M33 und Delta-Testregeln |
| [CODEX_STARTPROMPT.md](CODEX_STARTPROMPT.md) | Implementierung und autonome Reviews |
| [OPENCODE_REVIEW_PROMPT.md](OPENCODE_REVIEW_PROMPT.md) | unabhängiger zweiter Agent: Code und Zielerreichung |
| [AGENTS.workspace.md](AGENTS.workspace.md) | geprüfte Vorlage für die `AGENTS.md` im gemeinsamen Elternordner; einmalig übernehmen |
| [AGENTS_ERGAENZUNG.md](AGENTS_ERGAENZUNG.md) | Hinweise zur Workspace-Umstellung und zu den Repo-AGENTS |
| [SOURCES.md](SOURCES.md) | geprüfte Quellen und Grenzen |
| [templates/handoff.example.json](templates/handoff.example.json) | nach dem Commit erzeugter konkreter Kandidat |
| [templates/review-result.example.json](templates/review-result.example.json) | maschinenlesbares Urteil, kein vorbereiteter PASS |
| [templates/PHASENREQUEST.template.md](templates/PHASENREQUEST.template.md) | kurzer Reviewrequest vor dem Commit |

Die SPEC-Dateien sind verbindliche Detailkapitel **derselben** Spezifikation, keine separat zu beauftragenden Projekte. Codex bekommt das Gesamtpaket und arbeitet phasenweise.

## Ablage

Den Paketordner `dateninfrastruktur-dev-stack/docs/implementation/management-and-access/` mit dem bestehenden Repo zusammenführen. Grundinstallation und `schritt-2-datenladen` erhalten. Nicht alle Dateien ins Repo-Root legen; Root-README und Repo-AGENTS nicht blind überschreiben. Die **Workspace-`AGENTS.md` im Elternordner** sollte jedoch vor dem Start durch die aktualisierte Vorlage `AGENTS.workspace.md` ersetzt bzw. mit ihr sorgfältig zusammengeführt werden (vorher sichern).

**Wichtig:** Die bisherige Workspace-`AGENTS.md` zwingt Agenten noch zum Grundinstallationsauftrag und dessen Ausschlüssen. Ohne diese einmalige Anpassung können Codex und Reviewer widersprüchliche Anweisungen erhalten.

Repos als Geschwister:

```text
workspace/
  dateninfrastruktur-dev-stack/
  dateninfrastruktur-admin/          # neu / bei Bedarf initialisieren
  dateninfrastruktur-sodata/
  dateninfrastruktur-themenrepo/
  dateninfrastruktur-jenkins-dev/
  dateninfrastruktur-jenkins-gretl-plugin/
```

Die drei letzten Repos nur ändern, wenn der konkrete Anschluss es erfordert. Kein neues Workspace-Git-Repo anlegen. Arbeitsbereich in Codex ist der gemeinsame Elternordner.

## Startprompt

```text
Implementiere die Management-/Access-Etappe unserer Dateninfrastruktur.

Lies Workspace-/Repo-AGENTS und vollständig:
dateninfrastruktur-dev-stack/docs/implementation/management-and-access/CODEX_STARTPROMPT.md
dateninfrastruktur-dev-stack/docs/implementation/management-and-access/EXECUTION_PLAN.md
sowie alle darin referenzierten SPEC-Dateien, TEST_PLAN und Reviewprompt.

Beginne mit MA-0, dann MA-A bis MA-E. Nach jeder Phase gezielt testen,
lokal committen und autonom einen frischen OpenCode-2.x-Review mit DeepSeek
Flash 1017 über meinen vorhandenen DeepSeek-Zugang starten. Erst unabhängiges
ABGENOMMEN am aktuellen Kandidaten erlaubt die nächste Phase.

Verwende Cayenne5.0-M3 und die offiziell aktuelle stabile Spring-Boot-Version
(bei Spezifikationserstellung4.1.2), mit echtem frühem Kompatibilitätsnachweis.
Nach Fehlerkorrekturen nur betroffene Verträge und sinnvolle Regressionen
neu testen. Bestehende Nutzerarbeit, Repos, Volumes und Secrets erhalten.
Liefere funktionierenden Code, nicht nur einen weiteren Plan.
```

## Abnahme und Grenzen

MA-0 → MA-A → MA-B → MA-C → MA-D → MA-E. Jeder Übergang ist blockierend unabhängig abgenommen. MA-E umfasst die abschliessende echte Benutzerkette. Kein manuelles Wechseln zwischen Implementierungs-/Reviewmodell als normaler Ablauf.

Die JSON-Dateien sind Vorlagen mit `example_only=true`; sie belegen nichts. Tatsächliche Handoffs nach Produktcommit unter ignorierter `.runtime/management-review/` erzeugen. Spec-/Requesthashes und vollständige Repo-SHAs binden. Kein Commit enthält seinen eigenen SHA.

Technische Revisionsnachvollziehbarkeit ist Teil des Auftrags, keine rechtliche Compliancezertifizierung. Vollständige historische DBrekonstruktion, ClickHouse-Personenrechte, Superset-ACL/SSO, Agentic BI und produktiver OpenShiftbetrieb bleiben ausserhalb dieser Etappe.
