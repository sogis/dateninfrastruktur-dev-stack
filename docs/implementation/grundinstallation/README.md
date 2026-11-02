# Dateninfrastruktur: Auftrag für die Grundinstallation

Stand: 2. November 2026. Dokumentpaket v2 / Auftragsrevision 1.1. Dieses Paket ist ein Arbeitsauftrag für OpenCode. Es enthält noch keine implementierte oder gestartete Infrastruktur.

## Ziel

Eine eigenständige lokale Entwicklungsumgebung in fünf neuen `dateninfrastruktur-*`-Repositories. Die brauchbaren Teile des bestehenden Datenportals werden aus dokumentierten Quellständen kopiert und gezielt angepasst. ClickHouse, Keycloak, PostgreSQL und Superset ergänzen den übernommenen Kern.

Der erste erreichbare Zustand ist ein startbarer, überprüfter technischer Unterbau: Portal mit gültiger initialer Veröffentlichung, Jenkins/GRETL, Objektspeicher, Identitätsdienst, SQL-Zugang und BI-Verbindung. Den Freigabeprozess und die fachliche Datenpipeline bauen wir anschliessend darauf auf.

## Ablage und Einstieg

Diese README gehört nach **`dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/README.md`**, nicht ins Root des Dev-Stack-Repos. Dort liegt später die Betriebsanleitung des implementierten Stacks.

Das ZIP enthält unter `workspace/` bereits die passende Zielstruktur: `AGENTS.md` im gemeinsamen Elternordner, je eine `AGENTS.md` in den fünf Zielrepos und diesen Dokumentationsordner. Kopiere die Dateien in deinen vorhandenen gemeinsamen Arbeitsordner. Lege keinen zusätzlichen `workspace/workspace`-Ordner an. Vorhandene gleichnamige Dateien vergleichen und gezielt zusammenführen; weder komplette Repos ersetzen noch Verzeichnisse löschen.

Die fünf Repos bleiben unabhängig. Die gemeinsame AGENTS-Datei ausserhalb ihrer Git-Grenzen wird zusätzlich als [versionierbare Vorlage](templates/AGENTS.workspace.md) im Dev-Stack geführt. Die konkreten Repo-AGENTS werden jeweils in ihrem Repo versioniert. Der gemeinsame Arbeitsordner benötigt keine eigene `.git`.

Öffne in OpenCode vorzugsweise den gemeinsamen Elternordner. Bei Start in einem einzelnen Repo muss der Zugriff auf die Schwesterrepos ausdrücklich möglich sein. Beide Startprompts verlangen, die gemeinsamen Regeln, den Auftrag und die Repo-Anweisungen tatsächlich zu lesen. Eine erfolgreiche automatische Regelerkennung wird nicht einfach vorausgesetzt.

## Dateien und Verwendung

| Datei | Zweck |
|---|---|
| [AUFTRAG_GRUNDINSTALLATION.md](AUFTRAG_GRUNDINSTALLATION.md) | Gemeinsame Anforderungen, Kopierregeln, Komponenten, Phasen und Abnahmekriterien |
| [START_IMPLEMENTIERUNG.md](START_IMPLEMENTIERUNG.md) | Startprompt für DeepSeek Flash über die DeepSeek-API |
| [START_REVIEW.md](START_REVIEW.md) | Unabhängiger Prüfauftrag für Qwen 3.8 27b über die Infomaniak-API |
| [candidate-manifest.example.json](candidate-manifest.example.json) | Schema-v2-Beispiel mit Ablagepfaden und Anweisungsdateien; kein fertiger Kandidat |
| [templates/PHASENBERICHT.template.md](templates/PHASENBERICHT.template.md) | Struktur für die Implementierungsberichte P0 bis P3 |
| [templates/REVIEWBERICHT.template.md](templates/REVIEWBERICHT.template.md) | Struktur für einen unabhängigen Reviewbericht mit G01–G24 |
| [AENDERUNGEN.md](AENDERUNGEN.md) | Änderungen gegenüber dem vorherigen Auftragspaket |

