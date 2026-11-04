# MA-F0: konkreter Bestand und nichtdestruktiver Übernahmeplan

Inventurdatum: 4. November 2026. Private Rohinventur und Plan unter
STACK/.runtime/consolidation/{source-inventory,plan}.json (0700/0600), nicht
Teil eines Reviewhandoffs. Keine Original-.env oder Nutzerdumps an Reviewer.
Keine lokale Umschaltung/Stilllegung ist in F0 freigegeben.

## Beobachtete Quellen

Genau ein Foundationprojekt `dateninfrastruktur-dev-stack` mit neun laufenden
Dauerservices; echte Composelabels, Configfile und Arbeitsverzeichnis stimmen
mit diesem STACK überein. Zugehörige benannte Garage-, Jenkins-, ClickHouse-,
Superset- und PGvolumes sind identifiziert. PG16.10, UTF8/en_US.utf8; Keycloak
und Superset ausschliesslich plpgsql. Keycloak hat tatsächlich zwei Realms,
vier Nutzer und13 Clients. Superset enthält eine gespeicherte Verbindung.
Keine Realmvorlage wird als aktuelles Backup behandelt.

Genau eine durch private State-Dateien gebundene Managementquelle:
ADMIN/.runtime/managed-test. Ein PG16.9/PostGIS3.5.2, zwei Admin-/Portal-/Gateway-
Instanzen, ein Garage/Origin/Keycloak und ein Test-Headerbeobachter. Management
enthält2 Datensätze,4 Principals,2 Grants,3 Decisions und107 bestehende Auditzeilen.
Der aktuelle Nutzerissuer ist http://127.0.0.1:50097/auth/realms/dateninfrastruktur;
technischer urn:di:operator bleibt getrennt. Die Rohreferenzen binden alle
exakten IDs, Images, Labels, Mounts, Statehashes und zehn verwendete Volumes.

Der MA-Keycloak hat **wirklich** H2-Dateien unter /opt/keycloak/data/h2 in der
Container-Schreibschicht (kein Datenvolume). Vor Retire sauber stoppen,
geschützt sichern, offline mit demselben Keycloakimage exportieren. Import-JSON
ist kein Ersatz. Die MA-Garage verwendet zwei anonyme Volumes, die erhalten
bleiben, bis S3copy und Rückfall belegt sind. Keine binäre Garage-/PG-Datadirmischung.

12 weitere Dockercontainer sind unselektiert und bleiben unberührt. Andere
ADMIN-Runtimepfade enthalten keine zweite gebundene aktive Managementdatenbank;
isolierte historische Reviewcheckouts werden nicht als Livequellen ausgewählt.
Falls spätere Inventuren neue/abweichende befüllte Quellen zeigen: SOURCE_CHANGED
oder enger Quellenwahlblocker, kein Zusammenwerfen von Grants/Decisions.

## Zielentwurf (noch keine F1-Implementierung)

Eine kanonische compose.yaml, genau postgres/keycloak/garage/origin/gateway/
sodata/admin/jenkins/clickhouse/superset. Keine a/b-Instanzen, kein s3-browser
oder origin-probe als Dauer-Service. APISIX eigener Netzwerkraum, Jenkins per
jenkins:8080. Gateway18081, Keycloak18080, Superset18088, vorhandene ClickHouse-
Ports; keine normalen DB-/Admin-/Origin-/S3hostports. Einmalwerkzeuge als Profile.
Imagebuilds mit projekt-/quellgebundenen Tags, keine Überschreibung von :local.

Foundation Garage-, Jenkins-, ClickHouse-, Superset-Volumes grundsätzlich als
Ziele erhalten. PG hingegen logischer Restore beider Quellen in ein **neues**
benanntes Zielvolume, z.B. dateninfra..._postgres-ma-f. Das bestehende Foundation-
PGvolume bleibt Sicherung. Kein Austausch des Images am alten PGdatadir.
Keycloak→keycloak, Superset→superset, MA→dateninfrastruktur_management;
Owner/ACLs/Sequenzen/alte Auditzeilen in F2 vollständig restaurieren/vergleichen.

