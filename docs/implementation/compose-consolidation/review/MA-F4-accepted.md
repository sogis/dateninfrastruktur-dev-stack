# Unabhängiges Review MA-F4 – konsolidierte Endabnahme am gemeinsamen Compose-Verbund

**Urteil: ABGENOMMEN**

Geprüft wurde der Kandidat `20261105T013710Z` der Phase MA-F4 auf dem exakten
Handoff-SHA-Satz. Die Pflicht-IDs **F17, F18, F19 und F20** wurden vom Reviewer
**selbst und frisch** auf einem eigenen, kurzlebigen Compose-Projekt aus derselben
`compose.yaml`, denselben Images, Vorlagen und Setupwerkzeugen ausgeführt. Es gab
keine `carried_checks`; kein Vorbeleg und kein früheres Urteil wurde übernommen.
Zusätzlich wurde eine eigene, nicht vom Kandidaten vorgegebene Gegenprobe
(Fail-Closed und nicht gecachte Entscheidung beim Ausfall der Authorization API)
real ausgeführt. Produktbäume und Nutzerdienste blieben unverändert.

## 1. Bindung

| Feld | Wert |
|---|---|
| Phase / Kandidat | `MA-F4` / `20261105T013710Z` |
| Handoff-SHA256 | `efc97d321ee9bb9e4acca32d8e16da6bf179f3106e04fc8a959db487dfadd435` |
| Spezifikations-SHA256 | `eb50e505bcf11b1fd9453af29dc29d15fe0275407d870e229632da7e58b84a15` |
| Request-SHA256 | `f66b88f775d45a61ea2193e9bf5623efc387691ef1e38005d31d1895109b5489` |
| Workspace-AGENTS-SHA256 | `21df33d38618ccd414f082c901f08b457adbd07551620f49e5455565d2c8ee4e` |
| Modell / CLI | `deepseek/deepseek-flash` / `opencode v2.2.5` |
| Session | `ses_e56a5a96dffe9h3IdApqIZweQ1` (aus `events.jsonl` dieses Laufs) |

Selbst nachgerechnet: Handoff-, Request-, alle vierzehn Spezifikationsdatei- und der
Workspace-AGENTS-Hash stimmen; der Aggregatswert reproduziert sich als
`sha256(json.dumps(files_sha256, sort_keys=True))` = `eb50e5…84a15`. Der laufende
Runner ist die Desktop-CLI
`…/ai.opencode.desktop/cli/2.2.5-arm64/opencode-cli run --standalone --agent
management-review --model deepseek/deepseek-flash` (Prozessliste dieses Laufs); das
unabhängig im PATH liegende `opencode` ist **nicht** die Runner-CLI.

Repositories exakt aus dem Handoff, vor und nach dem Review erneut geprüft
(`integrity-before.txt`, `integrity-after.txt`; alle Bäume clean):