1. Lege die fünf Zielrepos als Geschwisterverzeichnisse an oder lass den Implementierungsagenten sie lokal initialisieren. Lege Auftrags- und AGENTS-Dateien gemäss Abschnitt 0 des Auftrags ab; auch noch nicht implementierte Zielrepos können diese Dateien schon enthalten. Bereits vorhandene Inhalte bleiben erhalten. Die GitHub-Repos kannst du wie vorgesehen selbst erstellen; ein Push ist für diesen Auftrag nicht erforderlich.
2. Öffne den gemeinsamen Arbeitsbereich in OpenCode. Stelle das vorhandene DeepSeek-Flash-Modell über die DeepSeek-API ein. Füge den gemeinsamen Auftrag und den Implementierungsprompt bei.
3. Der Agent erstellt die Grundinstallation in den beschriebenen Phasen. Er schreibt `reports/P0.md` bis `P3.md`, führt Prüfungen aus und legt ein echtes Kandidatenmanifest unter `candidates/<candidate-id>/candidate-manifest.json` ab. Zwischenstände sind prüfbar; es braucht keine neue fachliche Freigabe für jeden gewöhnlichen Arbeitsschritt.
4. Öffne für das Review eine neue OpenCode-Sitzung. Wähle ausdrücklich das gewünschte Qwen-Modell über Infomaniak. Übergib den gemeinsamen Auftrag, den Reviewprompt und das tatsächliche Kandidatenmanifest. Der Reviewer braucht Zugriff auf alle fünf Zielrepos. Sein eigener Bericht liegt unter `review/<candidate-id>/<run-id>/REVIEW.md`; er ändert keine Produktdateien und repariert keine Befunde.
5. Der Reviewer führt die Abnahme selbst aus und liefert `PASS`, `FAIL` oder `BLOCKED`. Bei Befunden korrigiert DeepSeek; Qwen prüft den neuen Kandidaten. Die Implementierung gilt erst nach diesem unabhängigen Abschlussreview als abgenommen.

Das Review kann zusätzlich nach Phase 1 und Phase 2 erfolgen. Ein Abschlussreview ist Pflicht. Bei automatischer Orchestrierung müssen die getrennte Sitzung, das tatsächlich verwendete Qwen-Modell und der geprüfte Kandidat nachweisbar sein. Ein zweiter Prompt an dasselbe Implementierungsmodell ersetzt dieses Review nicht.

## Welche Funktion hat AGENTS.md?

AGENTS.md enthält dauerhafte Hinweise zum jeweiligen Arbeitsbereich, nicht die vollständige Spezifikation und nicht einen zweiten Startprompt. Die gemeinsamen Regeln nennen Umfang, Quellen-/Zielgrenzen und den zentralen Auftrag. Die Repo-Regeln enthalten nur Ergänzungen für Stack, Portal, Jenkins-Runtime, Jenkins-Plugin beziehungsweise Themenrepo.

