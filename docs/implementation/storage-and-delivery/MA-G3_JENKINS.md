# MA-G3 – Jenkins-Anlieferung und technischer CSV-Lauf

Die Oberfläche `/anlieferung` führt über APISIX zu
`/jenkins/data-delivery/`. Jenkins nutzt seinen eigenen vertraulichen
Keycloak-Client `jenkins-delivery`, Authorization Code mit PKCE S256 und
`sub` als unveränderliche Jenkins-ID. Das interne Admin prüft das Access-Token
kryptografisch und prüft den Lieferauftrag anhand der aktuellen PG-Fachrechte.
Der Wiederherstellungsadministrator hat aus Jenkins-Rechten kein Lieferrecht.

Vor dem Multipart-Stream legt die Oberfläche einen autorisierten Auftrag an.
Der Upload bindet genau dessen UUID; CSRF-Crumb und Idempotenzschlüssel liegen
in Requestheadern. Der Stream ist auf das kleinste konfigurierte Limit
begrenzt. Standard 100 MiB, Hardlimit 256 MiB; APISIX erlaubt 257 MiB inklusive
Multipart-Rahmen und 300 Sekunden Sende-/Lesezeit zum Jenkins-Upstream.
Der Gateway verwendet eine DNS-Gültigkeit von zwei Sekunden für wechselnde
Compose-Containeradressen nach einem Neustart.
Die private Datei und ihre Metadaten werden synchronisiert und unveränderlich
materialisiert. Eine Unterbrechung zwischen Dateiabschluss und Seal bleibt
`UPLOADING`; gleiches Material kann wiederholt werden. Der Dispatcher
prüft Aufträge alle fünf Sekunden. Der Spoolsweep verarbeitet höchstens acht
ältere eigene Verzeichnisse pro Runde (fünf Minuten): unversiegelte Reste
können nach 24 Stunden zentral geschlossen werden, nach sieben Tagen werden
bestätigte terminale Reste dieser nicht angenommenen Aufträge entfernt.
Retrybare, angenommene und veröffentlichte Eingänge bleiben erhalten. Die
private S3-Archivierung und ihr Nachweis folgen in G4.

`di-csv-ingest` wird ausschliesslich mit eigenem Marker, fester Pipeline und
ohne Buildparameter provisioniert. Die getrennte Keycloak-Dienstidentität
`di-ingestion-executor` hat nur die Rollen `dispatch` und `execute`. Die
Jenkins-Ausführung verwendet `di-csv-executor`, mit `Agent/Build` für den
vorhandenen Ausführungsknoten und eigenen Jobrechten. Jenkins lädt seine vier
Zugangsdaten per JCasC aus Compose-Secret-Dateien. Diese Werte gelangen nicht
in die Prozessumgebung, die Jenkins beim Pipeline-Lauf serialisiert. Die
erste Stufe bindet
zentral einen exklusiven Claim, prüft Plan und Bytes und schreibt temporäre
Dateien nur in den Runworkspace. Plan und Ergebnis binden Bundle-, Repo- und
Imagehash. Der Dispatcher wiederholt dieselbe stabile Zustellung nach
Unterbrechung. Ein bestätigter beendeter Run wird anhand von Dispatch-, Run-
und Submissionbindung abgeglichen; ein Fachcommit kann nicht zurückgestuft
werden. Zugang, Status und Berichte für Lieferanten bleiben in der Oberfläche.

Der normale G3-Kandidat enthält keinen CSV-Prozessor; das Formular zeigt den
vorläufigen Zustand und erzeugt keine Lieferaufträge. Der isolierte Test
baut ein abgeleitetes Probeimage. Die Probe prüft tatsächliche Bytes, Identität,
Claims und Parallelität, erzeugt kein Erfolgsmanifest und publiziert nichts.

Vor der späteren lokalen Umstellung: mit eindeutiger Stack-Umgebung
`scripts/provision_ingestion_oidc.py --env <runtime.env> --register-pg`
ausführen, sobald die G2-Persistenz eingerichtet ist. Der explizite Schritt
erstellt oder verifiziert nur die beiden gebundenen Clients, registriert den
verifizierten Dienstsubject und vergibt keine Fachrechte. Bereits vorhandene
fremde Clientkonfiguration oder abweichende Credentials werden abgelehnt.

Jenkins stoppen. `scripts/retire_legacy_jenkins_g3.py plan --env <runtime.env>`
inventarisiert die eigenen alten Seed-/Organisationsjobs und die unveränderten
übrigen Jobs. `apply --env <runtime.env> --file <private-plan.json>` archiviert
nur exakt markierte Jobs im selben Volume, komplett mit Buildhistorie.
Drift, Namenskollisionen oder fremde Mounts werden abgewiesen. Danach das
explizit frisch gebaute Jenkins-Image mit
`scripts/bind_jenkins_image.py <tag> --env <runtime.env>` an seinen
unveränderlichen Image-ID binden. Der Normalstart enthält keine Migration.
