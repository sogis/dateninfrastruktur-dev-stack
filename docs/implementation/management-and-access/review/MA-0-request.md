# Reviewrequest MA-0

## Ausgangspunkt

- STACK base: `8b75fc562039b634da7a917fea22d672bbb3a1d7`
- PUBLIC base: `7eff0b138c23524ac522231ce312d4c6659635dc`
- ADMIN: neu, kein Vorgängercommit und kein Remote.
- Neue Phase, keine übertragbaren unabhängigen Phasenbelege.

## Änderungen und Wirkung

STACK-/PUBLIC-AGENTS ordnen die alten Grundinstallationsgrenzen historisch ein.
Adminrepo enthält Boot4.1.2/Cayenne5.0-M3/Java25-Grundgerüst und einen echten
isolierten PostgreSQL-Kompatibilitätstest. SQLExec bindet Actor transaktionslokal;
ORM-DML-Trigger und Bindungszeile protokollieren identische PID/Tx. Einerpool,
zwei Personen, fehlender Actor und Rollback nach ORM-Flush werden geprüft;
Neuladen über Cayenne erhält Unicode. Noch keine fachlichen Modelle/GUI.

ili2pg5.5.2/ili2c5.6.9/ilivalidator1.15.0 sind mit offiziellen URL/Archivehashes
gepinnt. Die Vanilla-PG16-Probe scheitert an fehlendem postgis_full_version();
mit eigenem nativen PG16/PostGIS-Container klappt die UUID-Schemaerzeugung.
Images der bestehenden Nutzerinstanz unverändert. Entscheidung und Quellen
stehen in MA-0-versions.md.

Kein bestehender autonomer Runner gefunden. Neuer kleiner Runner erstellt
Sibling-Clones genau nach Commit, Workspace-AGENTS-Kopie/Hash und Spec-/Request-
Hashbindung; echte neue OpenCode2.2.5-Standalone-Sitzung, vorhandene DeepSeek-
Credentials, exakter Modellalias. Sessionexport bestätigt Provider/Modell;
Datei-/Shellzugriff, Produktintegrität und strukturierte Pflichtnachweise sind
Gatebedingungen. Kein normaler Benutzerwechsel und keine globale Konfiguration.

## Neu ausgeführte Prüfungen / Reviewer-Testauswahl

| ID | Kommando und CWD | Erwartung / Implementierergebnis |
|---|---|---|
| M00 | STACK `./scripts/management/preflight.sh`; Quell-/Versionscheck gemäss MA-0-versions.md und ADMIN/db/toolchain.json | echter Bestand/Tools; keine Veränderungen an Nutzerressourcen |
| M01 | ADMIN `python3 scripts/compatibility.py` | PASS: Boot/ORM/PID/Tx, Pool/Outer-Rollback und ili2pg-UUID-Schema unter PG16/PostGIS; Exit0, 1 tatsächlich ausgeführter JUnit-Test |
| M02 | STACK `python3 scripts/management/test_review_gate.py`; tatsächliche Review-Sitzung | PASS: synthetisch gültiger Kontrollfall; falsche SHA, fehlender Report, fehlende/doppelte/skippte ID, falsches Modell, fehlende Gegenprobe und geänderter Quelltext öffnen kein Gate. Echtes DeepSeek-Datei-/Shellsmoke bereits ausgeführt, aber ausdrücklich keine Phasenabnahme |

Implementiererrohbeleg: ignoriertes `.runtime/management-review/MA-0/preflight/compatibility.log`.
Reviewer führt Tests selbst im Kandidaten aus, schreibt eigene Rohbelege in
seinen Ausgabeordner und wählt eine eigene relevante Gegenprobe.

## Nichtbetroffenheiten und Grenzen

MA-A-Modelle, vollständige Persistenz/Audit, Authentifizierung/Workflows,
öffentlicher DB-Katalog und Downloads sind spätere gesperrte Phasen.
Kein ClickHouse-/Superset-/Jenkins- oder Foundation-Vollbau, keine Nativezusage.
Keine Nutzer-.env oder historische Lade-/Grundinstallationsbelege verändert.
Im aktuellen ersten Runner laufen Pflichtchecks stets frisch; keine ungeprüfte
Übernahme älterer Belege. Shellrechte sind kein OS-Schreibschutz; Vorher/Nachher-
Hashes/Gitstatus des Kandidaten und Originals bleiben zwingend.

## Übergabe

Lokale Commits zuerst, danach ignorierter konkreter Handoff mit allen HEADs.
Nur vollständiges unabhängiges ABGENOMMEN an genau diesem Satz erlaubt MA-A.

## Runnerkorrektur vor Erstabnahme

Erster tatsächlicher Reviewstart blieb mit `Agent not found` geschlossen, ohne
Report oder Abnahme. OpenCode2.2.5 löst eine frisch angelegte Projektkonfiguration
verzögert auf. Runner prüft jetzt mit `debug agents --standalone` die wirkliche
Entdeckung des primary-Reviewagenten vor der neuen Review-Sitzung (maximal drei
Auflösungsversuche). Kein Ersatzagent/Modellfallback. Sämtliche MA-0-Pflichtchecks
bleiben frisch auszuführen; kein übertragener unabhängiger Beleg.
