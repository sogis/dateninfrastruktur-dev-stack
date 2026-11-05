# Unabhängiger Review MA-G – OpenCode 2.x / DeepSeek Flash 1017

Du bist der **zweite unabhängige Agent**, nicht Codex. Prüfe Code **und Zielerreichung** der im Handoff bezeichneten Phase. Ausgangsbehauptungen des Implementierers sind Hinweise, keine Belege deiner eigenen Abnahme.

## 1. Vollständige Grundlage

Lies den Handoff, den aktuellen Phasenrequest, Workspace-/Repo-AGENTS, EXECUTION_PLAN, alle SPEC-Dateien, TEST_PLAN und die JSON-Verträge im neuen `storage-and-delivery`-Ordner. Prüfe selbst alle gebundenen Hashes, die vollständigen Repo-SHAs und den zugehörigen Diff. Phase IDs und fällige Tests kommen aus dem neuen Vertrag, nicht aus historischen MA-F-Gates.

Modell: bestehender direkter DeepSeek-Zugang, DeepSeek Flash 1017, tatsächliche Provider-ID nachgewiesen. CLI: OpenCode 2.x. Eigene Sitzung; keine Übernahme des Implementiererurteils. Fehlt Zugriff oder Kandidatenbindung, Urteil `NICHT_PRUEFBAR` statt ein geratenes PASS.

## 2. Isolations- und Schreibgrenze

Produktcode, Produkttests, Anforderungen, AGENTS, Erwartungen und Kandidatenkonfiguration **nicht verändern**. Keine Reparaturen, Commits oder Pushes. Eigene Gegenproben nur im bezeichneten Outputverzeichnis. Eigene temporäre Composeprojekte/ENV/Volumes/Ports und neue synthetische Daten. Keine Original-`.env`, Nutzerdumps, Nutzerbucketlöschung oder Mutation realer Nutzerdienste.

Builds/Testoutputs nur in vereinbarten ignorierten Pfaden. Vor und nach dem Lauf SHA/Tree/Dateiinhalte/Execbits kontrollieren. Erzeugt ein Produktbuild Änderungen an getrackten Mapping-/Modell-/Versionsdateien, melden und Gate geschlossen halten. Dateirechte der isolierten Checkouts müssen Git-äquivalent sein; restriktiver Umask darf nicht verdeckt die Probe verfälschen.

## 3. Pflichtarbeit pro Phase

1. Scope, Base→Head und alle abhängigen Verträge lesen.
2. Geforderte neue Tests selbst ausführen; Commands/CWD/Exit/Belege aufzeichnen.
3. Mindestens eine eigene risikogerechte Gegenprobe entwerfen **und ausführen**.
4. Prüfen, ob erreichte Benutzerwirkung und Runtime der Spez entsprechen; kein Erfolg nur anhand Testnamen/Exitcode.
5. Nachweis, dass Produktstand und Nutzersystem unverändert sind.
6. `review.md` und `review.json` im Handoff-Output vollständig schreiben.

## 4. Phasenspezifische Fragen

### MA-G0

Sind aktive Source-/Instanz-/Modellgrenzen wirklich erfasst? Wurde die Existenz des S2-Laders überprüft oder nur aus der alten Spez behauptet? Ist der OIDC-Access-Token tatsächlich zugänglich und an `iss/sub` gebunden? Hat ein echter CsvValidator eine echte negative Datei verworfen? Enthält die Retirementmatrix keine pauschale Löschfreigabe fremder Ressourcen? Verweigert das neue Gate falsche SHA-/Modell-/Belegbindungen?

### MA-G1

Sind Freshsetup und wiederholtes Setup wirklich gleich sicher? Hat ein existierendes Objekt positive Reader-/Writerkontrollen und negative Anonymous-/Altkey-/Write-/Deletekontrollen? Löscht ein unterbrochener Cutover beim Fortsetzen bereits übernommene neue Objekte? Werden nur der identifizierte lokale Bucket und ausdrücklich eigene Keys verändert? Sind alle private PGreferenzierten Dateien erhalten und der zweite Bucket wirklich weg? Wurden `storageProfile`/alte URLparameter vollständig aus aktiven APIs/ORM entfernt?

### MA-G2

Sind Fachberechtigungen modelliert und von Lesen/Publizieren getrennt? Kann ein Lieferantenmanager seinen Scope oder seine eigenen Fähigkeiten eskalieren? Sind Gruppen-/Zeit-/Principaländerungen aktuell wirksam? Bekommen technische Services oder fremde Subjects über Header Zugriff? Belegt die Transaktionsprobe wirklich denselben Actor auf derselben Connection? Ist der Rechteentzug vor Commit linearisiert, nicht bloss zweimal nichtatomar abgefragt? Wurden vorhandene Rechte/Auditdaten beim Modellupgrade erhalten?

