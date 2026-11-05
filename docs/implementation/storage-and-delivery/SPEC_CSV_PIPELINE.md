# SPEC_CSV_PIPELINE – ein gemeinsamer GRETL-Ablauf für replace und append

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md), Schwerpunkt MA-G4. Ausführungsmodell ist die vorhandene Jenkins/GRETL-Toolchain, kein Wechsel zu Hop, Kestra oder gretl-runtime. Gegenwartsbehauptungen und externe Quellen stehen in [SOURCES.md](SOURCES.md).

## 1. Ein technischer Ablauf, viele fachliche Datensätze

TOPICS enthält künftig beispielsweise:

```text
runner/
  build.gradle                 # genau ein Einstieg ingestCsv
  settings.gradle
  src/... oder buildSrc/...    # nur notwendige wiederverwendbare Helfer
  run-csv.sh                   # fester begrenzter Aufruf, keine User-Shell
contracts/
  <definition-key>.json        # deklarativer CSV-/INTERLIS-Vertrag
models/
  <pinned>.ili                # Datenmodelle, nicht die alten Katalogtransportmodelle
fixtures/
  <dataset>/...               # kleine synthetische/öffentliche Testdaten
```

Bestehende geeignete GRETL-Tasks/-Helfer wiederverwenden. Eine Datenvertragsdatei pro unterschiedlichem Schema ist **kein eigener Job**. Dieselbe Implementierung verarbeitet sämtliche CSVverträge. Keine Möglichkeit, pro Contract freie Groovy-/SQL-Skripte hochzuladen oder in Requestparametern zu wählen.

Fachmetadaten, Eigentümer, Zugänglichkeit und Lieferrechte bleiben in PG. Technische Definitionsdateien enthalten keine Benutzerlisten, keine OIDC-Gruppen, keine Leserechte und keine S3-Schlüssel. Bestehende Organisationsordner sind nicht mehr die Quelle des Livekatalogs.

## 2. Bindender CSVvertrag

`CsvDefinition` wird als kleines, versionsgebundenes JSONschema dokumentiert. Mindestens:

| Feld | Vertrag |
|---|---|
| `definitionKey`, `contractVersion` | Stabile technische Identifikation; kein Klassenname aus Userinput. |
| `modelName`, `modelVersion`, `qualifiedTableName` | Konkreter INTERLIS-Datenmodell-/Klassenausschnitt, tatsächlich vom CsvValidator unterstützt. |
| `modelFiles` / `modelSetSha256` | Hashes **aller** aufgelösten Modellabhängigkeiten; mutable Online-Repositories allein sind nicht reproduzierbar. |
| `dialect` | UTF-8, Headerpflicht, Separator, Quote, Zeilenende-/BOMbehandlung, Nullkonvention. Explizit statt Plattformdefault. |
| `columns` | Geordnete, exakt geprüfte Abbildung CSVheader → Modellattribut → CHtyp/Exporttyp. Aus Modell ableiten oder maschinell dagegen validieren. |
| `businessKey` | Falls fachlich vorhanden aus Modell-UNIQUE bzw. genehmigter Definition; für append-Duplikatkontrolle. Kein zufälliger Zeilenhash als fachlicher Ersatz. |
| `limits` | Bytes, Zeilen, Zellenlänge; harte technische Obergrenzen gelten zusätzlich. |
| `allowEmptyReplacement` | Standard false; leere vollständige Ersetzung verlangt ausdrückliche technische/fachliche Freigabe, kein versehentlicher Datenverlust. |

Vollständiger Vertragshash umfasst relevante Typen, Dialekt, Semantik und Modellset. Laufender Auftrag bleibt an diese Version gebunden. Ein neuer Check-in verändert bereits angenommene Aufträge nicht. Runtimebundle/Contractregistry müssen denselben Hash verwenden; unerwartete Abweichung → geschlossener Fehler.

Unterstützter MVP-Typumfang: Text/MTEXT, Boolean, geordnete Enums, begrenzte Ganzzahlen/Dezimalzahlen, Datum und ausdrücklich UTC-normalisierte Zeitwerte. Keine automatische Interpretation von Geometrien, verschachtelten Strukturen oder beliebigen BAGs in CSV. Nicht unterstützte Modelltypen vor Auftragsannahme bzw. spätestens vor Load ehrlich ablehnen, nicht alles als String „irgendwie“ importieren.

