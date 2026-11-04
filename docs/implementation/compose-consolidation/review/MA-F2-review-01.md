# Unabhängiges Review MA-F2 – Bestandsübernahme und Rückfallprobe

**Urteil: NACHARBEIT** (ein MAJOR-Befund; F09–F13 selbst wurden real ausgeführt und bestanden, aber der Secret-Erhalt ist für eine nicht abgedeckte Secretklasse verletzt).

## 1. Bindung

| Feld | Wert |
|---|---|
| Phase / Kandidat | `MA-F2` / `20261104T232247Z` |
| Handoff-SHA256 | `0cc085a8b43488d32a5a7ff790815448ffbc088d43d78d67becaa08caafc60bb` |
| Spezifikations-SHA256 | `fc9fa000dea3e841f5398c13051d2f81021e34399bc4c5714cb0a37b39aba733` |
| Request-SHA256 | `a1f71b90cd5b3fafa699446ddd3d99517dc181be88fa170ef8fb6ba83070db0f` |
| Workspace-AGENTS-SHA256 | `21df33d38618ccd414f082c901f08b457adbd07551620f49e5455565d2c8ee4e` (identisch mit `templates/AGENTS.workspace.current.md`) |
| Modell / CLI / Session | `deepseek/deepseek-flash` / `opencode v2.2.5` / `ses_e5720afbdffeNewEAbRhhw52uK` |

Repositories (exakt aus dem Handoff):

