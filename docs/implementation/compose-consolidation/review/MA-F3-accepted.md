# Unabhängiges Review MA-F3 – ein Betriebsweg, echter Recreate und gesicherter Retire/Rückfall

**Urteil: ABGENOMMEN**

Geprüft wurde der Kandidat `20261105T005356Z` der Phase MA-F3 auf dem exakten
Handoff-SHA-Satz. Alle drei Pflicht-IDs F14/F15/F16 wurden **selbst und frisch**
ausgeführt; der Handoff enthält keine `carried_checks`, es wurde kein Vorbeleg
übernommen und kein altes Urteil weitergetragen. Zusätzlich wurden die im Request
genannten Begleitprüfungen, ein statischer Topologie-/Legacy-Runtime-Check und eine
eigene, nicht vom Provider-Test vorgegebene Gegenprobe real ausgeführt. Die
Produktbäume blieben unverändert; die Nutzerdienste wurden nicht berührt.

## 1. Bindung

| Feld | Wert |
|---|---|
| Phase / Kandidat | `MA-F3` / `20261105T005356Z` |
| Handoff-SHA256 | `c023fd5e2a920a3ad91f9da010bad96e9d59a7f4645843f3bc868ac693ac7182` |
| Spezifikations-SHA256 | `8adb97576d55fe4cf269e3d17d4dd156efb971e957ea1f44bbcb85505e9f3e67` |
| Request-SHA256 | `d6404b2c581f2f866f6b6c8cfcb9e15a2b0e8d2d57184c91fd25ac60ddc268cf` |
| Workspace-AGENTS-SHA256 | `21df33d38618ccd414f082c901f08b457adbd07551620f49e5455565d2c8ee4e` |
| Modell / CLI / Session | `deepseek/deepseek-flash` / `opencode v2.2.5` / `ses_e56cd3ebeffeiIhIqHtwM6pu6V` |

Selbst nachgerechnet: Handoff-, Request-, Spec-Datei- und Workspace-AGENTS-Hashes
stimmen; der aggregierte Spezifikationshash reproduziert sich als
`sha256(json.dumps(files_sha256, sort_keys=True))` = `8adb97…f3e67`. Der laufende
Runner ist die Desktop-CLI
`…/ai.opencode.desktop/cli/2.2.5-arm64/opencode-cli run --standalone --agent
management-review --model deepseek/deepseek-flash`; das unabhängig im PATH
liegende `opencode` 1.18.22 ist **nicht** die Runner-CLI. Die Session-ID stammt aus
dem Ereignisstrom dieses Laufs (`events.jsonl`), der auch die tatsächliche
Read-/Shell-Ausführung belegt. Der Gate-Selbsttest mit den Transportdaten ist in
`output/runner_selftest.json` festgehalten; das endgültige Runner-Artefakt liefert
die Orchestrierung.

Repositories (exakt aus dem Handoff, vor und nach dem Review erneut geprüft; alle
Bäume clean):

