# Unabhängiges Delta-Review MA-F2 – Garage-Secretpfad (F2-MAJOR-1)

**Urteil: ABGENOMMEN**

Geprüft wurde der gezielte Korrekturstand zum vorherigen MA-F2-Review
`20261104T232247Z`. Der frühere Phasenentscheid war `NACHARBEIT`; übernommen
werden ausschliesslich die dort tatsächlich ausgeführten, unveränderten
F09/F10/F12-Beobachtungen, nicht das alte Urteil. F11/F13 wurden am neuen
Kandidaten frisch ausgeführt. Eigene Gegenprobe bestanden, Produktbäume
unverändert.

## 1. Bindung

| Feld | Wert |
|---|---|
| Phase / Kandidat | `MA-F2` / `20261104T234324Z` |
| Handoff-SHA256 | `3a28389bd04277a18aad8c59207ae8ebc6cd206fa2b9945f02aef4b3e262fa5e` |
| Spezifikations-SHA256 | `1b5296fee74501d0a402a602f5de47f4d570505e728456790924a6ef14b1860c` |
| Request-SHA256 | `ee3575e8cf120a2216a794a503e3498b902e51be73d90347d8278428eb983e2d` |
| Workspace-AGENTS-SHA256 | `21df33d38618ccd414f082c901f08b457adbd07551620f49e5455565d2c8ee4e` |
| Modell / CLI / Session | `deepseek/deepseek-flash` / `opencode v2.2.5` / `ses_e570dd094ffeZBqM2Hl5T2PFaB` |

Alle Angaben wurden selbst nachgerechnet: Handoff-, Request-, Spec-Datei- und
Workspace-AGENTS-Hashes stimmen; der aggregierte Spezifikationshash ergibt
`1b5296...1860c`. Der Runner verwendet die Desktop-CLI
`.../cli/2.2.5-arm64/opencode-cli` (`opencode v2.2.5`); das unabhängig im PATH
liegende `opencode` 1.18.22 ist nicht die Runner-CLI.

Repositories (exakt aus dem Handoff, vor und nach dem Review geprüft):

