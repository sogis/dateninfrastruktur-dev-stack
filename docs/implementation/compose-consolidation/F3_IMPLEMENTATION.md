# MA-F3 – ein Betriebspfad und gesicherter Retire

Root-init/build/setup/up/stop/down/restart/status/logs verwenden denselben
ComposeContext. Managementaliases delegieren darauf. Keine Shell-.env-Ausführung,
keine neue separate DB, keine Host-JARs oder automatischen Seeds/Publikationen.
Bekannte Volumenzuordnungen werden vor Start geprüft; vorhandenes Setup verifiziert
nur den aktuellen Vertrag. Falsche Instanz oder geändertes Volume blockiert vor
Stop/Neuerstellung. Stop/Start und echter down/up ohne -v sind getrennte Prüfungen.

ADMIN-management_db ist nur noch ein expliziter PostgreSQL-Tooladapter. Alte
managed_runtime/identity_runtime/run/setup-CLIs delegieren; historische separate
Containerharnesses sind ausführbar gesperrt und in Git erhalten. Fachliche Java-
Tests, Modelle, Mapping, bisherige SQL-Migrationen und Native-/JVM-Buildoptionen
bleiben. Die existierenden Javaoperatoren erhalten einen gemeinsamen Compose-
Einstieg; kein zweiter Importworkflow. Alte Foundation-Smoketests erzeugen keinen
Legacy-Nutzerstack mehr. Ein neuer Smoke liest ausschliesslich den gewählten Kontext.

Die zusätzliche Gradle-Adaptergrenze weist Legacy-S3-Publikation im DB-Katalogmodus
vor Taskaktionen verständlich ab. Lokale Legacyartefakte und eigenständige Ladejobs
bleiben nutzbar; am ClickHouse-Lader, seinen Daten oder Archiven gibt es keinen Diff.

## Umschaltung

Ein expliziter Cutover baut Images vor der Schreibpause und bindet alle Quellen,
checkpoints, Zielcredentials, ausführbaren Dateien und Volumes. Er restauriert
über F2 und startet nach der vollständigen Quellsicherung genau die zehn Dienste.
Schema/Identitäten, private Objekte, Jenkinskonto und bestehende verschlüsselte
Supersetverbindung werden geprüft. Der abschliessende Benutzerfachpfad wird
getrennt nachgewiesen; kein Healthstatus als fertiger LOCAL_CUTOVER_VERIFIED.

Quellen-Dateisysteme werden im gestoppten Zustand vollständig per Docker export
privat archiviert; H2-Bytes werden zusätzlich gegen das aktuelle Offlinebackup
geprüft. Docker commit wurde nach einer tatsächlich reproduzierten containerd-
Manifestlücke bei neu getaggten Buildimages ersetzt. Es wird kein Image-GC/Prune
als vermeintliche Reparatur benutzt. Quellarchitektur, Env, Entrypoint/Cmd,
Healthchecks, Ports, Namespaces, Volumes und nötige Bindkonfigurationen bleiben
separat überprüfbar. Ein privates Recovery-Compose dient ausschliesslich dem
expliziten Rückfall, nie als zweite normale Laufzeit.

Retire prüft komplette Allowlist, Checksummen, Ownership und gestoppten Zustand.
Dann Restart deaktivieren und nur exakte CIDs ohne -v entfernen. Alle Original-
volumes bleiben behalten. Nach neuen fachlichen Zielwrites verweigert Rückfall
vor Stop oder Erstellung. Vorher kann auch nach rm aus den geprüften Exporten
rekonstruiert werden; der normale Zielstart wird während Recovery blockiert.

## Gezielte Tests

F14/F15: nichtleere Übernahme, echte Root-/Managementwrapper, lesendes Bestandssetup,
falsche Instanz/Volumenzuordnung, Stop/Start und vollständiger Recreate. Gleiche
Fach-/Audit-/Sequenz-/Secrethashes, reale Logins, aktive/widerrufene Rechte,
historische Dateien, Jenkinsmarker und Superset-ClickHouse-Verbindung.

F16: nicht gelistete CID und verändertes Backup abgewiesen; genaue Quellen ohne
Volumelöschung entfernt; Wiederherstellung aus Exporten mit aktuellem H2-Benutzer
und einer ehemaligen gemeinsamen Netzwerknamespace. Der Namespace-Child besitzt
einen erst nach Start geschriebenen Zustand: reines Image-/Template-Replay genügt
nicht. Die zusätzliche Migrationfixture ist kein HA- oder Defaultdienst.

Normale zehn Dienste haben keine network_mode-Kopplung; nur die ausdrücklich
benannte Legacy-Quellfixture und der private Recoverybefund stellen die alte
Namespacebindung für diese Gegenprobe dar. Alte Nutzercontainer werden durch
Tests/Reviewer nicht verändert. Der tatsächliche Cutover wartet auf F3-Abnahme.

## Risikobasierte Nacharbeit

| Änderung | Neu geprüft | Begründet unverändert |
|---|---|---|
| commit → export/import mit Metadaten | wirkliche aktuelle H2-Bytes und Wiederherstellung nach rm | keine DDL-/Fach-/Autorisierungsänderung |
| Namespace-Child ohne unzulässigen Hostname | F16 allein frisch, beide Server und nachträglicher Zustand wieder vorhanden | bestandene F14/F15-Recreatekette |
| Startblock vor/bei Recovery, kein Start ohne Setup | gezielte Guards vor Dockeraufruf, Writeguard vor Startblock/Stop | normale positive Wrapperkette mit bekanntem Setup |
| ursprüngliche dynamische Ports/literale Envwerte | gespeicherten tatsächlichen Port übernehmen, fehlenden Port verweigern; Dollars literal | Runtime-URLs ohne zufällige Neuzuteilung |
| Legacy-Publikationsadapter | echter Gradle-Fehler vor Taskaktion / lokaler Skip erfolgreich | Ladercode und private Archive ohne Diff |

Original-Jenkins wurde ausschliesslich lesend geprüft (acht Jobs, idle). Der
produktive Cutover prüft vor Stop nochmals idle/Queue und stoppt Jenkins samt
Namespace-Child vor den übrigen Schreibern; sein finaler Jobnamencheckpoint wird
mit dem Ziel verglichen. Keine Benutzer-Credentials oder Jobdaten im Reviewhandoff.