Null, leere Zeichenkette, führende Nullen, Dezimalkomma, Quotes, mehrzeiliges MTEXT und Header-Casing sind zu spezifizieren und mit den echten Pilotmodellen abzugleichen. Kein stilles Locale-Raten. Für die technischen Defaults z.B. UTF-8, `;` oder `,` je gepinnter Definition; nicht allen vorhandenen Daten einen erfundenen gemeinsamen Separator aufzwingen.

## 3. Verarbeitungsschritte

| Schritt | Wirkung | Darf aktuellen Stand verändern? |
|---|---|---|
| `verifyExecutionPlan` | IDs/Fence/Hash/Contract prüfen, Inputhash erneut lesen | Nein |
| `validateIncomingCsv` | Echter GRETL `CsvValidator`, echte Modellregeln und Typen | Nein |
| `prepareSnapshot` | Replace: nur neue Daten. Append: bisheriger vollständiger Stand + Delta | Nein |
| `validateCompleteSnapshot` | Ganze Kandidatendaten inkl. interner/übergreifender Unique-/Setregeln | Nein |
| `loadPrivateCandidate` | Neue immutable CH-Kandidatentabelle, feste UUIDnamen | Nein |
| `verifyCandidate` | Counts/Typen/Datenhash prüfen, kein teilweiser Load | Nein |
| `exportDistributions` | Vollständiges CSV/XLSX/Parquet aus demselben Snapshot | Nein |
| `storePrivateArtifacts` | Input/Report privat, Outputs unter reservierten Distributionkeys | Nein |
| `buildResultManifest` | Belegte Hashes/Counts/Versionen und Bindung | Nein |
| `completeViaAdmin` | Frische Rechteprüfung und PG-Fachcommit | **Ja, zentral und ausdrücklich** |
| `projectCurrentSqlView` | Abgeleitete CH-current-Sicht aus aktuellem PG-Soll | Ja, nach Commit, kontrolliert und wiederholbar |

Keine alten Tasks wie `publishToDatenportal`, `uploadCurrentManifest`, `reloadPortal`. Der neue Einstieg `ingestCsv` erzeugt ein Ergebnis für den zentralen Abschluss, nicht nochmals einen filebasierten Katalog.

## 4. Echte CsvValidator-Verwendung

Der vorhandene GRETL-Task bietet Header-/Delimiter-/Separator-/Encoding-Einstellungen. In G0 den konkreten Task-/Implstand und `validationOk`/`failOnError`-Verhalten prüfen [R6]. In der echten Pipeline gilt `failOnError=true`; `getDataFiles()==null` oder leere Liste dürfen nicht als erfolgreiche Validierung durchgehen. Input muss nachweislich existieren, Größen-/Hashprüfung bestanden haben und genau eine vereinbarte Tabelle bedienen.

Ein Prozess-Exitcode allein genügt nicht: strukturierter Validatorbeleg mit Modellset, ausgeführter Prüfung, Fehlerzahl und erfolgreichem Ergebnis. Warnungen sind dokumentiert; ein nicht ausgeführter Validator bleibt Fehler. Zeilen mit invaliden Typen oder referenzierten Constraints werden nicht einfach ignoriert oder als NULL eingefügt.

Bei append das Delta **und** den gesamten neuen Snapshot prüfen. Eine nur im Gesamtbestand doppelte Fach-ID muss die Veröffentlichung verhindern. Wiederverwendung einer bestehenden Implementierung ist gewünscht, solange diese Semantik tatsächlich erfüllt ist.

## 5. Replace/append und Historie

### Replace

Die CSV definiert den vollständigen neuen Stand der gewählten Ausgabe. Alte Versionen und deren Outputs bleiben unverändert. Nicht `TRUNCATE` auf der aktuellen Tabelle und danach schrittweise neu laden. Auch bei leeren Inputs gilt der explizite Vertrag.

### Append