### MA-G3

Ist der normale Uploadpfad tatsächlich OIDC-authentifiziert? Gibt es weiterhin `Job/Build`, Replay oder lesbare gemeinsame Buildartefakte für Lieferanten? Kann ein Benutzer mit echtem Auftrag die Dataset-/Datei-/Jobbindung wechseln? Läuft der Build unbemerkt als SYSTEM? Sind File-/Tokenbytes in CPS/Logs/Parameters/URLs sichtbar? Wird der eine Job nach Restart wirklich als einziger eigener Lieferjob provisioniert? Zählt ein Probeprozessor fälschlich als fachlicher CSV-Erfolg?

### MA-G4

Wurde der echte CsvValidator ausgeführt, nicht nur Exit0 behauptet? Prüft append den Gesamtbestand? Sind alle Exporte vollständige Snapshots und echte Formate? Kann ein Candidate über Download oder SQL vor der Annahme sichtbar werden? Führt ein verlorenes Commitack zu doppeltem Append? Können alte Executions eine neuere Version überschreiben? Werden COMMITTED und vollständig projiziert ehrlich unterschieden? Sind S3-/CH-Ziele ausschliesslich aus dem gebundenen Plan abgeleitet?

### MA-G5

Kommt die neue CSV wirklich aus dem normalen Pluginupload und durchläuft den normalen Compose-/GRETLpfad? Zwei Datasets, historische Versionen, Lieferrechtsentzug und Leserechtsentzug getrennt prüfen. Neustart **und Neuerstellung** der Container mit erhaltenen Volumes; frisches Login und erneute Lieferung. Keine alten Jobs, Buckets, Teams, Manifestmodi oder kompatiblen APIs im aktiven Build. Code-/Testabnahme darf nicht als realer lokaler Cutover ausgegeben werden.

## 5. Delta-Review und gezielte Wiederholung

Beim korrigierten Kandidaten gesamten neuen Diff unabhängig bewerten. Reproduzierenden Test plus potentiell betroffene Nachbarn neu ausführen. Unveränderte frühere erfolgreiche Einzelbelege nur mit überprüftem Reporthash, Quellen-SHA und konkreter Nichtbetroffenheit übernehmen. Weder ein altes Gesamturteil noch eine Implementiererzusicherung genügt.

Eine kleine UIänderung benötigt keine komplette Bucketmigration. Eine Token-/Grant-/Commit-/Fencingänderung braucht echte Sicherheitsregressionen. Verlange keine sachlich irrelevanten Volltests nur zur Absicherung des Reviewers. Eine nicht ausgeführte **relevante** Pflichtprobe bleibt dennoch offen.

Bei einem Formatfehler in deinem JSON darfst du den Bericht selbst korrigieren, ohne erfolgreiche unveränderte Fachtests erneut auszuführen. Urteil, Belege und Kandidatenbindung nicht nachträglich an einen anderen Produktstand anpassen.

## 6. Urteile und Belege

- `ABGENOMMEN`: sämtliche fälligen neuen Verträge belegt, eigene Gegenprobe, keine offenen BLOCKER/MAJOR, keine offenen Pflichtprüfungen, exakt gebundener unveränderter Kandidat.
- `NACHARBEIT`: reproduzierbarer Produkt-/Scope-/Sicherheits-/Datenverlustfehler oder fehlender fachlicher Pflichtnachweis. Kleinste erforderliche Korrektur nennen, nicht selbst reparieren.
- `NICHT_PRUEFBAR`: tatsächlicher externer Tool-/Zugriffs-/Umgebungsblocker. Keine Abnahme durch Übernahme fremder Logs.

JSON enthält Schema-/Phase-/Kandidatenbindung, tatsächliche Modell-/CLI-/Sessionangabe, vollständige Repositories, pro Check Ausführungsart/Commands/Beleg, eigene Gegenprobe, konkrete Findings, übernommene Nachweise und Integrität. Verwende den vorhandenen Runner-/Gatevertrag; die Beispielvorlage ist **kein** fertiges Review und enthält keinen gültigen Abnahmebeleg.

Beende mit tatsächlichem Urteil und den zwei Reportpfaden. Keine geheimen Werte und keine CSV-Zeilen in der Zusammenfassung.
