# Unabhängiges Review MA-F1 – kanonischer Single-Instance-Compose-Stack

**Urteil: ABGENOMMEN**

| Feld | Wert |
|---|---|
| Phase | MA-F1 |
| Kandidat | 20261104T210539Z |
| Reviewer-Modell (tatsächlich) | `deepseek/deepseek-flash` |
| CLI (tatsächlich ausführend) | `opencode v2.2.5` (`.../ai.opencode.desktop/cli/2.2.5-arm64/opencode-cli`) |
| Session | `ses_e579e3b7cffevc5eYRO1drN6jM` (Agent `management-review`) |
| Handoff-SHA256 | `18839f143cf19707adeeb759f84c615f30368c9689368336e15b5824ca0b84f6` |
| Spec-Aggregat-SHA256 | `08a23487587ea17faf78add1d00dd55a3eb4a333dbd1414dd1ff35f53ed3ddde` |
| Request-SHA256 | `d7c6ced9ceb6c37f7041b9a273da4e3460ab5020add47d69d1c2103f8aa1877a` |

> Hinweis zur Transporttransparenz: das `opencode` auf `PATH` ist ein anderes, älteres Binary (1.18.22). Die
> tatsächlich ausführende Sitzung läuft über die Desktop-CLI `opencode-cli` 2.2.5, die exakt
> `opencode v2.2.5` meldet. Modell/Agent/Session wurden aus dem laufenden Prozess verifiziert.

## 1. Selbst geprüfte Kandidatenbindung

Handoff, Request und alle Speckapitel wurden vollständig in der isolierten Workspace gelesen. Ich habe
Hashwerte und HEADs **selbst** neu berechnet (nicht aus dem Handoff übernommen):

```
$ shasum -a 256 .runtime/.../handoff.json
18839f143cf19707adeeb759f84c615f30368c9689368336e15b5824ca0b84f6
$ shasum -a 256 workspace/AGENTS.md
21df33d38618ccd414f082c901f08b457adbd07551620f49e5455565d2c8ee4e   (= templates/AGENTS.workspace.current.md)
$ shasum -a 256 .../review/MA-F1-request.md
d7c6ced9ceb6c37f7041b9a273da4e3460ab5020add47d69d1c2103f8aa1877a
# alle 11 Spec-Dateien: jeder Einzelhash = Handoff-Eintrag
```

Exakter SHA-Satz (vor **und** nach dem Review, `git status --porcelain` jeweils leer):