| Repository | HEAD |
|---|---|
| dateninfrastruktur-dev-stack | `49273ffd848b8fe6ac30d28d67b99a18333000dc` |
| dateninfrastruktur-admin | `14374ecd58f2ad27432ec7fe0fd4535021795d80` |
| dateninfrastruktur-sodata | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` |
| dateninfrastruktur-jenkins-dev | `08931fa8254d096e2addcd3aee97bc1b753f087d` |
| dateninfrastruktur-jenkins-gretl-plugin | `579f3fd54432a977122afb186469fbb40d95322f` |
| dateninfrastruktur-themenrepo | `303b2f0be785dc5b06882612f9b8bfcd8c17b040` |

Alle Base-SHAs sind Vorfahren der jeweiligen HEADs; nur STACK enthält einen
Commit (`6673b67..49273ff`). Die übrigen fünf Repos sind unverändert
(`base == head`).

## 2. Gelesener Umfang und Diff

Vollständig gelesen: `EXECUTION_PLAN.md`, `SPEC_MIGRATION.md`, `TEST_PLAN.md`,
`OPENCODE_REVIEW_PROMPT.md`, `F2_IMPLEMENTATION.md`, `MA-F2-request.md`,
Workspace-/Repo-AGENTS sowie der gesamte STACK-Diff
`6673b67eb3c51452d5e1714178d057738d1cb9e5..49273ffd848b8fe6ac30d28d67b99a18333000dc`:

- `compose.yaml`: `garage-setup` erhält `GARAGE_DEFAULT_*`, `GARAGE_ORIGIN_*`
  und `GARAGE_MANAGED_*` über Compose-Environmentinterpolation.
- `services/garage/setup-compose.py`: kein zweiter dotenv-Parser mehr;
  `values=dict(os.environ)`, Garage-2.4.1-Zeichenregeln vor jedem Admin-API-
  Schreibzugriff.
- `scripts/test_garage_migration_delta.py`: neue F11/F13-Regression mit echten
  Garagequellen/-zielen, Compose-Tooljobs und read-only Origin.
- `scripts/management/review-phase.py`, `review_gate.py`,
  `test_review_gate.py`: explizite, SHA-gebundene CARRIED-Übernahme.
- `F2_IMPLEMENTATION.md`, `MA-F2-request.md`, `review/MA-F2-review-01.md`:
  Dokumentation/Request des Deltas.

Kein Diff in PostgreSQL-Restore, Keycloak/Identität, Principal-Migration,
Coordinator, Rollback oder Superset/Backup. Die Zeichenregeln wurden gegen den
gepinnten Garage-2.4.1-Quellcode (`key_table.rs`, `Key::import`) geprüft: IDs
mindestens 8 ASCII-Alphanumerik/`-_.`, Secrets mindestens 16 graphische
ASCII-Zeichen (U+0021–U+007E). Die neue Prüfung setzt genau diese Grenzen um.

## 3. Selbst ausgeführte Prüfungen

| ID | Ausführung | Kommando / CWD | Exit | Beobachtung | Beleg |
|---|---|---|---|---|---|
| F09 | `CARRIED` | `./scripts/test-consolidation.sh --phase MA-F2` in `.../MA-F2/20261104T232247Z/workspace/dateninfrastruktur-dev-stack` | 0/0 | Nichtleerer logischer Restore PG16.9→16.10 in drei DBs; AccessGrants=2; Owners/ACLs/Sequenzen/Rollen- und DB-Parameter verglichen; kein Dump-only-Nachweis. Kein DB-Code im neuen Diff. | `prior-evidence/F09-evidence.log` (SHA256 `c8a676e6...`) |
| F10 | `CARRIED` | dieselbe Hauptprobe | 0/0 | Aktueller H2-Export, 4 Keycloak-User inkl. MA-only, exakte UUIDs, 3 Foundation-Overlaps, 1 MA-only-Import, 1 Profilupdate, auditierte Issuerzuordnung, altes Auditpräfix unverändert, Konflikte/gefälschter `di_writer`-Kontext verweigert, Replay no-op. Kein Identitäts-/Keycloak-Code im neuen Diff. | `prior-evidence/F10-evidence.log` |
| F11 | `EXECUTED` | `python3 scripts/test_garage_migration_delta.py` in `.../MA-F2/20261104T234324Z/workspace/dateninfrastruktur-dev-stack` | 0/0 | Quelle inventarisiert → Copy → Verify → Replay; 1 Objekt, 1 anfangs fehlend, 0 beim Replay; Origin-Read positiv, Origin-Write 403, Legacy-Key auf `ch.so.daten` positiv und privat 403; rclone-Operator und Origin-HTTP liefern identische Bytes. | `output/garage_delta.stdout.log` |
| F12 | `CARRIED` | dieselbe Hauptprobe | 0/0 | Echter Fehler nach Backup vor Aktivierung → Rückfall auf exakt dieselben Quellcontainer; geänderte Rolle/Client invalidiert Backup; Replay ohne Dubletten; auditierter Cayenne-Schreibvorgang mit fortgesetzter Sequenz; Rollback nach Zielwrites `ROLLBACK_UNSAFE`; PG-Container-/Image-ID unverändert. Zusätzlich `test_migration_safety.py` frisch: 4 Tests OK. | `prior-evidence/F12-evidence.log` |
| F13 | `EXECUTED` | `python3 scripts/test_garage_migration_delta.py` | 0/0 | Importierte Managed-/Origin-Secrets mit Dollar, beiden Quotezeichen und Backslash werden exakt transportiert; ein Newline-/Control-Secret wird mit `INVALID_GARAGE_CREDENTIAL` vor jeder Admin-API-/Schlüsseländerung abgewiesen; gültige Grafikzeichen funktionieren über S3, rclone-Operator und Origin. Das ist der geänderte Secret-Erhaltungsteil von F13; die unveränderten Superset-`SECRET_KEY`-/Verschlüsselungs- und Backup-Claims wurden im gebundenen Vorbericht `529acb...` am Base `6673b67` beobachtet und sind von diesem Diff nicht berührt. | `output/garage_delta.stdout.log` |

Ergänzend frisch ausgeführt:

- `DI_GATE_TEST_PHASE=MA-F2 python3 scripts/management/test_review_gate.py`
  → Exit 0, 1 Test OK. Der Gate-Test akzeptiert eine gebundene, erfolgreiche,
  unveränderte CARRIED-Beobachtung aus einem NACHARBEIT-Bericht und weist
  geänderten Report/Beleg, fehlende Begründung, FAIL-Quelle, fehlenden Verweis
  und ungebundene Übernahme ab.
- `python3 scripts/test_migration_safety.py` → Exit 0, 4 Tests OK. Der
  Compose-native Codec transportiert Quotes, Dollar, Backslash und Newline
  exakt; Env-/Render-Drift wird vor jeder Docker-Mutation abgewiesen.

## 4. Übernommene Nachweise (CARRIED)

| ID | Quellbericht | Begründete Nichtbetroffenheit |
|---|---|---|
| F09 | `529acb917f3346156f2d459a08f5e5981368d6adeb6d359985bf46b53bf5f9d5` | Kein PostgreSQL-Restore-/Backup-/Dump-/Owner-/ACL-/Sequenzcode im Diff; `compose.yaml` ergänzt nur `garage-setup`-Env-Werte. |
| F10 | derselbe | Kein Keycloak-/Identitäts-/Principal-/Auditcode im Diff; `migration_identity.py`, V009 und Keycloak-Setup unverändert. |
| F12 | derselbe | Kein Coordinator-/Binding-/Rollback-/Write-Guard-Code im Diff; die Garage-Delta-Probe ändert den Rückfallpfad nicht. |

Die kopierten Belege (`F09/F10/F12-evidence.log`, SHA256 `c8a676e6...`) und die
gebundenen Prior-Artefakte wurden vor der Übernahme per Hash geprüft. Das alte
`NACHARBEIT`-Urteil und der alte MAJOR-Befund werden nicht übernommen; nur die
unveränderten, erfolgreich selbst ausgeführten Beobachtungen.

## 5. Eigene Gegenprobe

**Hypothese:** Gültige Garage-2.4.1-Grafik-ASCII-Secrets mit Compose-/dotenv-
Metazeichen, die der Provider-Test nicht abdeckt (`${VAR}`, `#`, `=`, Backtick,
Klammern, Semikolon), werden von Compose literal zugestellt und bleiben über
Garage-Import, S3, rclone-Operator und Origin nutzbar.