| Repository | Base | HEAD |
|---|---|---|
| dateninfrastruktur-dev-stack | `cd9b551743585860f3998a40805e3b15ada1af8a` | `3990dab347a2b48a9a17c714eeb118928e07f259` |
| dateninfrastruktur-admin | `02eaa8a450c7e9d88bad6a01132f67bc98a37489` | `6009fb04063f16fcdb2ea6b3d9153e9553c9e4f1` |
| dateninfrastruktur-sodata | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` |
| dateninfrastruktur-jenkins-dev | `08931fa8254d096e2addcd3aee97bc1b753f087d` | `08931fa8254d096e2addcd3aee97bc1b753f087d` |
| dateninfrastruktur-jenkins-gretl-plugin | `579f3fd54432a977122afb186469fbb40d95322f` | `579f3fd54432a977122afb186469fbb40d95322f` |
| dateninfrastruktur-themenrepo | `6b0b635f066dc8de5000e3e549b983fb772dfb33` | `6b0b635f066dc8de5000e3e549b983fb772dfb33` |

## 2. Gelesener Diff und Umfang

Vollständig gelesen (`reviewed-diffs.txt`; Patch-Hashes
`fe1eb86b…399d9` für STACK, `96039b81…a0c695` für ADMIN):

- STACK `cd9b551…3990dab`: `scripts/test-consolidation.sh` (+MA-F4),
  `scripts/test_consolidation_f1.py` (Seed-Helfer: optionale `fixture_args` und
  `preserve_storage_config`, Defaultverhalten unverändert),
  `scripts/test_consolidation_f4.py` (neu), `F4_IMPLEMENTATION.md`, `MA-F4-request.md`.
- ADMIN `02eaa8a…6009fb0`: neue `ComposeAcceptanceIT`, kleine Fixture-Anpassung
  (Namespace-Präfix, idempotenter Operator-Principal) in `ManagedDownloadFixtureIT`.

Es gibt **keine** Änderung an Compose-Topologie, Gateway-/Originroute, Restore-,
Identitäts-, Schema- oder Fachlogik. Der Diff ist Prüf-/Fixture-/Dokumentationscode;
die Phasenverträge MA-A–E und F0–F3 sind dadurch nicht gefährdet (siehe Abschnitt 7).

## 3. Ausführungsumgebung und Isolation

Eigenes transientes Projekt `maf-f4-<random>` mit zufälligen freien Hostports,
eigenen benannten Volumes, privatem Runtimeverzeichnis und ausschliesslich
generierten Testcredentials. Keine Nutzer-`.env`, kein Nutzerdump, kein Zugriff auf
Nutzerdaten. Der Lauf baute die kanonischen Images aus den Kandidatenquellen und
startete genau die zehn Default-Services. Nach dem Lauf wurden Container, Netz,
Volumes, eigene Images und das private Runtimeverzeichnis des Reviewers entfernt
(`env-observations.txt`: 0 eigene Container/Volumes/Netze übrig).

Ein **Umgebungsartefakt** des isolierten Checkouts, kein Kandidatenfehler: der erste
Startversuch scheiterte, weil die Arbeitskopie alle Dateimodi verloren hatte
(0600/0700 statt 0644/0755) und Docker `COPY` diese Modi übernimmt; der
`superset`-Container konnte seine Config nicht lesen (`attempt1-note.txt`). Nach
Wiederherstellung checkout-äquivalenter Modi (nur Dateimodi, Inhalte/HEADs/git-Status
unverändert; `mode-normalization.txt`) lief der vollständige Pflichtlauf durch.

## 4. Pflichtprüfungen (alle frisch ausgeführt)

Ausgeführt über `python3 -u output/reviewer_f4_wrapper.py` (cwd
`…/workspace/dateninfrastruktur-dev-stack`), der exakt den Codepfad von
`./scripts/test-consolidation.sh --phase MA-F4` aufruft
(`test_consolidation_f4.run(fresh=True)`), ergänzt um die eigene Gegenprobe.
Log: `f4-fresh-run.log` (stdout), `f4-fresh-run.err` (leer). Exit 0 (kein Traceback,
Abschlusszeile nach Cleanup-Assertion).

| ID | Ergebnis | Kern der selbst beobachteten Wirkung |
|---|---|---|
| F17 | PASS | Echte PKCE-Code-Anmeldung über den normalen vertraulichen Client `management-gateway` (Testclient im Fixture deaktiviert); öffentlich sichtbare Metadatenänderung; Antrag (Anna) → Genehmigung (Claudia) → Download aktueller **und** historischer CSV/XLSX mit exaktem SHA256 → Widerruf genau dieses Grants → dasselbe, noch gültige JWT sofort 403 auf alle Dateien; Auditseite zeigt `save_published`/`approve`/`revoke`; separat neu erteilter Grant (Ben) bleibt positiv. |
| F18 | PASS | HEAD 200 ohne Body mit gleicher Content-Length, Range `bytes=2-7` → 206 mit exaktem Teilslice, `If-None-Match` → 304, unerfüllbarer Range → 416; gefälschte Identitäts-/Gateway-Header mit gültigem Token → 403; `/internal/authorization/check` öffentlich → 403; mehrdeutige Rohpfade (Query, `%70`, `%2e%2e`, Doppelslash, Extrasegment) → HTTP 400; Stop der Authorization API → 503, danach wieder 200; kurzlebiger Compose-Headerbeobachter hinter unveränderter OIDC/forward-auth-Kette sieht bei erfolgreicher, autorisierter Anfrage die exakten Bytes und **null** Credential-Headernamen; Routenbytes danach exakt wiederhergestellt. |
| F19 | PASS | Vor/Nach echter `down` (ohne `-v`) + `up --skip-build`: alle **zehn** Container mit neuen IDs; Management-Snapshot (Tabellen-, Audit-, Sequenz- und Sicherheits-/ACL-Hashes), Secrethash, Keycloak-Benutzer-UUIDs und ein eigens gesetzter deaktivierter Client (Attribut + Secret-Hash) identisch; Jenkins-Jobliste + Markerdatei, ClickHouse Schema-/Zeilenhash und die verschlüsselte Superset→ClickHouse-Verbindung unverändert; frisches OIDC-Login nach Recreate; widerrufenes Recht bleibt 403, aktives Recht bleibt 200; zusätzliche Metadatenänderung nach Recreate wird öffentlich sichtbar und die Auditsequenz läuft weiter. |
| F20 | PASS | Genau zehn laufende Defaultservices, je einmal, alle healthy; kein `container_name`, kein `network_mode`, keine Hostports für postgres/garage/origin/admin/sodata/jenkins, keine `.jar`-Mounts, nur die drei erwarteten Datenbanken; kein laufender Tool-/Beobachtercontainer am Ende; danach 0 Container/Volumes/Netze des Reviewprojekts. |

## 5. Eigene Gegenprobe

Hypothese: Nach erfolgreicher Autorisierung könnte der Gateway geschützte Bytes
während eines Ausfalls der Authorization API weiterliefern (fail-open oder gecachte
Entscheidung) und so einen unmittelbar zuvor ausgesprochenen Widerruf umgehen; dieselbe
gecachte Entscheidung könnte den Ausfall überleben.

Erwartung: vor dem Ausfall positiver Zugriff mit exakten Bytes und negativer Zugriff
für den widerrufenen Benutzer; während des Ausfalls 503 **ohne** Dateibytes für
berechtigten, widerrufenen, anonymen und offenen Zugriff; nach Wiederanlauf erneut
200 exakt für den Berechtigten und 403 für den Widerrufenen (GET und HEAD) — also eine
lebende, nicht gecachte Entscheidung.

Beobachtet: `{anonymous:[503,269,false], granted_ben:[503,269,false],
revoked_anna:[503,269,false], open_file:[503,269,false]}` (Status, Bodylänge,
Body==geschützte Bytes) und danach 200/403 wie erwartet. **PASS**, keine Offenlegung
und kein Cache-Bypass. Details: `counterexample.txt`, Rohbeleg `f4-fresh-run.log`
Zeilen 9–13.

## 6. Findings / Beobachtungen

Unverändert gegenüber dem ursprünglichen Urteil, nur als Objekte mit `severity`/`message` ausgegeben (Anforderung des Maschinen-Gates; keine inhaltliche Änderung):

```json
{
  "severity": "INFO",
  "message": "INFO: Der kandidateneigene Ausfalltest (security_delta) prüft nur die offene Datei; die kritischere Kombination berechtigt/widerrufen/anonym während des Ausfalls war nicht Teil des Kandidatentests. Die eigene Gegenprobe hat sie ausgeführt und bestanden; F18 ist damit belegt (kein Vertragsverstoss)."
}
```

```json
{
  "severity": "INFO",
  "message": "INFO: f4-accepted-local.json notiert observer_removed=true, während der Code den Beobachtercontainer zu diesem Zeitpunkt nur stoppt; entfernt wird er durch den Projekt-Cleanup. Der geprüfte Vertrag (kein laufender Tool-/Beobachtercontainer) ist erfüllt; keine Betriebsauswirkung."
}
```

```json
{
  "severity": "INFO",
  "message": "INFO (Umgebung, kein Kandidatenfehler): Der erste Startversuch scheiterte an verlorenen Dateimodi der isolierten Arbeitskopie (0600/0700 statt 0644/0755, Docker COPY erhält sie); nach Wiederherstellung checkout-äquivalenter Modi lief der Pflichtlauf vollständig durch. Inhalte/HEADs/git-Status unverändert."
}
```

Keine BLOCKER/MAJOR/MINOR-Findings.
## 7. Nicht erneut ausgeführte, begründet nicht betroffene Nachweise

F01–F03 und F04–F16 (Phase MA-F0 bis MA-F3) sowie die funktionalen MA-A–E-Suiten
wurden **nicht** wiederholt: der neue Diff enthält ausschliesslich Prüf-, Fixture- und
Dokumentationsdateien (kein Compose-, Gateway-, Restore-, Identitäts-, Schema- oder
Fachcode). Die einzige Änderung an einem bestehenden Testhelfer (`seed()` in
`test_consolidation_f1.py`) ist rückwärtskompatibel (optionale Argumente, bisheriges
Defaultverhalten unverändert). Frühere Abnahmen sind an den Base-SHAs dieses Handoffs
gebunden. Es wurden **keine** Belege übernommen (`carried_evidence: []`).

## 8. Produktintegrität

Vor und nach dem Review geprüft: alle sechs Repositories auf den exakten
Handoff-HEADs, `git status --porcelain` leer, kein getrackter Diff, keine
Modusänderung an getrackten Dateien (Git-Execbit unverändert). Buildartefakte
entstanden nur in ignorierten Pfaden (`.runtime/`, `dateninfrastruktur-admin/.gradle/`,
`dateninfrastruktur-admin/build/`). Workspace-AGENTS-Hash unverändert.

Die Nutzerinstanz wurde nicht berührt: die zehn Container des Projekts
`dateninfrastruktur` laufen unverändert mit ihren Startzeiten von 01:30 UTC (vor
Beginn dieses Reviews) und RestartCount 0; die Legacy-Container sind bereits vor dem
Review gestoppt (read-only beobachtet, `env-observations.txt`).

## 9. Abgrenzung zum realen Cutover

Dieses Review bescheinigt den **Code-/Teststand** der Phase MA-F4. Es ersetzt
ausdrücklich nicht den vollständigen konkreten Fachpfad am realen Ziel:
`WORK_QUEUE.md` und `F4_IMPLEMENTATION.md` weisen den Livezustand weiterhin als
`LOCAL_CUTOVER_PENDING` aus; Retire und `LOCAL_CUTOVER_VERIFIED` bleiben getrennt
nachzuweisen. Die read-only Beobachtung „zehn gesunde Zielservices, keine aktiven
Legacy-Duplikate“ stützt, ersetzt aber keinen solchen Nachweis.

## 10. Urteil

**ABGENOMMEN** für Kandidat `20261105T013710Z` (F17–F20 frisch ausgeführt, eigene
Gegenprobe bestanden, Produktbestand unverändert, exakte Bindung an den Handoff).
