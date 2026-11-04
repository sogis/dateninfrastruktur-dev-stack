# Reviewrequest MA-F2

- STACK base: `6673b67eb3c51452d5e1714178d057738d1cb9e5`
- ADMIN base: `14374ecd58f2ad27432ec7fe0fd4535021795d80`
- PUBLIC base: `b1f20075be43eb4d0edf771ee1440ea0e30e1801`
- JENKINS base: `08931fa8254d096e2addcd3aee97bc1b753f087d`
- PLUGIN base: `579f3fd54432a977122afb186469fbb40d95322f`
- TOPICS base: `303b2f0be785dc5b06882612f9b8bfcd8c17b040`

Umfang: gezielte Korrektur F2-MAJOR-1 aus dem unabhängigen Review
20261104T232247Z. Der vorherige Phasenentscheid war NACHARBEIT; alle Pflichtläufe
F09–F13 wurden dort trotzdem tatsächlich erfolgreich ausgeführt. Der zusätzliche
Garage-Codecgegenfall blockierte die Phase. Das alte Urteil wird nicht übernommen.

Änderung: garage-setup erhält seine sechs Credentialwerte durch Compose-
Environmentinterpolation statt eines zweiten dotenv-Parsers. Vor Admin-API-
Schreibzugriff prüft es die tatsächlichen Garage2.4.1-Zeichenregeln. Neue positive
S3-/rclone-/Originprobe verwendet importierte Secrets mit Dollar, Backslash und
beiden Quotezeichen. Zeilenumbrüche werden exakt transportiert, von Garage aber
als ungültige Controlcharacters vor jeder Schlüsseländerung abgewiesen.

Frisch selbst ausführen:
- `python3 scripts/test_garage_migration_delta.py` (F11/F13)
- `DI_GATE_TEST_PHASE=MA-F2 python3 scripts/management/test_review_gate.py`
- `python3 scripts/test_migration_safety.py`

Die Garageprobe startet nur zwei eigene kurzlebige Garagequellen/-ziele und
Compose-Tooljobs plus einen internen read-only Origin. Keine PG-/Keycloak-/
Anwendungszweittopologie. Echte S3bytes/Metadaten, Replay, Import, Originread,
Operatorread und negative Schreib-/Privatrechte müssen bestehen. Ungültige
Secretzeichen dürfen keinen vorhandenen Schlüssel rotieren.

| Geändert | Neu geprüft | Unverändert übernommene Beobachtung |
|---|---|---|
| Garageinput/Compose-Environment | F11/F13 Grafikzeichen, echter Copy/RO/Legacydeny, ungültige Controls | keine Übernahme des alten Codecgegenfalls |
| Reviewgate explizite Übernahme | bound prior report/runner/handoff/evidence; Manipulation, fehlende Begründung/FAIL/fehlender Verweis abgewiesen | keine alte Phasenfreigabe |
| Kein DB-/IAM-/Coordinator-/Rollbackdiff | neuen Diff und gebundene alte Eigenläufe prüfen | F09 volle DBs/Owners/ACLs/Sequenzen; F10 UUID/Principal/Audit; F12 Quellenänderung/Rückfall/Writeguard |

Der neue Handoff kopiert die alten synthetischen Reviewbelege in seinen eigenen
prior-evidence-Bereich und bindet ihre SHA256. F09/F10/F12 dürfen nach eigener
Nichtbetroffenheitsprüfung mit `execution: CARRIED`, `source_report_sha256`,
`reason` sowie den unveränderten alten Kommando/CWD/Exitfeldern und der kopierten
`evidence_path` dokumentiert werden. F11/F13 müssen `EXECUTED` am neuen Kandidaten
sein. Eine eigene sinnvolle neue Gegenprobe passend zum Delta ausführen.

Keine gesamte F2-/F1-/MA-A–E-Suite wiederholen: die Datenbank-, Identitäts- und
Rückfallimplementation hat keinen Diff. Das Haupttestprogramm bleibt für spätere
Integration unverändert verfügbar. Alle sechs HEADs und der ganze neue Diff sind
selbst zu prüfen. Keine Nutzerdateien/-secrets und keine Produktreparaturen.

Quelle der Garage2.4.1-Zeichenregeln:
https://github.com/deuxfleurs-org/garage/blob/v2.4.1/src/model/key_table.rs#L145
Livezustand weiterhin LOCAL_CUTOVER_PENDING; F3 ist noch geschlossen.
