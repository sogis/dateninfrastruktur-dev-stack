# Reviewrequest MA-F3

- STACK base: `1473754349739bdc7d79ab7762a5dabd44c1b856`
- ADMIN base: `14374ecd58f2ad27432ec7fe0fd4535021795d80`
- PUBLIC base: `b1f20075be43eb4d0edf771ee1440ea0e30e1801`
- JENKINS base: `08931fa8254d096e2addcd3aee97bc1b753f087d`
- PLUGIN base: `579f3fd54432a977122afb186469fbb40d95322f`
- TOPICS base: `303b2f0be785dc5b06882612f9b8bfcd8c17b040`

Umfang: F14–F16, ein Betriebsweg, gesicherter Retire und belegte Rekonstruktion.
F3_IMPLEMENTATION.md, docs/operations.md und docs/migration-ma-f.md beschreiben
Implementierung und Grenzen. Neue fachliche Modelle/SQLmigrationen gibt es nicht.
Root/Management/ADMIN-Launcher erzeugen keine separate Laufzeit. Historische
Containerharnesses sind ausführbar gesperrt; Javafachtests und Buildoptionen bleiben.

Selbst auszuführen aus STACK:
- `./scripts/test-consolidation.sh --phase MA-F3`
- `python3 scripts/test_compose_lifecycle_safety.py`
- `python3 scripts/test_migration_safety.py`
- `DI_GATE_TEST_PHASE=MA-F3 python3 scripts/management/test_review_gate.py`

Der Hauptlauf erstellt eigene nichtleere F2-Quellen und verwendet dann denselben
produktiven Cutover, dieselben öffentlichen Wrapper und Retire/Rückfalloperationen.
Keine Nutzerinstanz/-secrets oder vorhandene Nutzerdumps berühren. Das lokale
unveränderte Jenkinsimage wird nur über Image-ID gelesen. Alle eigenen Ressourcen
werden nach Ownershipprüfung beseitigt; Archive bleiben in ignorierten Pfaden.

F14: identischer expliziter Kontext für Root/Management, kein hidden Docker-run
oder ADMIN-state.json-Control. Falsche Instance oder geändertes Volume blockiert.
Reales Gradle: DBmode+Legacyupload scheitert vor Taskaktionen; lokaler Artefakt-/
Reloadskip bleibt möglich. Kein Diff am ClickHouse-Lader oder dessen Daten.
F15: bestehendes Setup nur lesend, Stop/Start UND down/up ohne -v. Tatsächlich neue
CIDs aller zehn Services; gleiche Fach-/Audit-/Sequenz-/Secrethashes, reale Logins,
aktive/widerrufene Rechte, historische Dateien, Jenkinsmarker und Superset→CH.
F16: vollständige Allowlist/Archivbinding, veränderte Liste oder Sicherung verweigert,
gezieltes rm ohne Volumelöschung, alle Originalvolumes weiter vorhanden.
Danach echte Wiederherstellung aus Dateisystemexport+Metadaten, aktuelle H2-Person
und ein erst nach Start geschriebener Namespace-Childzustand müssen wieder lesbar sein.

Die zwei ausdrücklich bezeichneten Legacy-Namespace-Quellfixtures sind ein Test
der alten APISIX/Jenkins-Kopplung, keine neuen Defaultdienste und kein HA. Normale
Services sind weiterhin genau zehn ohne network_mode. Der private, automatisch aus
Originalinspect erzeugte Recovery-Compose ist nur ein ausdrücklicher Rückfall.
Er hat ursprüngliche Namen/Ports/Namespaces und bleibt ausserhalb des Normalstarts.

Eigene passende Gegenprobe zusätzlich ausführen, z.B. Quelle/Retireliste oder
Archiv nach Bindung manipulieren und sicher nachweisen, dass kein unberechtigtes
Stop/rm folgt; oder fehlendes bekanntes Setup vor Start prüfen. Produkt nicht ändern.

Eigene Implementiererbefunde: Recreate/F14/F15 bestanden; nach einem spezifischen
Recovery-Namespace-Hostnamefix nur F16 erneut ausgeführt und bestanden. Laufzeit-
Schreibschichten werden per Docker export gesichert: docker commit versagte bei
alten neu getaggten Buildimagemanifesten mit fehlendem containerd-Digest. Kein
Prune als Reparatur. Zusätzliche Startblock-/Port-/Rollbackguard-Units und echter
Gradleadapter wurden gezielt geprüft. Der Reviewer führt den endgültigen vollen
F3-Hauptlauf selbst aus; keine alte MA-A–E-/F2-Vollsuite zusätzlich starten.

Der tatsächliche lokale Cutover ist NOCH NICHT durchgeführt. Alle 20 ausgewählten
Originalquellen wurden erneut lesend als unverändert laufend nachgewiesen; lokale
Jenkinsanmeldung zeigt acht unveränderte Jobs und keine aktive/queued Ausführung.
Erst nach unabhängiger F3-Abnahme: eigenes Wartungsfenster ankündigen und anhand
aktueller finaler Quellen tatsächlich umstellen. Vollständiger Fachpfad und
LOCAL_CUTOVER_VERIFIED bleiben F4 beziehungsweise der echten lokalen Prüfung.