**Ausführung:** `python3 output/counterexample_garage_env_literal.py` (eigenes
isoliertes `maf-f2-counter-*`-Compose-Projekt; nur synthetische Werte).

**Erwartung:** Container-Env und Operator-/Origin-Konfiguration enthalten die
exakten literalen Secrets (keine `${HOME}`-/`${PATH}`-Expansion); Managed-/Origin-
Reads gelingen; Origin-Write, Legacy-private-Read und Managed-Fremdbucket-Read
liefern 403; Origin-HTTP liefert dieselben Bytes.

**Beobachtung:** Alle vier PASS-Zeilen, Exit 0. Der Test hat die Env-Werte im
`garage-setup`-Container direkt geprüft, ein Objekt mit dem importierten
Managed-Key geschrieben, mit Origin gelesen, die 403-Grenzen geprüft und die
Bytes über rclone-Operator und Origin-HTTP verglichen. Cleanup entfernte alle
eigenen Container/Volumes/Netze.

Beleg: `output/counterexample_garage_env_literal.stdout.log` (stderr leer).

## 6. Befunde

Keine BLOCKER/MAJOR/MINOR-Findings. Der frühere F2-MAJOR-1 ist behoben: Der
zweite dotenv-Parser ist entfernt, Compose liefert die Werte direkt, und die
Garage-Zeichenregeln werden vor Mutation geprüft. Die neue Regression deckt
Dollar, beide Quotezeichen, Backslash und Newline-Transport ab; die eigene
Gegenprobe ergänzt `${VAR}`, `#`, `=`, Backtick und Klammern.

## 7. Integrität und Grenzen

- Produktbäume: exakt die Handoff-HEADs, `git status --porcelain` leer; der
  Vorher-/Nachher-Vergleich aller getrackten Dateien ist identisch
  (`before.json` → `output/after_integrity.json`).
- Keine Änderungen an Produktcode, Tests, Spezifikationen, AGENTS oder
  Konfiguration. Keine Reparatur.
- Laufzeit: ausschliesslich eigene `maf-f2-garage-*`- und
  `maf-f2-counter-*`-Compose-Projekte, zufällige Testcredentials, keine
  Nutzer-`.env`, keine Dumps. Nach dem Lauf keine eigenen `maf-*`-Container,
  -Volumes oder -Netze verblieben.
- Nutzerdienste (`dateninfrastruktur-dev-stack-*`, `di-ma-*`) und der
  Original-Workspace wurden nicht gestartet, gestoppt oder verändert.
- Keine Secretwerte in diesem Bericht oder in den Belegen. Der echte lokale
  Cutover bleibt `LOCAL_CUTOVER_PENDING` (F3/Operator).

## 8. Ergebnis

F11/F13 sind am neuen Kandidaten real ausgeführt und bestanden; F09/F10/F12
sind als unveränderte, hashgebundene Beobachtungen des vorherigen unabhängigen
Reviews begründet übernommen. Die eigene Gegenprobe bestätigt den reparierten
Secretpfad über zusätzliche Metazeichen. Produktbestand unverändert, keine
offenen Pflichtläufe, keine blockierenden Findings:

**ABGENOMMEN** für MA-F2 am SHA-Satz
`49273ffd848b8fe6ac30d28d67b99a18333000dc` (STACK) und den fünf unveränderten
Geschwister-HEADs. Der lokale Cutover ist damit nicht ausgeführt und bleibt
separat `LOCAL_CUTOVER_PENDING`.