Das Backend legt beim reservierten Dataset-Dispatch die Basisversion fest. Aus deren vollständigen Daten und dem Delta wird ein **neuer vollständiger Snapshot** erzeugt. Keine Mutation der früheren Version. Im MVP ist append kein upsert: eine kollidierende fachliche Schlüsselzeile wird abgewiesen, nicht still ersetzt. Wenn das Modell keinen Geschäftsschlüssel definiert, ist append ein wohldefiniertes Multiset-Anfügen; mögliche identische Datensätze sind dann fachlich zulässig, Retries derselben Submission aber trotzdem nicht doppelt wirksam.

Ein neuer Vertrag oder eine inzwischen anderweitig veränderte Basis bewirkt `CONFLICT`; kein stilles Rebase eines laufenden Auftrags. Zwei Lieferungen desselben Datasets werden geordnet; verschiedene Datasets können parallel verarbeitet werden.

### Identität

Submission-ID, Execution-ID, DataVersion-ID, Distribution-ID und fachliche Ausgabe-ID sind unterschiedliche Begriffe. „2026“ ist eine Ausgabe, nicht die ID jedes technischen Neuladens. Korrekturlieferungen erzeugen neue Versionen innerhalb dieser Ausgabe.

Datenhash und Dateihash unterscheiden: Originaldatei-SHA256 belegt die angelieferten Bytes; Snapshotdatenhash belegt normalisierte vollständige Daten; Exporthash belegt ein konkretes Format. Eine vom XLSX-Writer variierende ZIP-Metadatei ist kein Grund, Originaldaten als verändert zu behaupten.

## 6. ClickHouse-Datenhaltung

Eine tatsächlich vorhandene geeignete S2-Implementierung kann die folgenden Verantwortlichkeiten erfüllen. Keine Verfügbarkeit behaupten, bevor der Code und seine Tests gefunden wurden. Falls sie fehlt, eine **kleine** explizite Implementierung innerhalb des Runnerbereichs erstellen, nicht eine neue allgemeine ili2db→ClickHouse-Plattform.

Empfohlener MVP-Vertrag:

- Eigener technischer Bereich `di_data` für versionierte vollständige Tabellen, getrennt vom bestehenden `foundation`-Bereich.
- Eindeutige servergenerierte Kandidatennamen aus DataVersion-/Execution-UUID, z.B. `v_<hexuuid>_<attempt>`; keine SQL-Identifier aus hochgeladenen Titeln.
- Erst vollständig laden, synchrones Ergebnis und Counts/Datenhash prüfen. `async_insert` ohne überprüfte Fertigstellung ist unzulässig.
- Neue Kandidatentabellen sind für gewöhnliche Foundation-/Superset-/DBeaverkonten **nicht** lesbar. `SELECT ON *.*` oder pauschales `di_data.*` für normale Nutzer darf nicht neu vergeben werden.
- Der zentrale Projector führt eine stabile current-Sicht je Dataset/Ausgabe, z.B. `di_public_sql.ds_<uuid>_current`, nur auf den aktuell committeten Snapshot. Historische Snapshotreferenzen bleiben eindeutig.
- Geeignete ClickHouse-Funktionen am gepinnten Server prüfen. `EXCHANGE` hat Enginevoraussetzungen; `CREATE OR REPLACE VIEW`-Verfügbarkeit und Rechteverhalten testen. Keine behauptete Atomarität zwischen PG und CH [S6/S7].

Die genaue Datenbank-/Namenskonvention ist in G0 verbindlich zu fixieren; bestehende gute S2-Snapshotregeln haben Vorrang vor unnötiger Neuentwicklung. Entscheidend sind Immutable-Historie, keine Candidateoffenlegung, keine doppelten Appendwirkungen und ein überprüfbarer aktueller Stand.

Technische Konten: Loader darf benötigte Kandidaten im eigenen Bereich erstellen/befüllen, nicht Accounts/Grants verwalten. Projector darf nur definierte Views/Referenzen projizieren. Der alte Defaultadmin wird nicht an Uploadbenutzer ausgegeben. Positive JDBCtests verwenden technische Lesekonten oder eigene eng begrenzte Testrollen, nicht einen neu eröffneten personenbezogenen SQLzugang.

