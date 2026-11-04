# Reviewrequest MA-F0

- STACK base: `f72d929f304ae97bc395be7195ad33dd5d2eebe2`
- ADMIN base: `7986d67330fd6a304d98d2c4e73aa38d139bde4a`
- PUBLIC base: `20d94f5fbb9259f446f7ac0b22dd0e72b2d22ca6`
- JENKINS base: `08931fa8254d096e2addcd3aee97bc1b753f087d`
- PLUGIN base: `579f3fd54432a977122afb186469fbb40d95322f`
- TOPICS base: `7d99ceec0e392a5f12b602c0840c4762c7213fba`

## Umfang und Ergebnis

Nur F0: lesende Inventur/Plan/Eigentümergrenze, konkreter PG-Kompatibilitätsbuild,
aktive AGENTS-Verweise und vorhandener Reviewrunner auf MA-F erweitert. Keine
F1-Topologie vorweggenommen, kein Cutover, keine Nutzercontainer/-volumes geändert.
F0_BASELINE.md enthält den bereinigten konkreten Befund und Zielentwurf.
Private Nutzerinventur/.env/Plan/Dumps werden ausdrücklich **nicht** mitgegeben.

`consolidation.py inventory` liest IDs/Labels/Mounts/Images/Statebindungen und
DBkataloge in BEGIN READ ONLY. `plan` bleibt nichtdestruktiv. Exakte Objekt-ID,
Sourceimage/Mounts, Composeprojekt/Arbeitsverzeichnis/Configfile und Legacy-
Statehash/Mitgliedschaft werden vor einem Operationcallback verifiziert.
Unselektierte Fremdprojekte bleiben tabu. Live ist genau eine gebundene befüllte
MAquelle erkennbar; Identitätsabgleich bleibt bis gesichertem aktuellem H2export
PENDING, keine Personenannahme anhand Realmvorlagen. Echter H2-Schreibschichtpfad
wurde gelesen und für Backup/Retire vorgemerkt. Foundation-/MA-Secrets nur als
private Dateireferenzen/Feldnamen und Hashes, nie als Report-/Promptinhalt.

Image: BAO16-3.5 ist tatsächlich weiterhin PG16.9; offizielles PostGIS16 hat in
den geprüften Manifesten nur amd64. Kleiner nativer Build auf offiziellem
postgres16.10-bookworm per Manifestdigest, PostGIS3.5.2-PGDG-Archivpakete mit
festen arm64/amd64/all-SHA256. Kein Downgrade/Majorwechsel, keine GIS-Extensions
in template1 oder anderen DBs. Sourcepins und echtes arm64-Ergebnis im Image-Lock.
Alpine→Debian wird später logisch migriert, kein Datadirimagewechsel.

Reviewtransport wiederverwendet scripts/management/review-phase.sh, MA-F0–F4
mit sechs isolierten Geschwistercheckouts, neuen Spec-/Requesthashes und
STACK/.runtime/compose-review. Aktive Workspace-AGENTS ist im Template exakt
versioniert und zusätzlich zum Handoff gehasht. Alte MA-Runnerfälle bleiben.
JSONbericht bitte im vorhandenen **management**-Reviewrunnerformat schreiben
(binding/reviewer/integrity), IDs F01/F02/F03; die neue F-Vorlage ist nur Beispiel.

## Selbst auszuführende Tests

Aus STACK `./scripts/test-consolidation.sh --phase MA-F0`.

| ID | Beweis |
|---|---|
| F01 | OwnershipTest: falsche volle ID, Name, Mount, fremdes Projekt/Service/Arbeitsverzeichnis vor jedem Operationcallback verweigert; Output0700/0600; eigene relevante Gegenprobe erforderlich |
| F02 | Wirklicher eigener kurzlebiger Compose-PGprobecontainer, natives Image ohne amd64-Emulation; drei logische DBs, server_version_num>=160010 und <170000, PostGIS3.5.2/uuid-ossp nur Management; benanntes frisches Probevolume wird ausschliesslich im eigenen Projekt entfernt |
| F03 | Gate-Negativtest auf MA-F0: fremde SHA, fehlende/doppelte/geskippte IDs, falsches Modell/Report, fehlende Gegenprobe oder veränderte Produktquelle verweigert. Tatsächlicher frischer OpenCode2-/DeepSeek-Lauf mit Read- und Shelltools ist genau dieses Phasenreview; Prozess-/Modell-/Sessionnachweis durch Runner |

Der F02-Probe ist ausdrücklich nur eine Kompatibilitätsprobe, kein zweiter
Anwendungsstack. Keine Foundation-/MA-A–E-Vollsuiten starten. Defaultinventory
auf Nutzer-Composeprojekt im isolierten Checkout ist nicht der Testauftrag:
für eigene Inventurgegenproben eigenen Projektnamen/Fixtures verwenden. Niemals
Originalzustandsdateien oder Nutzercredentials lesen/kopieren. Eigene Docker-
Metadaten lassen sich am Probeprojekt oder einer eigenen Fixture prüfen.

Lokaler Volltest erfolgreich (.runtime/maf-f0-tests.log): native PG16.10,
PostGIS3.5.2, drei DBs, unprivilegierte Fremdressourcen nicht angefasst. Danach
nur lesende State-/Secretreferenzen und neue F-ID-Bindungen ergänzt: gezielte
F01-Unitprobe, F03-Gate für MA-F0 und alter MA-0-Regressionsfall erneut erfolgreich.
PG-Dockerfile/Abhängigkeiten unverändert. Alle ausgewählten Nutzerressourcen
anschliessend mit denselben IDs/Images/Mounts/Runningzuständen nachgeprüft.

## Nicht betroffen / Grenzen

Fachmodell, Cayenne, Audit-/Authz-/JWT-SQL und Applikationscode unverändert.
Keine Fach-/Identitäts-/Dateimigration bisher, keine Löschung. Noch kein F1-Stack,
noch kein Recreate-/Restore-/Userjourney-Nachweis. LOCAL_CUTOVER_PENDING.
Nur lokale Commits; kein neuer Push-/Releaseauftrag in MA-F.