| Repository | Base | HEAD | Änderung |
|---|---|---|---|
| dateninfrastruktur-dev-stack | `1473754349…1b856` | `59fd0545dcb198fb5b483a8fd8440da16db5d8f1` | 1 Commit |
| dateninfrastruktur-admin | `14374ecd58…95d80` | `02eaa8a450c7e9d88bad6a01132f67bc98a37489` | 1 Commit |
| dateninfrastruktur-sodata | `b1f20075be…0e1801` | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` | unverändert |
| dateninfrastruktur-jenkins-dev | `08931fa825…f087d` | `08931fa8254d096e2addcd3aee97bc1b753f087d` | unverändert |
| dateninfrastruktur-jenkins-gretl-plugin | `579f3fd544…5322f` | `579f3fd54432a977122afb186469fbb40d95322f` | unverändert |
| dateninfrastruktur-themenrepo | `303b2f0be7…b040` | `6b0b635f066dc8de5000e3e549b983fb772dfb33` | 1 Commit |

Alle Base-SHAs sind Vorfahren der HEADs; die drei unveränderten Repos haben
`base == head`.

## 2. Gelesener Umfang

Vollständig gelesen: `EXECUTION_PLAN.md`, `SPEC_MIGRATION.md`, `TEST_PLAN.md`,
`OPENCODE_REVIEW_PROMPT.md`, `AGENTS_ERGAENZUNG.md`, `F3_IMPLEMENTATION.md`,
`MA-F3-request.md`, `WORK_QUEUE.md`, Workspace-AGENTS und die AGENTS der
betroffenen Repos sowie `docs/operations.md` und `docs/migration-ma-f.md`.

Gelesene Diffs (vollständig, nicht nur Statistik):

- STACK `1473754..59fd054` (54 Dateien, +1215/−2310): `compose.yaml`,
  `compose_operations.py`, `compose_runtime.py`, `compose_operator.py`,
  `consolidation.py`, `migration_lifecycle.py`, `migration_retirement.py`,
  `migration_coordinator.py`, `migration_prepare.py`, `migration_binding.py`,
  `services/migration/storage.py`, Root-/Management-Wrapper, `bootstrap.py`,
  `smoke_compose.py`, `test_consolidation_f3.py`, retired Grundinstallationsskripte.
- ADMIN `14374ec..02eaa8a` (23 Dateien, +126/−1095): `managed_runtime.py`,
  `identity_runtime.py`, `run.py`, `setup.py`, `managed_setup.py`,
  `management_db.py`, `compatibility.py`, `managed_control.py`, `managed_pilot.py`,
  `legacy_import.py`, retired Python-Testharnesses, README/Doku.
- TOPICS `303b2f0..6b0b635`: `datenportal-publication.gradle` (Taskgraph-Guard)
  und README.

Kein Diff an Modellen, SQL-Migrationen, Mapping/Audit-Kern, Sodata, Jenkins-Dev
oder GRETL-Plugin. Kein Diff an einem ClickHouse-Lader; die einzige
publikationsnahe Änderung ist die Ablehnung im Gradle-Vertrag.

## 3. Selbst ausgeführte Pflichtprüfungen

Ausgangspunkt war der dokumentierte Hauptlauf aus dem Request. Er baut eigene
nichtleere F2-Quellfixtures (Foundation und Management), verwendet denselben
produktiven Cutover und dieselben öffentlichen Wrapper, führt echte
Stop/Start- und `down`/`up`-Runden ohne `-v` aus, retired die exakten Quellen und
rekonstruiert sie aus den geprüften Archiven.

| ID | Ausführung | Kommando / CWD | Exit | Beobachtung | Beleg |
|---|---|---|---|---|---|
| F14 | `EXECUTED` | `./scripts/test-consolidation.sh --phase MA-F3` in `…/workspace/dateninfrastruktur-dev-stack` | 0/0 | Root- und Managementwrapper liefen mit identischem explizitem Kontext. Falsche `INSTANCE_ID` (`stop.sh`) und geänderte `POSTGRES_VOLUME` (`up.sh`) ergaben `OWNERSHIP_MISMATCH` **vor** Mutation. `setup.sh` verifizierte den Bestand rein lesend (identischer Snapshot und ENV-Digest). Echter Gradle-Lauf im Jenkins-Container: DB-Katalogmodus + `s3Publish=true` scheiterte vor jeder Taskaktion mit der dokumentierten Meldung und ohne `> Task`; `s3Publish=false` lieferte `reloadPortal SKIPPED`. | `output/F14_F15_F16-main.stdout.log` |
| F15 | `EXECUTED` | dieselbe Hauptprobe | 0/0 | Stop/Start über den Managementwrapper und anschliessend echtes `down`/`up` ohne `-v`. Alle zehn Service-Container-IDs waren danach tatsächlich neu. Tabellen-/Audit-/Sequenz-/ACL-/Trigger-/Extension-Snapshot und ENV-Secretdigest blieben identisch; reale Keycloak-Logins, wirksamer Widerruf (403), Datei-Hashes, Jenkinsmarker und die verschlüsselte Superset→ClickHouse-Verbindung blieben erhalten. Keine Defaultseeds, keine zusätzlichen Dauercontainer. | `output/F14_F15_F16-main.stdout.log` |
| F16 | `EXECUTED` | dieselbe Hauptprobe | 0/0 | Erweiterte Retire-Allowlist → `OWNERSHIP_MISMATCH`; nachträglich verändertes Sicherungsmanifest → `BACKUP_FAILED`, jeweils vor jeder Entfernung. Danach wurden genau die geplanten, gestoppten Quellen ohne `-v` entfernt; doppeltes Retire war idempotent; alle Originalvolumes blieben per `inspect` identisch. Der Rückfall rekonstruierte aus Dateisystemexporten, Bind-/Konfigurationsarchiven und ursprünglichen (auch dynamischen) Ports die aktuelle H2-Person (`Anna MA current profile`) und den erst nach Quellstart geschriebenen Namespace-Childzustand; das Ziel blieb gestoppt. | `output/F14_F15_F16-main.stdout.log` |

Laufzeit des Hauptlaufs: `2026-11-05T00:55:29Z` → `2026-11-05T01:06:08Z`,
Exit 0, **stderr leer**. Belegzeilen: `PASS F14 legacy adapter …`,
`PASS F14/F15: …`, `PASS F16: …`, `PASS MA-F3 F14–F16`.

### 3.1 Zusätzlich selbst ausgeführte Begleitprüfungen

| Prüfung | Kommando / CWD | Exit | Beobachtung | Beleg |
|---|---|---|---|---|
| Lifecycle-Guards | `python3 scripts/test_compose_lifecycle_safety.py` in `…/dateninfrastruktur-dev-stack` | 0/0 | 3 Tests OK: Recovery-/Rollback-Sperre und fehlendes Setup blockieren vor `resolve`/Build/Docker; dynamischer Port und `$`-Literale bleiben erhalten; Namespace-Child ohne unzulässigen Hostnamen; `ROLLBACK_UNSAFE` vor Stop, gültiger Rückfall blockiert zuerst. | `output/test_compose_lifecycle_safety.stderr.log` |
| Migrationssicherheit | `python3 scripts/test_migration_safety.py` | 0/0 | 4 Tests OK: Namespace-Reihenfolge, fremder Parent/Zyklus abgewiesen, ENV-/Render-Drift vor Docker, Compose-nativer Secret-Codec. | `output/test_migration_safety.stderr.log` |
| Review-Gate | `DI_GATE_TEST_PHASE=MA-F3 python3 scripts/management/test_review_gate.py` | 0/0 | 1 Test OK: falscher SHA/Report, fehlende/duplizierte IDs, falsches Modell, unausgeführte Gegenprobe und ungebundene Übernahme schliessen das Gate. | `output/test_review_gate.stderr.log` |
| Statische Topologie | eigener Read-only-Check `output/static_topology_and_no_legacy_runtime.log` | 0/0 | Genau zehn Dienste ohne Profile; kein `container_name`, kein `network_mode` bei Dauer-Services, kein Host-JAR-Mount; keine `docker run/create`- oder `managed_runtime`/`identity_runtime`-Aufrufe in den aktiven STACK-Skripten; ADMIN-Launcher delegieren nachweislich an STACK. | `output/static_topology_and_no_legacy_runtime.log` |

## 4. Eigene Gegenprobe

**Hypothese.** Ein Retire-/Quiesce-Plan, der eine nach der Planaufnahme unter
gleichem Compose-Servicenamen **neu erzeugte** Quelle noch mit der alten
Container-ID nennt, wird vor dem ersten Stop verweigert und lässt die
Ersatzressource unberührt. Eine Retire-Allowlist, die eine geplante Quelle still
auslässt, wird ohne jede Containerentfernung abgewiesen.

**Warum diese Probe.** Der Provider-Test deckt nur eine *erweiterte* Allowlist und
ein verändertes Manifest ab. Die Vertragsklausel „inzwischen andere Ressourcen“
und die Reihenfolge „vollständige Auswahl prüfen, dann erst stoppen“ werden dort
nicht direkt adressiert.

**Ausführung.** `python3 output/counterexample_retire_stale_source.py` in
`…/workspace/dateninfrastruktur-dev-stack`, eigenes Projekt
`maf-f3-counter-*` mit der kanonischen `compose.yaml` (nur
`migration-fixture`-Profil, keine Anwendungstopologie).

**Erwartung.** Exit 0 mit sechs PASS: veraltete Auswahl abgewiesen, keine Quelle
gestoppt, aktuelle Auswahl funktioniert, Teilmengen-Allowlist abgewiesen, nichts
entfernt, Cleanup erfolgt.

**Beobachtung.** Exit 0, **6 passed / 0 failed**: Die alte Child-ID
(`d78a052d775c`) wurde durch eine neue (`adf5e349351a`) ersetzt; der veraltete Plan
scheiterte vor jedem Stop, Parent und Ersatz-Child liefen weiter. Ein Plan mit der
aktuellen ID stoppte beide. Die Teilmengen-Allowlist ergab `OWNERSHIP_MISMATCH`,
beide Container blieben vorhanden. Das eigene Projekt wurde vollständig entfernt.

Beleg: `output/counterexample_retire_stale_source.stdout.log` (stderr leer).

## 5. Findings

**Keine BLOCKER/MAJOR/MINOR-Findings.** Die geprüften F14–F16-Verträge sind
erfüllt; der Code setzt die Ablösung der alten Orchestrierung konsistent um.

Nicht blockierende Beobachtungen (keine Anforderungsverletzung, nicht reparieren):

- `stop.sh` vergleicht die gespeicherte Volumenzuordnung nicht; nur `setup`, `up`
  und `restart` tun das. Ein Stop ist nicht destruktiv, und der anschliessende
  Start wird vor jedem Build/Containerwechsel belegt abgewiesen. Die
  F14-Kernforderung „geänderte Zuordnung blockiert vor Neuerstellung“ ist erfüllt.
- `logs --follow` startet den Compose-Prozess direkt und ruft `verify_project`
  nicht auf. Es findet keine Mutation statt; die Bindung bleibt dieselbe.

## 6. Integrität und Grenzen

- Produktbäume: exakt die Handoff-HEADs, `git status --porcelain` vor und nach dem
  Review leer. Der Vergleich aller getrackten Dateien gegen `before.json` ist
  identisch (`output/after_integrity.json`, Zwischenstand ebenfalls clean).
- Keine Änderung an Produktcode, Tests, Spezifikationen, AGENTS oder
  Konfiguration; keine Reparatur, keine Commits.
- Laufzeit: ausschliesslich eigene `maf-f3-*`- und `maf-f3-counter-*`-Projekte mit
  zufälligen Ports, eigenen Volumes und synthetischen Testcredentials. Das lokale
  Jenkinsimage wurde nur über seine Image-ID gelesen. Keine Nutzer-`.env`, keine
  Dumps, keine Nutzersecrets.
- Nutzerdienste: die 20 Container `dateninfrastruktur-dev-stack-*` und `di-ma-*`
  sind vor/nach identisch (IDs und Status; `output/user_services_before.txt` vs.
  `user_services_after.txt`).
- Nach dem Lauf keine eigenen `maf-f3`-Container, -Volumes oder -Netze
  zurückgeblieben.
- Keine Secretwerte in Bericht oder Belegen. Der reale lokale Cutover ist
  weiterhin nicht ausgeführt und bleibt `LOCAL_CUTOVER_PENDING` (F4/Operator),
  nicht Teil dieser Codeabnahme.

## 7. Ergebnis

F14, F15 und F16 sind am Kandidaten real ausgeführt und bestanden; die
Begleitprüfungen und die eigene Gegenprobe bestätigen Scope-, Recreate- und
Retire-/Rückfallgrenzen. Produktbestand unverändert, keine offenen Pflichtläufe,
keine blockierenden Findings.

**ABGENOMMEN** für MA-F3 am SHA-Satz
`59fd0545dcb198fb5b483a8fd8440da16db5d8f1` (STACK),
`02eaa8a450c7e9d88bad6a01132f67bc98a37489` (ADMIN),
`6b0b635f066dc8de5000e3e549b983fb772dfb33` (TOPICS) und den drei unveränderten
Geschwister-HEADs. Der lokale Cutover bleibt separat `LOCAL_CUTOVER_PENDING`.