## 7. Typen, Export und Nachweise

- Decimal mit exakter Skalierung, kein Zwischenweg über binäres `double` für fachliche Dezimalwerte.
- IDs mit führenden Nullen bleiben Text, wenn das Modell Text festlegt.
- `DATE` bleibt Datum. Zeitwerte nach dem vorhandenen UTCvertrag, nicht Hostlokalzeit. Zeitzonenprobe einschliessen.
- String/Enum/Boolean müssen in CSV, CH, XLSX und Parquet dieselbe Bedeutung behalten.
- XLSX: Texte mit `=`, `+`, `-`, `@` als Textzellen, niemals als Formeln; Worksheetgrenzen prüfen. Kein stilles Abschneiden bei >1'048'576 Zeilen oder zu langen Zellen.
- Parquet: Typen tatsächlich prüfen, nicht CSVbytes unter `.parquet` ablegen. Zulässige Bibliothek/Version pinnen.
- CSV: dokumentierter maschinenlesbarer Dialekt; Daten nicht durch stilles Excel-Escaping verändern. Der Download ist ein Attachment, kein ausführbares HTML.
- Alle Outputs basieren auf **demselben** vollständigen Snapshot; append liefert nicht bloss das Delta als aktuellen Download.
- Hashen/Upload möglichst streamend, bounded Memory. Arbeitsverzeichnis je Run, keine global gemeinsam überschriebenen `data.csv`/`result.json`.

## 8. Klassen-/Methodenplan Runner

Package z.B. `ch.so.agi.dateninfrastruktur.ingest` in einem kleinen wiederverwendbaren TOPICS-Buildmodul; tatsächliche Sprache Java/Groovy passend zum bestehenden GRETL-Gradleweg.

| Typ / Methode | Vertrag |
|---|---|
| `CsvExecutionPlanReader.read(path)` | Striktes Schema, IDs/Hash/Targetallowlist, unbekannte Felder/Versionsabweichung ablehnen. |
| `CsvDefinitionRegistry.resolve(key, expectedHash)` | Nur freigegebene gepackte Definition; kein Netzfetch zu Benutzer-URLs. |
| `ModelSetResolver.resolveAndVerify(definition)` | Alle ILI-Abhängigkeiten mit SHA; keine stille neueste Version. |
| `IncomingCsvVerifier.verify(file, plan)` | Existenz, Größe, Hash, Encodingvorprüfung, limits. |
| `CsvValidationAdapter.validate(file, definition)` | Tatsächlicher CsvValidator/Report, keine Ersatzregexvalidierung. |
| `SnapshotBuilder.replace(...) / append(...)` | Vollständiger Kandidat, alte Version unverändert, deterministisches Typschema. |
| `SnapshotValidator.validateComplete(...)` | Modellregeln über Gesamtbestand; liefert Counts/Digest. |
| `ClickHouseSnapshotWriter.stage(...) / inspect(...) / verify(...)` | Neue eindeutige Kandidaten, synchrones Ladeergebnis, sichere SQLidentifier. |
| `DistributionExporter.exportCsv/Xlsx/Parquet(snapshot, outputPlan)` | Formate typkorrekt, keine Formeln/Trunkierung, große Dateien nicht komplett im RAM. |
| `PrivateArtifactWriter.writeImmutable(key, source, evidence)` | Kein Überschreiben anderer Bytes; bei existenten identischen Bytes geprüfter No-op. |
| `CsvResultManifestWriter.write(plan, validation, snapshot, artifacts)` | Eindeutiger Schema-/Planbezug, keine Credentials, bounded JSON. |
| `ExecutionWorkspace.create/cleanupOwned` | Nur eigene Runpfade, kein globales Workspace-Löschen. |

`ingestCsv` komponiert diese Schritte; keine Klasse „GodPublisher“, die wieder Katalog, IAM und ETL in einer Groovy-Datei vermischt. Vorhandene geeignete GRETL-Tasks und SQL-Dateien dürfen Teile übernehmen. Die zentrale Autorisierung und die PG-Versionannahme werden **nicht** im Runner nachprogrammiert.

## 9. Wiederanlauf und Teilfehler

