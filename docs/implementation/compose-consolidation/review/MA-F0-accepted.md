# Unabhängiges Review MA-F0 – Compose-Konsolidierung

- **Urteil: ABGENOMMEN**
- **Phase:** MA-F0 (Gate F01–F03)
- **Kandidat:** `20261104T203347Z`
- **Reviewer:** OpenCode 2.x, tatsächliches Modell `deepseek/deepseek-flash` (DeepSeek V4.1 Flash 1017),
  CLI `opencode v2.2.5`, Session `ses_e57bb6b73ffebw5I7Zf0KVJDsD` (frische Sitzung, Read- und Shelltools tatsächlich ausgeführt).
- **Reviewdatum:** 2026-11-04

## 1. Bindung (selbst geprüft, nicht übernommen)

| Element | Wert |
|---|---|
| Handoff SHA256 | `f5a20ede6662780d4676d3acc6e345e19e421ff71e023813e5aa7de692dd81d7` |
| Spezifikation Aggregate SHA256 | `734440b41ca95ecc6ed7cc2283caf2fd4202eb9b892601a3486c98a716e8ac99` |
| Request SHA256 | `ce211c3c921890a24deeef7c9d34d8858f08c176424a76950c01b389872ef696` |
| Workspace-AGENTS SHA256 | `21df33d38618ccd414f082c901f08b457adbd07551620f49e5455565d2c8ee4e` |

Alle zehn Spezifikationsdateien wurden einzeln neu gehasht; alle Werte stimmten. Der Aggregate-Hash
wurde aus der sortierten `files_sha256`-Map nachgerechnet und stimmt. Die aktive Workspace-`AGENTS.md`
ist byte-identisch mit `templates/AGENTS.workspace.current.md`; der Runner erzwingt diese Gleichheit.

Exakter SHA-Satz (HEADs selbst per `git rev-parse` gelesen, alle Trees clean):

