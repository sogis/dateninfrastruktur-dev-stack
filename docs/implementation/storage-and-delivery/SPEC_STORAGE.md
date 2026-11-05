# SPEC_STORAGE – ein privater Bucket ohne Legacybetriebsart

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Schwerpunkt MA-G1; neue Upload-/Outputpfade werden in G3/G4 angeschlossen. Ausgangscode und technische Quellen: [SOURCES.md](SOURCES.md), R1/R2 und S1.

## 1. Speichervertrag

Der **einzige anwendungseigene Datenbucket** heisst `ch.so.daten`. Sein Name ist technische Deploymentkonfiguration, keine fachliche Eigenschaft einer Distribution. In der lokalen Ziellaufzeit ist kein zweiter Datenbucket dieser Anwendung nötig.

```text
ch.so.daten/
  ingestion/<submission-uuid>/input.csv
  ingestion/<submission-uuid>/attempts/<execution-uuid>/validation.json
  ingestion/<submission-uuid>/attempts/<execution-uuid>/result.json
  downloads/<distribution-uuid>/data.csv
  downloads/<distribution-uuid>/data.xlsx
  downloads/<distribution-uuid>/data.parquet
```

Jede Distribution hat eine eigene UUID; die drei Beispielzeilen stehen deshalb real unter unterschiedlichen UUID-Verzeichnissen. Derselbe Objekt-Key wird nie mit neuen Daten überschrieben. Vor dem PG-Commit abgelegte Outputs sind allein durch ihre Existenz nicht verfügbar. Der Origin sieht nur `downloads/`; die Authorization API verlangt eine existierende, verfügbare Distribution unter einem freigegebenen Dataset/Ausgabe/Version.

`ingestion/` wird nicht unter `/downloads/` gemappt. Prüfberichte werden über die berechtigte Anlieferungsoberfläche in bereinigter Form ausgegeben, nicht über einen anonymen Dateilink. Kein `current.json`, kein `catalog.duckdb`, keine publizierte Gesamt-XTF als Livequelle. Historische Datenversionen behalten eigene unveränderliche Outputs.

## 2. Technische Identitäten

| Identität | Rechte | Verwendung / Ablage |
|---|---|---|
| Storage-Administrator | Garage-Verwaltungs-API für Bucket/Keys; kein Benutzerlogin | Ausschliesslich explizite Setup-/Upgrade-Tools, private Garagekonfiguration. Nicht Jenkins-Web-/Job-ENV. |
| `di-storage-writer` | Lesen + Schreiben im einen Bucket; kein Bucket-Owner, kein CreateBucket | Vertrauenswürdiger CSV-Verarbeitungsjob und ausgewählte Operatoren, aus Jenkins Credentials bzw. Compose-Toolsecret. |
| `di-storage-reader` | Lesen im einen Bucket; kein Schreiben/Löschen/Owner/CreateBucket | rclone-Origin und ein lesender, expliziter Verifikationsoperator. |

APISIX, Sodata und das Admin-Webbackend haben **keine S3-Credentials**. Admin prüft authentifizierte Ergebnisbelege der vertrauenswürdigen Verarbeitung; ein Uploadbenutzer darf solche Belege nicht selbst erzeugen. Separate technische Verifikationsjobs dürfen den Readerschlüssel nutzen.

Garage-Bucketrechte sind keine IAM-Prefixrechte. Der Writer kann technisch mehr als einen Dataset-Prefix lesen/schreiben; der Reader kann technisch den Bucket lesen. Prefixkonfiguration des Origins und feste Jobpläne begrenzen die normalen Wege, sind aber keine zusätzliche native S3-ACL. Keine unhaltbare Append-only-/Object-Lock-/Create-only-Garantie behaupten. Writer/Plattformoperatoren gehören zur vertrauenswürdigen Infrastruktur; untrusted Benutzer dürfen weder Skripte noch Credentials konfigurieren.

Die Begriffe `GARAGE_DEFAULT_*`, `GARAGE_MANAGED_*`, `DI_MIGRATION_IMPORT_KEYS` und öffentlicher Publisher entfallen aus **aktiver** Konfiguration. Neue eindeutige Namen beispielsweise:

