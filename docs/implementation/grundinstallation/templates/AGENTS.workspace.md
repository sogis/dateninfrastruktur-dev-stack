# AGENTS.md – Dateninfrastruktur-Arbeitsbereich

## Geltung und Einstieg

Dieser Arbeitsbereich enthält fünf eigenständige Zielrepos: `dateninfrastruktur-dev-stack`, `dateninfrastruktur-sodata`, `dateninfrastruktur-jenkins-dev`, `dateninfrastruktur-jenkins-gretl-plugin` und `dateninfrastruktur-themenrepo`. Nur diese sind Produktziele dieses Auftrags. Der gemeinsame Elternordner ist kein neues Git-Repo. Vorhandene `datenportal-*`-Repos sind nur Quellen und bleiben unverändert.

Lies zu Beginn ausdrücklich diese Dateien; Links sind Leseaufträge, kein Nachweis, dass Inhalte bereits geladen wurden:

1. `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/AUFTRAG_GRUNDINSTALLATION.md` vollständig.
2. Je nach aktueller Rolle `START_IMPLEMENTIERUNG.md` **oder** `START_REVIEW.md` aus demselben Ordner.
3. Die `AGENTS.md` jedes Zielrepos, in dem du arbeiten oder das du prüfen wirst; zu Beginn der repoübergreifenden Grundinstallation alle fünf.

Der konkrete Sitzungsauftrag bestimmt, ob du implementierst oder unabhängig prüfst. Diese Datei startet keine Umsetzung und wählt kein Modell. Ein fehlender oder widersprüchlicher Auftrag ist keine Erlaubnis, Produktdateien zu verändern. Anforderungen nicht still abschwächen. Repo-Dateien ergänzen den zentralen Auftrag, ersetzen ihn aber nicht.

## Umfang und Übernahme

- Nur die vereinbarte lokale Grundinstallation; kein Portal-Freigabeprozess, kein SSO-Ausbau, kein LDAP-Import, keine fachliche ClickHouse-Pipeline, kein Agentic BI.
- Quellen und Zielzustand vor Änderungen erfassen. Bereits abgelegte AGENTS-/Auftragsdateien, Remotes und Nutzerarbeit erhalten. Kein ungefiltertes Kopieren, kein `rsync --delete` in vorhandene Ziele.
- Insbesondere kein `jenkins-home/`, keine alten Secrets und keine Laufzeit-Historie aus den Quellen übernehmen. Quell-AGENTS nicht ungeprüft aktivieren oder über diese Regeln kopieren.
- Keine globale Ersetzung von `datenportal`. Zulässige technische Namen bleiben gemäss Auftrag erhalten; aktive Build- und Laufzeitziele gehören in den neuen Namespace.
- Jeder Git-Befehl bezieht sich auf das konkrete Zielrepo, etwa mit `git -C <repo> ...`. Keine übergeordnete `.git` anlegen und kein pauschaler Commit fremder Änderungen.

## Sicherheit und Nachweise

Nur eigene lokale Testressourcen verwenden. Kein produktiver S3-Write, Remote-Push, externes Reload, `docker system prune` oder ungezielte Volume-Löschung. Ein reguläres Stoppen erhält Volumes. Secrets nur durch die vorgesehenen Programme verwenden, nie in Dialogen, Berichten oder Git veröffentlichen.

Implizite Annahmen durch tatsächliche Tests ersetzen. Exitcode, Arbeitsverzeichnis und Testgrenze dokumentieren. Nicht ausgeführte Pflichtnachweise bleiben offen. Die G01–G24 des Auftrags sind der Abnahmevertrag.

## Implementierung und Review

**Implementierung:** gezielt in den fünf Zielrepos arbeiten. Phasenberichte nach `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/reports/`; festgeschriebene Kandidaten nach `candidates/<candidate-id>/` im selben Dokumentationsordner. Bestehende Berichte nicht rückwirkend passend machen.

**Review:** neue Sitzung, das im Reviewprompt vorgegebene Modell und genau der übergebene Kandidat. Produktdateien, Tests, Anforderungen, Prompts und AGENTS-Dateien nur lesen; keine Reparaturen oder Produkt-Commits. Builds und Tests mit eigenen isolierten Laufzeitdaten sind erlaubt. Bericht und bereinigte Belege nur nach `review/<candidate-id>/<run-id>/`. Produktstand vor/nach dem Lauf prüfen. AGENTS.md ist kein technischer Schreibschutz.

Unabhängige Abnahme nur nach tatsächlich durchgeführtem Review; ein zweiter Prompt an den Implementierungsagenten genügt nicht. Nach Produktkorrekturen neuen Kandidaten erstellen.

## Versionierbare Arbeitsbereichsvorlage

Diese Datei wird zusätzlich unter `dateninfrastruktur-dev-stack/docs/implementation/grundinstallation/templates/AGENTS.workspace.md` geführt. Änderungen ausserhalb eines eingefrorenen Reviews an beiden Stellen konsistent halten und im Handoff hashen. Keine globalen OpenCode-Anweisungen oder Accounts überschreiben. Für einen anderen Auftrag gelten dessen ausdrückliche Umfangsgrenzen; diese Grundinstallation nicht ungefragt wiederholen.
