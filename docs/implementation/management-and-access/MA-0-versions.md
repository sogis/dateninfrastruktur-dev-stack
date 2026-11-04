# MA-0: Bestand und Versionsentscheidungen

Erhebung 4. November 2026, macOS arm64, Temurin25.0.2.

| Repository | Ausgangs-HEAD | Ausgangszustand |
|---|---|---|
| STACK | `8b75fc562039b634da7a917fea22d672bbb3a1d7` | getrackte Dateien sauber; unversionierte historische candidates/review erhalten |
| PUBLIC | `7eff0b138c23524ac522231ce312d4c6659635dc` | sauber |
| ADMIN | nicht vorhanden | sicher neu initialisiert; kein Remote konfiguriert, kein Push |
| TOPICS | `7d99ceec0e392a5f12b602c0840c4762c7213fba` | sauber, unverändert |
| Jenkins-Dev | `08931fa8254d096e2addcd3aee97bc1b753f087d` | sauber, unverändert |
| Jenkins-Plugin | `579f3fd54432a977122afb186469fbb40d95322f` | sauber, unverändert |

Bestehende Remotes der fünf vorhandenen Repos sind die entsprechenden
`sogis/dateninfrastruktur-*`-GitHub-Repositories. Der gemeinsame Elternordner
ist weiterhin kein Git-Repository. Root-AGENTS passt bereits zum Auftrag.
Nur STACK-/PUBLIC-AGENTS wurden gezielt um aktive Phasengrenzen ergänzt.

## Geprüfte Versionen

- Spring Boot4.1.2: [offizielle GA-Meldung](https://spring.io/blog/2026/10/23/spring-boot-4-1-2-available-now/) und Maven-Central-Metadaten geprüft.4.2.0-RC1 ist Preview, keine neuere GA. Genau4.1.2 gepinnt; bestehendes Sodata noch unverändert4.1.0 bis zu seinem betroffenen Phasenvertrag.
- Apache Cayenne5.0-M3: [Apache Downloads](https://cayenne.apache.org/download/), als Alpha/Milestone veröffentlicht. Reales Artefakt `org.apache.cayenne:cayenne:5.0-M3` aufgelöst; Java25, vorhandener Gradle9.5.1-Wrapper. Keine4.2-Rezepte oder Hibernateabhängigkeit.
- INTERLIS-Tools aus offiziellen Release-JSONs: ili2pg5.5.2 (enthält ili2c5.6.8), separater ili2c5.6.9, ilivalidator1.15.0. URLs/Archive-SHA256 in ADMIN/db/toolchain.json. Keine Behauptung, Compiler-/Validatorpflichten aus MA-A seien bereits erfüllt.
- PostgreSQL16: isolierte Probe zeigt, dass ili2pg5.5.2 auch geometriefrei `postgis_full_version()` aufruft. Vanilla16.10 scheitert reproduzierbar vor Schemaerzeugung. Management bekommt deshalb einen eigenen nativen PG16/PostGIS-Service; kein Austausch bestehender Nutzerinstanzen/Volumes. Spikeimage `ghcr.io/baosystems/postgis:16-3.5`, Manifestdigest `sha256:0f1c5c0f70f03d4d19ad1d7308d86e6162dff5429c491002298a7b5e46d2f2e8`; arm64 ist im Manifest vorhanden. Endgültiger Betriebsdienst folgt MA-B.
- Nutzerstack bleibt bei APISIX3.19.0-debian, Keycloak26.8.1, Garage2.4.1, rclone1.75.2 und vorhandenen Ressourcen. Keine neue Gateway-/OIDC-Funktion in MA-0 behauptet.

## Reale Reviewkette

PATH enthält OpenCode1.18.22, zusätzlich liegt1.15.10 unter `~/.opencode/bin`.
Die vorhandene Desktopinstallation enthält dagegen die verwendbare native CLI
`~/Library/Application Support/ai.opencode.desktop/cli/2.2.5-arm64/opencode-cli`.
Sie meldet `opencode v2.2.5`; ihre echte `run --help` unterstützt
`--standalone`, `--agent`, `--model`, `--format json`. Keine globale Änderung.
`DI_OPENCODE` kann einen anderen tatsächlich installierten2.x-Pfad bezeichnen;
1.x wird strikt abgelehnt.

Die vorhandene DeepSeek-Authentifizierung wird unverändert verwendet, keine
Secrets ausgelesen, kopiert oder neu als Pflicht-ENV verlangt. Modellliste und
[offizieller DeepSeek-Aliasvertrag](https://api-docs.deepseek.com/quick_start/agent_integrations/)
belegen `deepseek/deepseek-flash` → DeepSeek-V4.1-Flash-1017. Kein Go-/Free-Alias.
Ein frischer Toolsmoke hat Datei-Lesen und Shellassertion tatsächlich ausgeführt;
das ist ausdrücklich keine MA-0-Abnahme. Runner prüft zusätzlich das Modell aus
dem bereinigten tatsächlichen Sessionexport.

Es gibt lokal keinen `scripts/step2/review-phase.sh` oder gleichwertigen
versionierten autonomen Runner. Daher kleiner neuer Runner unter
`scripts/management/`. Agent nutzt geprüfte2.x-Regellisten (`permissions`,
`action: shell`, `effect`, `mode: primary`), keine V1-Konfiguration.
Shellrechte sind kein OS-Schreibschutz; Produktdateihashes und Gitstatus werden
vor/nach verglichen, Originalrepos ebenfalls überwacht. Frische lokale Clones
enthalten keine Original-`.env` oder ignorierten Nutzerlaufzeitdaten.

## Reproduzierbare Kommandos

Aus STACK: `./scripts/management/preflight.sh`,
`python3 scripts/management/test_review_gate.py` und nach Produktcommit
`./scripts/management/review-phase.sh MA-0`.
Aus ADMIN: `python3 scripts/compatibility.py`.

Nur der Runner darf bei validiertem unabhängigem Bericht `ACCEPTED.json`
erzeugen. Der Produktcommit ist nicht sein eigener Nachweis. Bei fehlendem
Report, Modell-/SHA-Fehler, skippten Pflichtchecks oder fehlender Gegenprobe
bleibt das Gate geschlossen. Rohlogs liegen ausschliesslich unter ignoriertem
`.runtime/management-review/MA-0/`. Kein neuer allgemeiner Foundationlauf.