```text
DI_STORAGE_BUCKET=ch.so.daten
DI_STORAGE_ENDPOINT=http://garage:3900
DI_STORAGE_REGION=garage
DI_STORAGE_WRITER_ACCESS_KEY / DI_STORAGE_WRITER_SECRET_KEY
DI_STORAGE_READER_ACCESS_KEY / DI_STORAGE_READER_SECRET_KEY
```

Die tatsächlichen Werte bleiben nur in den vorgesehenen privaten Dateien/Credential Stores. Ein Parser muss Sonderzeichen korrekt behandeln; niemals mit simplen Split-/Shellinterpolationsoperationen Geheimnisse beschädigen. Keine Secretwerte in URLs, CLI-Argumenten, `docker compose config`-Reports oder Testausgaben.

## 3. Frische Einrichtung und erneutes Setup

`GarageProvisioner` ersetzt die bisherige Fresh-/Migration-Verzweigung in `services/garage/setup-compose.py`. Pythonfunktionen sind ausreichend; folgende Schnittstellen müssen erkennbar sein:

| Funktion | Ein-/Ausgabe und Verhalten |
|---|---|
| `load_storage_target(runtime) -> StorageTarget` | Aktiver Compose-Kontext, interner Endpoint, Bucket, tatsächlich identifizierter Garage-Service. Keine globalen AWS-ENV oder impliziten Cloudendpunkte. |
| `ensure_private_bucket(target) -> BucketIdentity` | Erzeugt fehlenden eigenen Bucket oder prüft bestehenden. Websitefreigabe deaktiviert; unbekannte fremde Identität/Zuordnung ablehnen. |
| `ensure_key(kind, stored_reference) -> KeyReference` | Vorhandenen Schlüssel erhalten, fehlenden einmal erzeugen. Existierender Key mit anderem Secret ist Fehler, nicht Anlass für stille Rotation. |
| `reconcile_permissions(bucket, writer, reader)` | Exakte Sollrechte herstellen; alte anwendungseigene Keys nach Umstellung entziehen. Keine Abhängigkeit von einem Migrationsflag. |
| `verify_storage_policy(target) -> PolicyReport` | Tatsächliche Key-/Bucket-/Websiteeinstellungen prüfen, keine Secretwerte ausgeben. Enthält Liste erlaubter Key-IDs nur im privaten Detailbericht. |
| `render_reader_config(reader, target)` | `origin.conf` mit ausschliesslich Readercredentials, keine Fallbacks. |
| `render_writer_config(writer, target)` | Nur für explizite Tools; Webprozess/Origin bekommt diese Datei nicht. |
| `write_secrets_atomically(...)` | Private Dateimodi, atomarer Austausch, Verlust der vorherigen Secretdatei vermeiden. |

Gültigkeitsregel: `setup(setup(S))` verändert weder Datensätze/Objekte noch Schlüsselinventar und Secrets. Falsche Rechte dürfen auf Sollzustand korrigiert werden; diese Korrektur wird als technische Operation dokumentiert. Fehlende Credentials verursachen einen geschlossenen Fehler, niemals Zugriff mit einem allgemeineren Key.

Garage nicht dauerhaft mit der alten `--default-bucket`-/Defaultkey-Initialisierung starten, wenn diese bei jedem Start alte Berechtigungen oder obsolete Keys wiederherstellt. Normalstart benötigt nur vorhandene Garagekonfiguration und Volumes. Ein leerer Neuaufbau wird ausschliesslich durch den expliziten Setupjob initialisiert.

Die bestehenden Startskripte bleiben die **einzige** aktive Lifecycle-API. Einmalige Toolcontainer sind Compose-Services/Profile; keine zweite `docker run`-Orchestrierung.

## 4. Origin, Gateway und kontrollierte Auslieferung

Origin verwendet den einen Reader und `ch.so.daten/downloads`, bleibt read-only, ohne Directorylisting, ZIP und schreibende Methoden. Die getestete Behandlung von HEAD, Range, ETag/304 und `Cache-Control: no-store` erhalten. Ein HTTP-401/403/503 der Autorisierung darf nie durch einen direkten S3-Redirect umgangen werden.