| Repo | HEAD |
|---|---|
| dateninfrastruktur-dev-stack | `ceb0bfa657a2fffef57535911026381542cc3102` |
| dateninfrastruktur-admin | `3f6f0f0d526de81e84a9d496582cd9265ed180ce` |
| dateninfrastruktur-sodata | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` (unverändert) |
| dateninfrastruktur-jenkins-dev | `08931fa8254d096e2addcd3aee97bc1b753f087d` (unverändert) |
| dateninfrastruktur-jenkins-gretl-plugin | `579f3fd54432a977122afb186469fbb40d95322f` (unverändert) |
| dateninfrastruktur-themenrepo | `303b2f0be785dc5b06882612f9b8bfcd8c17b040` |

Belege: `product-before.txt`, `product-after.txt`, `evidence-hashes.txt`.

## 2. Gelesener Diff / Scope

```
STACK  fc2ab19..ceb0bfa  12 Dateien, +1367/-342
ADMIN  6b6388b..3f6f0f0   9 Dateien, +167/-4
TOPICS 7d99cee..303b2f0   2 Dateien, +13/-2
PUBLIC/JENKINS/PLUGIN     keine Änderung
```

Gelesen wurden u. a. `compose.yaml` (JSON-förmiges YAML), `scripts/compose_runtime.py`,
`scripts/test_consolidation_f1.py`, `services/apisix/{config.single.yaml,routes.template.json}`,
`services/{garage/setup-compose.py,postgres/initialize-compose.py,postgres/Dockerfile,superset/*,clickhouse/init}`,
ADMIN `Dockerfile`, `scripts/{database_target,setup_explicit,management_db,audit_setup,interlis_tools}.py`,
`ComposeFixtureCommand.java`, `ComposeJourneyIT.java`, `ManagedDownloadFixtureIT.java`, `build.gradle`,
TOPICS `datenportal-publication.gradle`. Diffstat: `review-diffstat.txt`.

Kernbefunde des Code-Reviews (Zielerreichung):
- **Genau eine Standardtopologie**: 10 Default-Services, keine `container_name`, kein `network_mode`,
  keine `*-a/-b`, Einmaljobs ausschliesslich mit Profil `setup`/`tools`/`test`.
- **Ein PG16/PostGIS** (`16.10-bookworm` + PostGIS 3.5.2, arm64-nativ, gepingte Hashes), drei getrennte DBs.
- **Kein H2-Keycloak**: `KC_DB=postgres`; stabiler Issuer `localhost:18080`, internes JWKS `keycloak:8080`.
- **Kein Host-JAR**: Admin/Sodata werden aus Quellen gebaut; Tooling-/Test-Targets im Image.
- **APISIX aus Jenkins-Netzwerkraum gelöst**: eigener Dienst, eigene Loopback-Portbindung, Jenkins über `jenkins:8080`.
- **Setup entkoppelt**: `database_target.py`/`management_db.py` im `DI_DATABASE_TARGET=postgresql`-Modus
  verbieten Container-Lifecycle; `audit_setup` schreibt im Zielmodus keine getrackte `db/audit-policy.json`.
- **Superset erhält** bestehende Verbindung (`configure_database.py` überschreibt nicht mehr).
- **DB-Katalogmodus** der Legacy-Pipeline unterdrückt Portalreload deterministisch.

## 3. Pflichtprüfungen F04–F08 – selbst ausgeführt

Einziger Pflichtbefehl aus dem Request, im isolierten Checkout ausgeführt:

```
CMD:  ./scripts/test-consolidation.sh --phase MA-F1
CWD:  <workspace>/dateninfrastruktur-dev-stack
EXIT: 0   (STARTED 21:09:53Z, ENDED 21:11:30Z)
```

Das Skript baut ausschliesslich die kanonische `compose.yaml` mit frischem Zufallsprojekt, reservierten
Ports, neuen Testcredentials/Volumes und räumt nur eigene Container/Volumes ab.

| ID | Ergebnis | Beobachtung (selbst verifiziert) | Evidenz |
|---|---|---|---|
| **F04** | PASS | 10 laufende, gesunde Services, je einmal, echte Compose-Namen; `container_name`/`network_mode`=false; keine `.jar`-Bindmounts; Hostports nur Loopback auf gateway/keycloak/superset/clickhouse. Zusätzlich live beobachtet (`live-topology.txt`). | `evidence/F04.txt` |
| **F05** | PASS | `server_version_num=160010`, PostGIS 3.5.2 nur im Management, exakt 3 DBs, keine GIS-Extension in template1/keycloak/superset, App-Rollen unprivilegiert. Gegenprobe: echte Mutationsversuche/Cross-DB-Logins werden verweigert (s. u.). | `evidence/F05.txt` |
| **F06** | PASS | Explizites Setup (postgres-init/management-setup/garage-setup/clickhouse-init) + kanonisches `up -d --wait`; leerer Katalog (`dataset+accessgrant=0`), `/`=200 ohne „MA-E Pilot“; Build aus Quellen, kein Host-JAR. | `evidence/F06.txt` |
| **F07** | PASS | Ein Keycloak auf PostgreSQL; echter Passwort-Grant-Token **und** echter Playwright-Browsercodeflow (anna Antrag → claudia Genehmigung → privater Download); anon open 200+Hash, anon restricted 401, berechtigter-aber-nicht-freigegebener Benutzer 403; alle 8 Distributionen (2 Datensätze × 2 Versionen × 2 Formate) mit passendem sha256 erneut geladen; `/internal/...` und `/ch.so.daten/...` 403. | `evidence/F07.txt` |
| **F08** | PASS | `/jenkins/login`=200, `/anlieferung`=302 → `/jenkins/...`; echter Offline-Gradle-Adapterlauf im isolierten Jenkins meldet `reloadPortal SKIPPED` und `reloadPortal=false` (DB-Modus, kein Legacyreload); gespeicherte (SECRET_KEY-verschlüsselte) Superset-ClickHouse-Verbindung führt echtes `SELECT` mit 3 Zeilen aus; Upstreams über Service-DNS, keine defekten localhost-Upstreams. | `evidence/F08.txt` |

Vollständiges Rohlog: `F04-F08.log` (sha256 `af1d02f8…`). Zwischenlog eines vom Transport abgebrochenen
Hintergrundversuchs (nur F04–F06 erreicht) transparent in `F04-F08.attempt1-interrupted.log`; dieser Lauf
wurde vom Reviewer über die produktseigene, eigentümergeprüfte Cleanup-Funktion sauber abgeräumt und der
Pflichtbefehl danach vollständig neu ausgeführt (Exit 0).

## 4. Eigene Gegenprobe (unabhängig, nicht umbenannt)

**Hypothese:** Client-seitige Identitäts-/Gateway-Header können kein echtes OIDC-Credential ersetzen;
kodierte/traversierende Downloadpfade erreichen keine Dateien; die dokumentierten PG-Rollen-/DB-Grenzen
verweigern **echte** Mutationsversuche (nicht nur fehlende Privileg-Bits).

Ausgeführt in `counterexample.py` gegen eine eigene, kanonisch gestartete isolierte Instanz
(`--keep-runtime`, Projekt `maf-f1-33908578a9`, Exit 0). Ergebnis **7/7 Probes bestanden**:

```
positive control anna restricted .... 200, sha256 match   (erschlossene Ressource existiert)
positive control anonymous open ..... 200, sha256 match
forged X-DI-Gateway-Credential u. a. . 401, 0 bytes       (kein Ersatz für echtes Token)
forged headers /internal/authorization 403
GET /downloads/%2e%2e/%2e%2e/etc/passwd 400, kein "root:"-Byte
GET /downloads/..%2f..%2fetc%2fpasswd   400, kein "root:"-Byte
DB: di_writer/di_public eigenes SELECT ok; di_public DELETE di_management.dataset -> permission denied
    di_writer DELETE audit.row_change -> permission denied
    di_public->keycloak, di_writer->superset -> "permission denied for database"
    di_owner/di_audit_owner rolcanlogin = 0/0; audit.tableowner = di_audit_owner
    audit-Funktionen SECURITY DEFINER = true
```

Belege: `counterexample.log` (sha256 `6aa25d91…`), `counterexample-setup.log`, `evidence/CE.txt`.
Die Gegenprobe ist positiv kontrolliert (identisches Credential liefert zuerst erlaubte Bytes) und
bestätigt damit belastbar die Negativresultate gemäss TEST_PLAN §2.

## 5. Findings

Keine BLOCKER, keine MAJOR. Nicht blockierende Beobachtungen:

1. **MA-F1-OBS-1 (MINOR, Teststärke):** Die Fixture schreibt für alle Versionen/Formate identische Bytes
   (alle CSV gleich, alle XLSX gleich). Die Prüfung „alle historischen Byteshashes“ belegt damit je
   Distribution registrierten sha256/Grösse/Verfügbarkeit und die ausgelieferten Bytes, kann aber Version 1
   und Version 2 inhaltlich nicht unterscheiden. Empfehlung für eine Folgephase: versionsspezifische Bytes.
   Der sicherheitsrelevante F07-Vertrag (Autorisierung + registrierter Hash) ist dennoch echt ausgeführt.
2. **MA-F1-OBS-2 (INFO):** Direkte Own-DB-Loginproben decken keycloak/superset/di_writer/di_authz/di_public
   ab; `di_migrator`/`di_audit_reader` werden indirekt (Audit-UI im Browserflow, Owner-/Privilegprüfungen,
   Reviewer-Gegenprobe) abgedeckt, nicht durch einen eigenen Loginprobe. Optional ergänzen.
3. **MA-F1-OBS-3 (INFO, Risiko für F3/F4):** Jenkins trägt weiterhin `s3Publish=true` mit
   `publicationManifestUrl=http://gateway:9080/ch.so.daten/current.json`, das der neue Gateway mit 403
   verweigert. Der DB-Modus unterdrückt den Reload korrekt (nachgewiesen); ein Legacy-`s3Publish`-Job
   könnte aber am 403-Manifest scheitern. Kein F1-Gate, bei der Legacy-Ablösung (F3/F4) behandeln.

## 6. Nicht ausgeführt / nicht erforderlich

- **F01–F03:** MA-F0-Gate, bereits unabhängig abgenommen (20261104T203347Z), durch diesen Kandidaten nicht verändert.
- **F09–F13 (F2), F14–F16 (F3), F17–F20 (F4):** spätere Phasen.
- **MA-A–E-Vollsuiten:** laut TEST_PLAN/EXECUTION_PLAN bewusst nicht erneut auszuführen.
- Offene Pflichtläufe: **keine**.

## 7. Integrität

- **Produkt unverändert:** alle sechs Repos vor/nach identisch (HEAD + leeres `git status --porcelain`);
  Workspace-AGENTS, alle Spec-Dateien und der Request exakt handoff-gleich; `db/audit-policy.json` nicht umgeschrieben.
- **Eigene Ressourcen:** nach dem Lauf keine eigenen Container/Volumes; verbleibend nur
  projektgebundene Build-Images (`dateninfrastruktur-*:maf-f1-…`, in `review.json` gelistet).
- **Nutzerlaufzeit unangetastet:** Foundation-Stack (`dateninfrastruktur-dev-stack`, 9 Container) blieb
  durchgehend „Up 30 hours (healthy)“; keine Nutzer-`.env`, Dumps, Volumes oder Services gelesen/verändert.
- Keine Produktdateien, Tests, Specs, AGENTS oder Konfiguration durch den Reviewer geändert; keine Commits/Pushes.

## 8. Urteilsbegründung

Der normale deklarative Composepfad startet nachweislich den vollständigen Stack (10 Dauer-Services, ein
PG16/PostGIS, kein H2-Keycloak, keine zweiten Gateways/Admins/Portale, keine Host-JAR-Abhängigkeit).
APISIX ist vom Jenkins-Netzwerkraum gelöst. Echte UI-/OIDC-/Download-/Jenkins-/Superset-Anbindung wurde
selbst ausgeführt, nicht durch Containerstatus ersetzt. Die eigene Gegenprobe bestätigt zusätzlich die
Sicherheits- und DB-Grenzen. Damit sind die F1-Verträge F04–F08 mit überprüfbarem Testnachweis erfüllt;
die MINOR-Beobachtung schwächt die Evidenz nicht gate-relevant. → **ABGENOMMEN** am exakten SHA-Satz.

**Nächster Schritt:** Codex darf MA-F2 beginnen. `LOCAL_CUTOVER_PENDING` bleibt unverändert.
