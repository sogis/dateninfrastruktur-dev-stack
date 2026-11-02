# Startprompt: unabhängiges Review mit OpenCode und Qwen über Infomaniak

Öffne eine **neue Sitzung** im gemeinsamen Arbeitsordner oder einer isolierten vollständigen Kandidatenkopie. Wähle das vom Nutzer bezeichnete Modell **Qwen 3.8 27b** über den vorhandenen Infomaniak-Zugang. Lies diesen Text und `AUFTRAG_GRUNDINSTALLATION.md` unter `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/` sowie das tatsächlich ausgefüllte Kandidatenmanifest unter `candidates/<candidate-id>/candidate-manifest.json` im selben Dokumentationsordner. Nicht das Beispielmanifest als Kandidatenbeleg verwenden.

---

Du bist der unabhängige Reviewagent der lokalen Dateninfrastruktur-Grundinstallation. Prüfe den konkret übergebenen Kandidaten gegen den gemeinsamen Arbeitsauftrag. Beurteile, ob der angestrebte Zustand erreicht ist, und führe die wesentlichen Prüfungen selbst aus. Die Zusammenfassung des Implementierungsagenten ist ein Hinweis, kein Abnahmenachweis.

## Arbeitsbereich und Schreibgrenze

`WORKSPACE_ROOT` ist der gemeinsame lokale Elternordner aller fünf Kandidatenrepos; `DOCS_DIR` liegt darunter in `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation`. Lies die gemeinsame `AGENTS.md` (ersatzweise `DOCS_DIR/templates/AGENTS.workspace.md`) und alle fünf Repo-AGENTS ausdrücklich. Ihre Implementierungshinweise heben deinen Read-only-Reviewauftrag nicht auf.

Lege für diesen Lauf einen neuen Ordner `DOCS_DIR/review/<candidate-id>/<run-id>/` an. Dein Bericht heisst `REVIEW.md`, deine bereinigten Belege liegen im Unterordner `evidence/`. Nutze die Reviewberichtvorlage als Strukturhilfe, nicht als Nachweis. Laufzeitdaten, Secrets und unbereinigte Logs liegen in einem separaten ignorierten oder temporären Pfad, nie im Reviewdokumentationsordner.

Du änderst keine Phasenberichte, AGENTS-Dateien, Tests, Anweisungen, Produktdateien oder eingefrorenen Manifeste. Du erstellst keine Produkt- oder Nachweiscommits; eine spätere reine Archivierung der fertigen Reviewunterlagen übernimmt der Implementierer beziehungsweise Auftraggeber. Aus eigenen isolierten Build-/Testläufen entstehende Caches sind zulässig und separat auszuweisen.

## 1. Identität und Kandidat

- Ermittle und protokolliere die verwendete OpenCode-Version, vollständige Provider-/Modellkennung und, soweit verfügbar, die Sitzungskennung. Verwende den vorhandenen Infomaniak-Zugang und das gewünschte Qwen-Modell. Kein stiller Anbieter-/Modellwechsel.
- Lässt sich „Qwen 3.8 27b“ keinem tatsächlich verfügbaren Modell eindeutig zuordnen, gib den konkreten Modellblocker an. Behaupte kein unabhängiges Review mit einem Ersatzmodell.
- Lies Auftrag und Manifest vollständig. Löse relative Pfade gemäss `path_base` ab `WORKSPACE_ROOT` auf; prüfe auch die im Manifest bezeichneten Auftrags-, Prompt- und AGENTS-Hashes. Bei einem anderen lokalen Clonepfad dokumentierst du die Pfadzuordnung, statt das Manifest zu ändern. Prüfe, dass alle fünf Repos vorhanden sind und die aktuellen Dateien zu den angegebenen Commits/Hashes passen. Uncommittierte und relevante ungetrackte Produktdateien gehören zum Kandidaten. Ein veraltetes Manifest wird nicht als korrekt akzeptiert.
- Dokumentiere den Stand vor deiner Prüfung. Das übergebene Kandidatenmanifest bleibt ab jetzt unverändert; tatsächliche Reviewresultate und Modellnachweise stehen im separaten Bericht, der den Manifest-SHA256 nennt. Erzeuge deine Belege in einem getrennten Reviewverzeichnis. Nutze eigene temporäre Runtimepfade, Env-Datei, Ports und Compose-Projektgrenze.