Die einzigen fachlichen Datei-URLs sind `/downloads/<distribution-uuid>/<safe-filename>`. Keine Presigned-Download-URLs an Benutzer, weil sie bis Ablauf der Signatur an einem späteren Entzug vorbeiführen würden. Keine Aliasroute für alte Bucket-URLs. Ein generisches Default-Deny ist zulässig; eine alte URL-Whitelist allein reicht nicht als Bypassschutz.

Origin/Admin/Garage haben im normalen Compose keine direkten Hostports. Intern verfügbare S3-API ist weiterhin signaturpflichtig. Auch ein `open`-Dataset muss über dieselbe aktuelle Authorization-Entscheidung laufen. Bei DB-/API-Ausfall werden **alle verwalteten** neuen Downloads verweigert.

Statische APISIX-Konfiguration wird als technische Konfiguration gerendert, nicht pro Grant geändert. Bei Dateiaustausch und bestehenden Einzeldatei-Bindmounts kontrolliert neu erstellen/remounten; nicht annehmen, dass ein atomarer Hostrename die alte Containerdatei sicher ersetzt. Ein Konfigurationsrender allein ist kein Nachweis des wirksamen Routings.

## 5. Einmalige Umstellung des vorhandenen Entwicklungsbestands

### 5.1 Berechtigter Löschumfang

Der Nutzer hat den alten **lokalen** Inhalt von `ch.so.daten` freigegeben. Das Verfahren muss die konkrete Garage-Instanz und den internen Bucket-Identifier verifizieren. Der gleiche globale Name bei AWS oder einer fremden Instanz ist **kein** zulässiges Löschziel.

Vorbereitung erfasst lesend: Compose-Projekt/Instanzkennung, Garage-Container/-Volumezuordnung, Bucket-ID, Objektliste mit Größe/Hash/Metadaten, aktuelle PG-Distributionreferenzen, alte Keys/Aliase und Websitezustand. Keine Geheimnisse im Modellprompt. Eine kleine private Umstellungsdatei reicht; kein allgemeines Backup-/Migrationframework.

### 5.2 Ablauf ohne Verlust registrierter privater Dateien

1. Neue technische Konfiguration und Code auf isolierten synthetischen Quellen beweisen; unabhängiges G1-Review.
2. Kurzes lokales Wartungsfenster: betroffene anwendungseigene Schreiber stoppen bzw. Ausführung sperren. Sourceinventur erneut prüfen. Downloads dürfen kurz 503 liefern, niemals unautorisiert Daten liefern.
3. Aus PG alle auf dem alten privaten Backend referenzierten Objekte erfassen, einschliesslich historischer und zurückgezogener Distributionen. Referenzen auf weitere fachlich benötigte Objekte ausdrücklich aufnehmen.
4. Alte Objekte im identifizierten `ch.so.daten` **einmalig** löschen. Kein Backup dieser ausdrücklich entbehrlichen Altobjekte erforderlich. Operation nur gegen die gebundene Inventur; keine ungezielte rekursive Löschung aller Buckets.
5. Noch benötigte Objekte aus `di-managed-private` mit unveränderten Keys, Bytes und benötigten Content-Metadaten nach `ch.so.daten` übertragen. Hash und Größe wirklich prüfen, ETag nicht pauschal als SHA/MD5 interpretieren.
6. Bei Wiederanlauf nach Teilfehler: bereits geprüfte neue Objekte **nicht** erneut mit dem alten Purgeschritt löschen. `PURGED → COPYING → VERIFIED → SWITCHED` wird dauerhaft gejournalt. Zielobjekt mit anderen Bytes verursacht Konflikt, kein Überschreiben.
7. Distribution-Schema/Runtime umstellen, Objekt-Keys und UUIDs erhalten; neue Originroute prüfen. Dieselben erlaubten/verweigerten Downloads müssen denselben Inhalt bzw. Status liefern.
8. Erst nach verifiziertem Ziel `di-managed-private` entfernen. Unbekannte, nicht als entbehrlich nachgewiesene Sourceobjekte sind ein enger Übernahmeblocker, keine pauschale Löschfreigabe. Bereits bekannte reine Testcanaries können nach Inventur als entbehrliche Fixtures behandelt werden.
9. Alte anwendungseigene Keys/Aliase und obsolete Websitekonfiguration entfernen. Einen evtl. vorhandenen reinen Foundation-Smoke-Bucket nur entfernen, wenn Inhalt und Eigentümerschaft ausschliesslich nachgewiesene Testfixtures sind. Fremdbuckets nicht anfassen.
10. Lokalen Endzustand prüfen; Umstellungstool aus aktiver Compose-/Operator-API entfernen. Keine fortdauernde „Migration Import Keys“-Betriebsart.