OpenCode V2 dokumentiert das Laden von AGENTS-Dateien abhängig von Workspace, Projektgrenzen und gelesenen Unterverzeichnissen. Die Dateien werden kombiniert; Konflikte werden nicht automatisch aufgelöst. Deshalb sind die Hinweise hier rollenverträglich formuliert, und die Startprompts verlangen zusätzlich das ausdrückliche Lesen. Nach Änderungen an bereits geladenen verschachtelten AGENTS-Dateien eine neue Sitzung starten. [Primärquelle: OpenCode V2 Instructions](https://opencode.ai/v2/docs/instructions/)

AGENTS.md ist weder Modellkonfiguration noch Zugriffssandbox. DeepSeek beziehungsweise Qwen wird in der jeweiligen Sitzung gewählt. Ein Review bleibt ein eigener Auftrag ohne Produktänderungen. Dieses Paket ersetzt keine globale OpenCode-Konfiguration und verlangt keine neuen API-Key-Variablen.

## Berichte versionieren, Prüfgegenstand unverändert halten

Phasenberichte und bereinigte Implementierungsbelege werden vor dem Handoff mit dem Produktstand festgeschrieben. Das Manifest entsteht anschliessend unter `candidates/<candidate-id>/`. Der Reviewer erzeugt eigene Unterlagen unter `review/<candidate-id>/<run-id>/`. Nach dem abgeschlossenen Review können diese beiden Nachweisbereiche separat im Dev-Stack versioniert werden. Das Manifest referenziert weiterhin den geprüften, vorherigen Produktstand, nicht den späteren Nachweiscommit. Genauere Regeln stehen in Abschnitt 8.1 des Auftrags.

Laufzeitdaten und unbereinigte Logs bleiben in ignorierten oder temporären Pfaden. Keine Secrets, Zugangsdaten oder Secret-Hashes unter `docs/` ablegen.

## Modellwahl und vorhandene Anmeldung

Die Installation des Nutzers wird verwendet. Keine globale OpenCode-Konfiguration ersetzen und keine gespeicherten Accounts exportieren. Eine neue API-Key-Umgebungsvariable ist keine Voraussetzung, wenn der Zugang bereits funktioniert.

Die offizielle DeepSeek-API führt derzeit `deepseek-flash`. Für OpenCode ist zusätzlich der tatsächliche lokale Provider-Schlüssel erforderlich. Die genaue Infomaniak-Modellkennung hinter der Benutzerbezeichnung **„Qwen 3.8 27b“** muss aus der vorhandenen Modellauswahl oder der Modellliste des konkreten AI-Produkts ermittelt werden. Dieses Paket erfindet dafür keine Kennung. Wenn die Zuordnung nicht gelingt, bleibt das Review offen; es wird kein anderes Modell ausgewählt.

Die OpenCode-Oberfläche genügt. CLI-Aufrufe sind eine Alternative, deren Optionen zuerst gegen die installierte Version zu prüfen sind:

```sh
opencode --version
opencode run --help
opencode models --help
```

Nach Auflösung der vollständigen `provider/model`-Kennung kann der Implementierungsaufruf beispielsweise so aussehen:

```sh
# Aktuelles Verzeichnis: gemeinsamer Workspace.
DOCS_DIR="$PWD/dateninfrastruktur-dev-stack/docs/implementation/grundinstallation"
: "${DI_IMPLEMENT_MODEL:?Exakte vorhandene Provider-/Modellkennung setzen}"
opencode run \
  --model "$DI_IMPLEMENT_MODEL" \
  --file "$DOCS_DIR/AUFTRAG_GRUNDINSTALLATION.md" \
  --file "$DOCS_DIR/START_IMPLEMENTIERUNG.md" \
  "Setze die beschriebene Grundinstallation vollständig um."
```

`DI_IMPLEMENT_MODEL` ist nur die Modellkennung, kein API-Schlüssel. Ein entsprechender Reviewaufruf steht in [START_REVIEW.md](START_REVIEW.md). Eine fehlende Variable darf nicht zu einer unbeabsichtigten Standardmodellwahl führen: Modell vor dem Start prüfen.

V1 und V2 von OpenCode verwenden unterschiedliche Konfigurationsfelder. Eine zusätzliche Agentendefinition ist optional und wird erst nach Versionsprüfung projektlokal erstellt. Kein pauschales Rezept zum Abschalten aller Berechtigungsprüfungen verwenden.

## Was bei Jenkins in den neuen Namespace kommt

Es gibt in der geprüften Abhängigkeitskette **ein projektspezifisches Jenkins-Plugin**: `datenportal-jenkins-gretl-plugin`. Es wird nach `dateninfrastruktur-jenkins-gretl-plugin` kopiert. Dazu kommen das Image-/Runtime-Repo `dateninfrastruktur-jenkins-dev` und das benötigte `dateninfrastruktur-themenrepo`.

Die üblichen Jenkins-Plugins werden weiterhin als unveränderte Abhängigkeiten installiert. Die bestehende versionierte `plugins.txt` wird zunächst vollständig übernommen. GRETL selbst ist eine zusätzliche Gradle-Abhängigkeit; dafür ist kein Jenkins-Plugin-Fork nötig.

**Besonders wichtig:** Im geprüften Jenkins-Runtime-Quellrepo liegt auch ein versioniertes `jenkins-home/`. Dieses Verzeichnis wird vollständig vom Kopieren ausgeschlossen, einschliesslich seiner Git-Historie im neuen Zielrepo. Die neue Instanz erhält ein frisches eigenes Volume.

## Grenzen dieses Pakets

Der Auftrag beschreibt eine lokale Grundinstallation. Sodata erhält dabei noch keinen neuen Benutzerlogin. Keycloak wird eingerichtet, aber noch nicht mit Portal, Superset oder ClickHouse verbunden. Superset verwendet zunächst einen lokalen Administrator und einen eingeschränkten technischen ClickHouse-Zugang. Der spätere Berechtigungsprozess, AIO-Anbindung, personenbezogene SQL-Konten, Dashboard-Fachlichkeit und CSV-Import nach ClickHouse werden nicht vorweggenommen.

Alle Ergebnisse und Tests der späteren Implementierung müssen im Kandidatenmanifest und Reviewbericht tatsächlich belegt werden. Die Quellenanalyse, auf der dieses Paket beruht, ersetzt diese Laufzeitprüfung nicht.

## Quellen für die Bedienung

- [OpenCode CLI](https://opencode.ai/v2/docs/cli/commands/)
- [OpenCode Agenten](https://opencode.ai/v2/docs/agents/)
- [OpenCode Berechtigungen](https://opencode.ai/v2/docs/permissions/)
- [DeepSeek API](https://api-docs.deepseek.com/)
- [Infomaniak: Modelle eines AI-Produkts](https://developer.infomaniak.com/docs/api/get/2/ai/%7Bproduct_id%7D/openai/v1/models)