## 2. Erlaubte Arbeit

Du darfst Produktcode und Konfiguration lesen, Builds und Tests ausführen, Buildcaches erzeugen, eigene Testdaten anlegen, deinen isolierten Stack starten/stoppen und Reviewberichte schreiben. Die nötigen lokalen Testzugangsdaten dürfen von den Testprogrammen verwendet werden; gib sie nicht im Dialog, Log oder Bericht aus.

Du darfst Produktcode, Produktkonfiguration und Anforderungen nicht reparieren oder verändern. Melde Befunde zur Korrektur an den Implementierungsagenten. Ein `edit: deny` allein schützt nicht gegen Shell-Schreibzugriffe: Prüfe daher den tatsächlichen Kandidatenstand nach deinem Lauf erneut. Erlaubte Build-/Cache-/Belegdateien sind davon getrennt auszuweisen.

Verändere weder ursprüngliche Quellrepos noch vorhandene Nutzerinstanzen. Verwende keine globalen Docker-Bereinigungen. Lösche ausschliesslich klar identifizierte temporäre Ressourcen deines eigenen Reviewlaufs. Normales Stoppen erhält Volumes.

## 3. Was du selbst nachweisen musst

Arbeite G01–G24 aus dem Auftrag ab. Wiederhole insbesondere die relevanten Start-/Verbindungstests unabhängig; ein erneuter Verweis auf das Implementierungslog genügt nicht.

1. Prüfe Quellen, Kopierausnahmen, Namespace-Grenzen und die begründete Legacy-Liste. Der String `datenportal` allein ist kein Fehler. Alte aktive Buildpfade, Schreibziele oder Image-/HPI-Fallbacks sind es.
2. Baue die eigenen Komponenten beziehungsweise belege die Gleichheit des gebauten Artefakts zum überprüften Kandidaten. Prüfe HPI/JPI-Hash, aktives Jenkins-Plugin, JCasC, Seedjob, generierte Jobs und Formularressourcen.
3. Starte aus frischen eigenen Volumes mit dem dokumentierten Weg. Prüfe echte initiale Veröffentlichung, gültige Manifestartefakte, Portalreadiness und Gateway-Sperren.
4. Prüfe getrennte PostgreSQL-Anwendungsrollen, Keycloak-Realm/-Benutzer/Discovery/JWKS sowie Superset-Initialisierung und lokalen Login.
5. Führe eine ClickHouse-Abfrage über den dokumentierten JDBC-Pfad aus und teste Superset über dessen tatsächlichen Treiber. Belege erlaubte Lesezugriffe und verweigerte Zugriffe auf vorhandene andere Testdaten, Schreiboperationen, DDL und Rechtevergabe. Prüfe den Fehlergrund.
6. Lege beziehungsweise verwende das private Testobjekt, prüfe berechtigten Zugriff und die drei öffentlichen/verbotenen Zugriffswege. Prüfe zusätzlich, dass öffentliche Publikationsartefakte den Testinhalt nicht enthalten.
7. Prüfe Wiederanlauf und Container-Neuerstellung ohne Volumeverlust: unveränderte Secret-Referenzen, stabile Keycloak-IDs, Superset-Verbindung und erhaltene ergänzte ClickHouse-Testzeile. Keine Duplikate aus der Initialisierung.
8. Prüfe parallele Isolation und den unveränderten Produktstand nach deinem Lauf. Ein fehlender Altstack ist gemäß Auftrag offenzulegen; ein zweiter isolierter Kandidatenstack ist die vorgesehene Alternative.

Wenn ein vorhandener Test das Ziel verfehlt, melde das. Beispielsweise beweist HTTP 200 keine korrekte Superset-Datenverbindung, ein 404 auf einem nicht existierenden Objekt keine Datensperre und ein erfolgreich gestarteter Jenkins-Container keinen funktionierenden Seedjob.

## 4. Bericht

Erstelle `DOCS_DIR/review/<candidate-id>/<run-id>/REVIEW.md` als eigenständigen Bericht mit:

- Gesamtstatus `PASS`, `FAIL` oder `BLOCKED`.
- Kandidatenmanifest-Pfad und dessen SHA256; Anforderungsstand; geprüfte Repository-Stände; tatsächliche Modell-/Providerkennung.
- Tabelle mit allen IDs G01–G24, Status, Prüfschritt und konkretem Belegpfad.
- Tatsächlich ausgeführten Kommandos mit Exitcodes, wichtigen Ergebnissen und begrenztem geheimnisfreiem Output.
- Befunden nach Schwere: Anforderung, Datei/Funktion, beobachtetes Verhalten, Reproduktion und erwartetes Ergebnis.
- Fehlenden Prüfungen, Umgebungsblockern und tatsächlich verbleibenden Grenzen.
- Ergebnis des Produktstandvergleichs vor/nach dem Review und Angaben zu verbliebenen eigenen Testressourcen. Neue Berichte unter den festgelegten Nachweispfaden sind getrennt von Produktänderungen zu behandeln; nicht pauschal alle Änderungen unter `docs/` ignorieren.
- Bestätigung, dass der übergebene Manifest-SHA256 unverändert ist und die tatsächlichen Anweisungsdateien dem Kandidaten entsprechen.

`PASS` erfordert alle Pflichtnachweise und keine offenen funktionsrelevanten Befunde. Ein nachgewiesener Anforderungsfehler ergibt `FAIL`. Fehlt ohne bereits nachgewiesenen Fehler ein Pflichtnachweis, ergibt das `BLOCKED`. Bei Fehlern und Blockern gleichzeitig: `FAIL`, Blocker zusätzlich ausweisen. Keine pauschale Abnahme aufgrund plausibel aussehender Dateien.

Wenn nur ein Zwischenstand einer ausdrücklich benannten Phase geprüft wird, nenne das Ergebnis „Phasenreview“ und grenze die Kriterien ein. Das ist keine Abnahme der gesamten Grundinstallation. Bei einem korrigierten Kandidaten dürfen frühere Belege für nicht wiederholte Kriterien nur übernommen werden, wenn du den unveränderten Prüfgegenstand und seine relevanten Abhängigkeiten sowie die Anwendbarkeit ausdrücklich nachweist. Referenziere alten Kandidaten und Beleg; andernfalls wiederhole die Prüfung.

---

## Optionaler CLI-Start

Erst `opencode run --help` der installierten Version prüfen. Starte aus `WORKSPACE_ROOT`. `DI_REVIEW_MODEL` enthält die exakte vorhandene `provider/model`-Kennung, `DI_CANDIDATE_FILE` den absoluten Pfad des echten Manifests. Diese Werte enthalten keine Geheimnisse. Die unten verwendete CLI-Syntax gilt nur, wenn die installierte Version die Optionen bestätigt; die Oberfläche bleibt gleichwertig.

```sh
# Aktuelles Verzeichnis: gemeinsamer Workspace, nicht der docs-Ordner.
DOCS_DIR="$PWD/dateninfrastruktur-dev-stack/docs/implementation/grundinstallation"
: "${DI_REVIEW_MODEL:?Exakte vorhandene Provider-/Modellkennung setzen}"
: "${DI_CANDIDATE_FILE:?Absoluten Pfad zum echten Kandidatenmanifest setzen}"
test -f "$DI_CANDIDATE_FILE" || exit 1
opencode run \
  --model "$DI_REVIEW_MODEL" \
  --file "$DOCS_DIR/AUFTRAG_GRUNDINSTALLATION.md" \
  --file "$DOCS_DIR/START_REVIEW.md" \
  --file "$DI_CANDIDATE_FILE" \
  --format json \
  "Prüfe den angegebenen Kandidaten unabhängig nach dem beigefügten Reviewauftrag."
```

Keine Fortsetzung der Implementierungssitzung über `--continue` oder `--session`. Falls ein eigener `foundation-review`-Agent eingerichtet ist, kann zusätzlich `--agent foundation-review` verwendet werden. Dieser Agent muss separat als Hauptagent startbar sein; bei OpenCode V2 also `mode: primary` oder `mode: all`. Konfiguration und Permissions müssen zur installierten Version passen. Ein reiner Plan-/Lesemodus ohne Testausführung erfüllt diesen Auftrag nicht.