`PrivateBucketCutover.plan()` ist lesend; `apply(bound_plan)` verlangt unveränderte Instanz-/Bucket-/PG-Bezüge. Bei einem erneuten Aufruf nach abgeschlossenem Cutover **abbrechen oder nur lesend verifizieren**, niemals nochmals leeren. Nach neuen Lieferungen darf das Tool keinen alten Baselinezustand herstellen.

### 5.3 Grenzen

Kein `down -v`, kein Garage-Volumereset, keine Ersetzung der Management-DB durch Seedfixtures, kein Löschen bestehender AccessDecisions/Auditzeilen. Private Dateien sind nicht automatisch entbehrlich, nur weil die Umgebung ein MVP ist. Nichtreferenzierte alte öffentliche Entwicklungsartefakte benötigen dagegen keine Kompatibilitätsroute.

## 6. Datenmodell und Verifikationscode

`Distribution.storageProfile` und `legacyAccessUrl` entfernen. `objectKey` bleibt mandatory und innerhalb des einzigen Backends eindeutig. Das Datenmodell kennt keine Bucket-/Endpointauswahl pro Datei. G1 muss alle Constructor-/DTO-/Cayenne-/View-/Fixture-Verwendungen mitändern; ein ignorierter optionaler `storageProfile`-Parameter wäre verbotener Kompatibilitätscode.

Vorhandenen `RclonePrivateObjectVerifier` bzw. Operator auf `verify(canonicalKey, expectedEvidence)` anpassen. Der technische Endpoint kommt aus festem Runtimevertrag. Keine Übergabe eines vom Benutzer bestimmten Profils oder einer URL. Die fachliche Veröffentlichung neuer Lieferungen verwendet ab G4 den vollständigen Ergebnisvertrag; der Operator darf kein separater Weg sein, ungültige neue CSV ohne Validierung als angenommen zu markieren.

## 7. Neue Uploads und immutable Outputs

Input wird zunächst begrenzt im Jenkins-Uploadspool gespeichert; Originalhash und Größe sind Bestandteil der versiegelten Submission. Der technische Job archiviert die Eingangsdatei unter `ingestion/` und schreibt finale Outputs unter vorher reservierten Distribution-UUIDs. Vorhandene Objekte mit gleichem Key und gleichem Hash können nach Prüfung als wiederholter Schritt akzeptiert werden. Andere Bytes sind ein Fehler, nie ein erfolgreicher Retry.

Anwendungsseitiges „nie überschreiben“ ersetzt keine S3-WORM-Garantie. Diese Grenze dokumentieren. Downloads prüfen die aktuelle PG-Verfügbarkeit, nicht die Existenz irgendeines Keys. Ein Benutzer kann aus einer erratenen UUID keinen Stagingstand beziehen.

## 8. Abnahme MA-G1

Frischaufbau und Bestandsumstellung erreichen dieselbe Policy. Der Reader kann ein existentes Objekt lesen, aber weder schreiben noch löschen; der Writer kann notwendige Objektoperationen, aber weder Bucket erstellen noch Ownerrechte verändern; anonyme GETs werden verweigert. Keine weiteren Writercredentials in normalen Webcontainern. Zweites Setup, Neustart und Recreate erhalten Rechte/Keys/Dateien. Alte URL oder alter allgemeiner Key liefert keine geschützten Bytes. Siehe G10–G19 in TEST_PLAN.