| Repository | HEAD |
|---|---|
| dateninfrastruktur-dev-stack | `6673b67eb3c51452d5e1714178d057738d1cb9e5` |
| dateninfrastruktur-admin | `14374ecd58f2ad27432ec7fe0fd4535021795d80` |
| dateninfrastruktur-sodata | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` |
| dateninfrastruktur-jenkins-dev | `08931fa8254d096e2addcd3aee97bc1b753f087d` |
| dateninfrastruktur-jenkins-gretl-plugin | `579f3fd54432a977122afb186469fbb40d95322f` |
| dateninfrastruktur-themenrepo | `303b2f0be785dc5b06882612f9b8bfcd8c17b040` |

Alle sechs Produktbäume waren vor und nach dem Review clean (`git status --porcelain` leer). Die im Handoff genannten Spec-Dateien, der Request, die Workspace-AGENTS und der aggregierte Spezifikationshash wurden selbst nachgerechnet; alle stimmen. Der Runner verwendet die Desktop-CLI `.../cli/2.2.5-arm64/opencode-cli` (`opencode v2.2.5`); das unabhängig im PATH liegende `opencode` 1.18.22 war nicht die Runner-CLI.

## 2. Geprüfter Umfang

Vollständig gelesen: EXECUTION_PLAN, SPEC_MIGRATION, TEST_PLAN, OPENCODE_REVIEW_PROMPT, F2_IMPLEMENTATION, Request, Workspace-/Repo-AGENTS; Diffs STACK `09bf4dd..6673b67` und ADMIN `3f6f0f0..14374ec` (Compose-Toolservices, `migration_db.py`, `migration_identity.py`, `migration_coordinator.py`, `migration_backup.py`, `migration_prepare.py`, `migration_binding.py`, `services/garage/setup-compose.py`, `services/migration/storage.py`, V009 und `principal_identity_migration.py`, F2-/Sicherheits-/Identitätstests).

Ausgeführt mit eigenen isolierten `maf-f2-*`-Projekten, zufälligen Loopback-Ports, eigenen Volumes und ausschliesslich synthetischen Testcredentials. Keine Nutzer-`.env`, keine Dumps, keine Nutzerdienste (`dateninfrastruktur-dev-stack-*`, `di-ma-*`) wurden gelesen, gestoppt oder verändert.

## 3. Selbst ausgeführte Pflichtprüfungen

| ID | Kommando / CWD | Exit | Beobachtung | Beleg |
|---|---|---|---|---|
| F09 | `./scripts/test-consolidation.sh --phase MA-F2` in STACK | 0 | Nichtleerer logischer Restore PG16.9→16.10 in drei DBs; AccessGrants=2; Tabellen/Audit/Owner/ACLs/Sequenzen/Rollen- und DB-Parameter verglichen. | `f09_f13_consolidation.stdout.log` Zeile 6 |
| F10 | dieselbe Hauptprobe + `python3 scripts/test_migration_identity_permissions.py` | 0 / 0 | Aktueller H2-Export, 4 Keycloak-User (3 Foundation-Overlaps + MA-only), UUID-Beweis, Foundation-Passwörter erhalten, 3 Issuer-Bindungen umgestellt, altes Auditpräfix unverändert, Konflikte/gefälschter `di_writer`-Kontext verweigert, Replay no-op. | Hauptlog Zeile 6; `test_migration_identity_permissions.stdout.log` Zeile 1 |
| F11 | dieselbe Hauptprobe | 0 | 8 verwaltete Objekte mit unterschiedlichen Bytes/Metadaten; idempotentes Copy; Byte-/Metadatenkonflikt und Quelländerung abgewiesen; Origin RO und Foundation-Key privat verweigert, jeweils nach funktionierendem Positivzugriff. | Hauptlog Zeile 14 |
| F12 | dieselbe Hauptprobe + `python3 scripts/test_migration_safety.py` | 0 / 0 | Echter Fehler nach Backup vor Aktivierung → Rückfall auf exakt dieselben Quellcontainer; geänderte Rolle/Client invalidiert Backup; Replay ohne Dubletten; audited Cayenne-Schreibvorgang mit fortgesetzter Sequenz; Rollback nach Zielwrites `ROLLBACK_UNSAFE`; PG-Container-/Image-ID unverändert. Sicherheitstests: 4 OK. | Hauptlog Zeilen 2, 17; `test_migration_safety.stderr.log` |
| F13 | dieselbe Hauptprobe | 0 | Entschlüsselte Superset→ClickHouse-Verbindung liest 3 Zeilen; `SUPERSET_SECRET_KEY` erhalten; Archive privat (0600); keine Originalsecrets im Handoff. | Hauptlog Zeile 16 |

Zusätzlich: `python3 ../../output/counterexample_target_binding.py` (eigene isolierte Zielbindungsprobe) → Exit 0: exakte Bindung akzeptiert; geänderte `INSTANCE_ID` und veränderte Plan-`target_instance` jeweils als `OWNERSHIP_MISMATCH` vor jedem Docker-Mutationsaufruf abgewiesen; 0 Mutationsaufrufe.

## 4. Eigene Gegenprobe (fehlgeschlagene Hypothese)

Hypothese: Ein migriertes Garage-Secret mit `$`, Backslash und Zeilenumbruch wird vom Compose-Codec und vom Ziel-Garage-Setup identisch dekodiert, sodass importierter Key und `operator.conf` konsistent bleiben.

Ausführung: `python3 output/counterexample_garage_env_codec.py` (STACK als CWD; nur synthetische Werte, keine Produktdatei verändert).

Ergebnis: **Hypothese widerlegt.**
- Compose-Codec (`read_env`, Grundlage von `operator.conf`/`storage.py`): `'pa$word\\path\nline'`
- Zielparser in `services/garage/setup-compose.py:13`: `'pa$$word\\\\path\\nline'`
- Gleichheit: `False`

Damit importiert das Ziel-Garage-Setup einen anderen Secret-Wert als das Storage-Tool verwendet; `origin.conf` wird zusätzlich aus dem veränderten Wert geschrieben.

## 5. Befund

### F2-MAJOR-1 – Ziel-Garage-Setup umgeht den Compose-Dotenv-Codec

- **Ort:** `services/garage/setup-compose.py:13` (manuelles `line.split('=',1)[1].strip("'\"")`), verwendet in `imported_key()` für `GARAGE_MANAGED_*`/`GARAGE_ORIGIN_*` (Zeilen 27, 39) und beim Schreiben von `origin.conf` (Zeile 47); Gegenstück `scripts/compose_runtime.py:4-17`.
- **Wirkung:** `compose_runtime.encode_env` schreibt JSON-double-quoted Werte und verdoppelt `$`; der manuelle Parser entfernt nur Quotes. Bei Secrets mit `$`, Backslash, Quote oder Newline entstehen unterschiedliche Werte zwischen Garage/Origin und `operator.conf`/`storage.py`. Der F2-Delta nutzt diesen Parser neu für die zu importierenden MA-Garage-Keys. Ein solcher Migrationslauf kann beim S3-Copy/Read scheitern oder einen unbrauchbaren Key importieren; die F11/F13-Fixture verwendet `secrets.token_hex` und deckt den Fall nicht ab.
- **Widerspruch:** F2_IMPLEMENTATION behauptet, Quotes, Dollars, Backslashes und Zeilenumbrüche blieben in übernommenen Secrets erhalten; `test_migration_safety.test_compose_native_secret_codec` prüft nur `read_env`, nicht den Garage-Konsumenten.
- **Kleinste Korrektur (nicht ausgeführt):** `setup-compose.py` muss `runtime.env` mit demselben Compose-nativen Decoder lesen (oder die Werte über Compose-Environment beziehen), bevor `imported_key()`/`origin.conf` sie verwenden; Regression mit `$`/Backslash/Newline und positivem S3-Zugriff plus erwarteter Negativgrenze ergänzen.

## 6. Integrität und Grenzen

- Produktbäume: exakt die Handoff-HEADs, clean; keine Änderungen an Produktcode, Tests, Spezifikationen, AGENTS oder Konfiguration. Keine Reparatur.
- Laufzeit: ausschliesslich eigene `maf-f2-*`-Projekte/Volumes/Ports/Testcredentials; nach dem Lauf keine `maf-*`-Container oder -Volumes verblieben. Nutzerdienste und Original-Workspace unverändert.
- Der echte lokale Cutover wurde bewusst nicht ausgeführt: `LOCAL_CUTOVER_PENDING` (F3/Operator).
- Keine Secrets, Dumps oder personenbezogenen Rohdaten in diesem Bericht.

## 7. Ergebnis

F09–F13 sind auf nichtleeren isolierten Fixtures technisch nachgewiesen; die Daten-, Identitäts-, Storage-, Rückfall- und Superset-Nachweise sind belastbar. Wegen des reproduzierten MAJOR-Defekts im Ziel-Garage-Secretpfad ist die Phase jedoch **NACHARBEIT**: Codex muss die kleinste Korrektur umsetzen, neu committen und ein Delta-Review auslösen.