| Repo | HEAD |
|---|---|
| dateninfrastruktur-dev-stack | `125aace5dda88fe63e58bd575ccc4bef5ab48532` |
| dateninfrastruktur-admin | `6b6388b350f6de3d49abde076629a9c8d50a5ba0` |
| dateninfrastruktur-sodata | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` |
| dateninfrastruktur-jenkins-dev | `08931fa8254d096e2addcd3aee97bc1b753f087d` |
| dateninfrastruktur-jenkins-gretl-plugin | `579f3fd54432a977122afb186469fbb40d95322f` |
| dateninfrastruktur-themenrepo | `7d99ceec0e392a5f12b602c0840c4762c7213fba` |

Die Request-Base-SHAs sind Vorfahren der HEADs (Runner prüft `merge-base --is-ancestor`); die drei
unveränderten Repos haben base == head.

## 2. Gelesener Umfang

Vollständig gelesen: `EXECUTION_PLAN.md`, `SPEC_MIGRATION.md`, `TEST_PLAN.md`,
`OPENCODE_REVIEW_PROMPT.md`, `CODEX_STARTPROMPT.md`, `AGENTS_ERGAENZUNG.md`, `F0_BASELINE.md`,
`README.md`, `SOURCES.md`, Workspace-AGENTS, die AGENTS der betroffenen Repos sowie die
Reviewvorlagen. Gelesener Diff `f72d929f..125aace5` (STACK), `7986d673..6b6388b3` (ADMIN),
`20d94f5f..b1f20075` (PUBLIC); JENKINS/PLUGIN/TOPICS unverändert.

Diff-Inhalt STACK: neues `services/postgres/{Dockerfile,image.lock.json}`,
`tests/consolidation/pg-probe.compose.yaml`, `scripts/consolidation.py`,
`scripts/test_consolidation_f0.py`, `scripts/test-consolidation.sh`, Erweiterung von
`scripts/management/{review-phase.py,review_gate.py,test_review_gate.py}`, AGENTS-Ergänzung,
`F0_BASELINE.md`, `WORK_QUEUE.md`, Request und Workspace-AGENTS-Kopie. ADMIN/PUBLIC nur
AGENTS-Ergänzung. Kein Eingriff in `compose.yaml` (F1-Topologie nicht vorweggenommen).

## 3. Pflichtprüfungen (selbst ausgeführt)

| ID | Befehl (CWD) | erwartet/beobachtet | Beobachtung |
|---|---|---|---|
| F01 | Ownership-Unittest + lesende Inventur mit eigenem Projektfilter (`STACK/`) | 0 / 0 | Falsche volle ID, Name, Mount, Projekt, Service, Arbeitsverzeichnis und zu kurze ID werden **vor** dem Mutationscallback verweigert (Callback 0-mal aufgerufen); private Pfade 0700/0600. Zusätzlich Inventur mit eigenem Projektnamen: 0 Quellen selektiert, 32 unselektiert, kein Env-Ref, Modi 0700/0600, kein Dockerobjekt verändert. |
| F02 | Echter kurzlebiger Compose-PG-Probecontainer (`t.pg_probe()`, `STACK/`) | 0 / 0 | Nativ **arm64** (Host arm64), `server_version_num=160010` (PG 16.10), PostGIS-Lib **3.5.2**, drei logische DBs `keycloak`/`superset`/`dateninfrastruktur_management`; PostGIS/uuid-ossp nur in Management, in `template1`/`keycloak`/`superset` je 0. Eigenes Projekt `maf-f0-ccb934556c86`, eigenes benanntes Volume, danach restlos entfernt. |
| F03 | Gate-Negativtest (`scripts/management/`) | 0 / 0 | Fremder Repo-SHA, fehlende/doppelte ID, `NOT_EXECUTED`, falsches Modell, nicht ausgeführte Gegenprobe, `example_only`, falsches Urteil, fehlender Report und veränderte Produktquelle schliessen das Gate. Zusätzlich eigene Validierung des realen Handoffs (siehe §4). |

Der kombinierte Lauf `./scripts/test-consolidation.sh --phase MA-F0` wurde ebenfalls ausgeführt
(Exit 0) und liegt als Zusatzbeleg vor.

Alle Befehle liefen ausschliesslich im isolierten Klon; Produktpfade wurden nicht verändert.

## 4. Eigene Gegenprobe (nicht umbenannter Produkttest)

Reviewer-eigenes Skript `counterexample_f01_ownership.py` (im Ausgabeordner, ausserhalb der
Produktbäume) gegen **echte** Dockerobjekte und ein Fixture-Dateisystem:

- **Hypothese:** Da `verify_ownership` den Container live neu inspiziert, kann ein manipulierter
  Plan weder Name, Mount, ID noch Projekt scope-spoofen; ein privater State-Pfad, der aus
  `ADMIN/.runtime` ausbricht, wird verweigert — jeweils vor dem Operationscallback.
- **Positivkontrolle:** Ein treuer Ref auf einen echten, korrekt gelabelten Decoy-Container wird
  akzeptiert und der Callback genau einmal mit der inspizierten ID aufgerufen (Test ist nicht vakuum).
- **Negativfälle (alle Exit 0 = Verweigerung):** gespoofter Name, gespoofter Mount-Source, fremdes
  Compose-Projekt, zu kurze Container-ID, symlinkender State-Pfad ausserhalb des Runtimeverzeichnisses.
  Der Callback wurde in allen Negativfällen **0-mal** aufgerufen.
- Decoy-Container danach entfernt; keine Restressource.

Damit ist die F01-Kernaussage unabhängig von der Mock-basierten Produkteinheit bestätigt.

## 5. Befunde

Keine BLOCKER/MAJOR. INFO-Beobachtungen (nicht abnahmeblockierend):

1. **Image-ID nicht bitstabil:** Zwei reale Probeläufe ergaben unterschiedliche Image-IDs
   (`sha256:f3343b…`, `sha256:7433c9…`) bei identischem Dockerfile/Base-Digest/Pakethashes. Das ist
   normales Docker-Verhalten (Creation-Metadaten); der Buildvertrag sind die gepinnten Digests/Hashes,
   nicht die Image-ID. `image.lock.json` formuliert das bereits korrekt.
2. **F01-Einheitstest deckt den Foundation-Zweig ab;** der Management-State-Zweig und
   `config_files` werden im Code geprüft, aber nicht durch einen mutierten Einheitstest. Meine
   Gegenprobe deckt Live-ID/Name/Mount/Projekt und den State-Pfadausbruch ab. Empfehlung für spätere
   Phasen: zusätzliches Management-Fixture.
3. **`issuer_reference`** übernimmt das `keycloak`-Feld der privaten State-Datei unverändert in die
   private Inventur/den Plan (0700/0600). Das bleibt im privaten Bereich; der bereinigte Bericht darf
   `secret_refs` niemals serialisieren.

## 6. Grenzen dieses Reviews

- Die private Rohinventur und der Live-Plan des Implementierers wurden **bewusst nicht** an den
  Reviewer übergeben. Die Aussage „genau eine gebundene befüllte MA-Quelle“ ist daher nicht
  unabhängig nacherhoben; geprüft wurden Code-Pfad, Planstruktur und die fail-closed-Logik. Das ist
  eine dokumentierte Live-/Cutover-Grenze (`LOCAL_CUTOVER_PENDING`), kein F0-Codefehler.
- Kein F1-Stack, kein Restore, kein Cutover wurde geprüft (phasenkonform nicht Teil von F0).
- Die Nutzercontainer und -volumes wurden nicht angefasst: 32 Container und 33 Volumes sind vor/nach
  byte-identisch (siehe `docker-before.json`/`docker-after-all.json`).

## 7. Integrität

- Produktbäume unverändert: alle sechs HEADs identisch, `git status --porcelain` überall leer,
  Index-/Blob-Hash vor/nach gleich (`f16a17ce…`).
- Probecontainer/-volumes/-netzwerke restlos entfernt; einzige verbleibende eigene Ressource ist das
  lokal gebaute Probeimage `dateninfrastruktur-postgres:maf-f0-268eaea8ac25` und private
  `.runtime`-Belegverzeichnisse (0700) im isolierten Klon.
- Keine Nutzersecrets, keine `.env`, keine Dumps gelesen oder in den Bericht übernommen.

## 8. Übernommene Nachweise

Keine. F0 ist die erste Phase; MA-A–E-Nachweise wurden nicht als Beweis für MA-F-Code übernommen.

## 9. Ergebnis

Die F0-Liefergegenstände sind vorhanden und die drei Pflichtverträge sind mit echten, selbst
ausgeführten Prüfungen belegt. Die Eigentümergrenze verweigert Manipulationen vor jeder Mutation,
das gewählte PG16/PostGIS-Image läuft nativ mit drei Datenbanken und korrekt begrenzten Extensions,
und der Reviewweg führt echte Tools aus und schliesst bei falschen Manifesten. Das Gate ist damit
**ABGENOMMEN** für den exakten Kandidaten-SHA-Satz.