| Fehlerzeitpunkt | Erwartung |
|---|---|
| Vor/bei Validator | Keine CH-/Downloadpublikation, klare Validierungsablehnung. |
| Halb geladene CH-Kandidatentabelle | Nicht aktuell/nicht lesbar für normale Nutzer; neuer Attempt oder vollständige bestätigte Reparatur, kein Doppelappend. |
| Dateioutput teilweise hochgeladen | Fehlender/abweichender Hash verhindert READY_TO_COMMIT. |
| S3/CH fertig, Admin nicht erreichbar | Auftrag bleibt privat/uncommitted, Nachweise können erneut übermittelt werden. |
| Rechte während Verarbeitung entzogen | Commit abgewiesen; kein alter Grantcache. |
| PGcommit erfolgreich, Antwort verloren | Gleiche Submissionabfrage zeigt dieselbe Version, kein zweiter Datensatz. |
| CH-current-Projektion nach PGcommit fehlerhaft | Status COMMITTED, keine fachliche Rückabwicklung; Projector repariert genau den aktuellen Sollstand. |
| Alter Worker meldet später Erfolg | Fence/Executionkonflikt, keine Änderung an neuerem Stand. |

Fehlgeschlagene Kandidaten sind bezeichnet und nicht öffentlich. Eine kleine explizite Bereinigung darf nur nachgewiesen unreferenzierte, beendeten Attempts gehörende Objekte entfernen; kein pauschales Bucket-/Tabellen-Purge. Im MVP keine automatische allgemeine Garbage-Collectionplattform erforderlich, aber kein unbegrenztes anonymes Testartefakt-Wachstum im Abschlusslauf.

## 10. Pilot und Abnahme

Zwei kleine Datensätze, verschiedene OwnerOffices oder zumindest klar getrennte Scopes. Einer open, einer restricted. Mindestens drei Annahmen: erster Replace, korrigierender Replace, Append; alte vollständige Stände bleiben prüfbar. Vorhandene passende Pilot-CSV/Modelle nutzen, sonst klar synthetische versionierte Fixtures. Öffentliche Originale nicht als plötzlich vertraulich darstellen.

Ungültige Typen, fehlende Pflichtfelder, doppelte Fach-ID über Alt+Delta, falsches Modell, zu große Datei und manipulierte Plan-Targets müssen wirklich fehlschlagen. Spätestens G5 erfolgt der Weg über die Pluginoberfläche, nicht nur ein direkter Testaufruf des Java-Service.

## 11. Ausführungs- und Formatvertrag als implementierbarer Einstieg

Der feste Operator-/Pluginaufruf kann beispielsweise lauten:

```text
run-csv --plan <serverseitiger-absoluter-planpfad>
        --input <runworkspace>/input.csv
        --output <runworkspace>/result
```

`run-csv` übersetzt ausschliesslich diese geprüften Pfade in den einen vorhandenen Java17-/Gradle-GRETL-Aufruf mit Task `ingestCsv`. Das konkrete Wrapperlayout aus TOPICS übernehmen oder konsistent neu strukturieren. Benutzer wählen weder `-p`, Task, Repositorybranch, Init-Script noch Java-Optionen. Alle Childprozesse mit Argumentlisten, festen Arbeitsverzeichnissen und geprüftem Exit starten. Keine interpolierten Shellbefehle aus Kommentaren oder CSVheadern.

Für Typ-/Formattests braucht es mindestens einen kleinen repräsentativen Vertrag mit Text-ID `00123`, Decimal ohne Rundungsverlust, Datum, Boolean/Enum, nullable Text und mehrzeiligem MTEXT. Diese Testwerte sind keine zusätzlich verlangten fachlichen Attribute der echten Pilotdatensätze, sondern eine eigene technische Fixture. Beide echten Piloten müssen unabhängig davon mit ihren tatsächlichen Modellen verarbeitet werden.

Bereits im Themenrepo vorhandene valide CSV-Datenmodelle werden nicht im Zuge der Katalogbereinigung gelöscht. „Kein Datasheet/PublishedCatalog“ betrifft den alten Metadaten-Livevertrag, nicht INTERLIS als Datenvalidierungsmodell.