Ein Zielissuer http://localhost:18080/realms/dateninfrastruktur. Aktuelle MA-
Principalbindungen erst nach echtem Offlineexport/UUID-/Konfliktabgleich auditiert
umstellen; interne Principal-UUIDs, Grants und alte Decisions/Audit unverändert.
Foundationcredentials bei Personenüberschneidung erhalten. Fremde Clients nicht
mit Realmvorlagen überschreiben. Personenabbildung ist noch PENDING, keine
ungeprüfte Zuordnung als fertig behauptet. Neu anmelden beim expliziten Cutover.

Alle vorhandenen Secrets nur programmatisch übernehmen: Foundation-.env plus
konkrete Containerkonfiguration; MA-State/roles/config-Dateien als Referenzen.
Superset-SECRET_KEY unverändert. Ein aktiver Runtimeordner im STACK, alte
Konfigurationen als Rückfallbeleg. S3copy private Keys unverändert; abweichender
vorhandener Key ist Konflikt. Legacyöffentliche Route standardmässig sperren,
Bytes/Buckets behalten. Keine externen Originaldaten ändern.

Nach abgenommenem F3-Code: Schreibpause ankündigen, finale Backups/Checkpoints,
Zielrestore verifizieren, stabile Ports umschalten, fachlichen Zugriff prüfen,
erst dann gebundene Altcontainer ohne Volumelöschung retire. Keine Löschung
ungesicherter Schreibschichtdaten. Rückfall nur vor neuen Zielwrites automatisch.

## PG-Kompatibilitätsentscheid

Der vorhandene BAO16-3.5-Registrydigest ist weiterhin PG16.9; BAO16-3.6 existiert
nicht. Die geprüften offiziellen PostGIS16-Tags liefern nur amd64. Deshalb kleiner
abgeleiteter Build auf **offiziellem postgres16.10-bookworm per Manifestdigest**
und PGDG-Archivpaketen PostGIS3.5.2 mit festem Versions-/SHA256check. Kein neuer
Major und kein blindes Minor-Downgrade. Lock unter services/postgres/image.lock.json.

Realer F02-Composeprobecontainer läuft nativ arm64: server_version_num160010,
PostGIS3.5.2 und uuid-ossp in Management, drei logische DBs, keine GIS-Extensions
in template1/Keycloak/Superset. Die Probe wurde wieder entfernt; keine neue
parallele Anwendungslaufzeit. amd64-Pakethash ist gepinnt, amd64-Lauf nicht
behauptet. Locale-/Collationunterschied Alpine→Debian verlangen logischen Restore
und neue Indexbildung mit Fehlerabbruch in F2.

Primärquellen: [PostgreSQL Debian](https://www.postgresql.org/download/linux/debian/),
[PGDG-Archiv](https://apt-archive.postgresql.org/),
[BAO-Quellrepo](https://github.com/baosystems/docker-postgis).
Manifestplattformen und tatsächliche Versionen wurden zusätzlich per Docker geprüft.

## Reviewtransport und Tests

Installierte Desktop-CLI: opencode v2.2.5, run --help mit standalone/agent/model/json.
`models --standalone` liefert deepseek/deepseek-flash; der offizielle
[DeepSeek-Aliasvertrag](https://api-docs.deepseek.com/quick_start/agent_integrations/)
ordnet deepseek-flash dem Stand DeepSeek-V4.1-Flash-1017 zu. Kein Free-Provider,
kein globaler Account-/Key-/Permissionwechsel. Tatsächliche Session-/Modell-/Read-/
Shellbeweise folgen im unabhängigen F0-Lauf.

Vorhandener Runner unterstützt jetzt MA-F0–F4 mit sechs Geschwistercheckouts,
neuem Specordner/Runtimepfad und Hash der tatsächlich aktiven Workspace-AGENTS-
Kopie. Alter MA-Reviewvertrag bleibt erhalten. F01 Fehl-ID/Label/Projekt/Mount
verweigert vor Mutationscallback; F02 native reale PGprobe; F03 falsche SHA,
fehlende/skipppte Reports/Tools öffnen das Gate nicht. Keine MA-A–E-Vollsuiten.
