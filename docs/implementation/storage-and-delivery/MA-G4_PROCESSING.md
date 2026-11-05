# MA-G4 – CSV-Verarbeitung, private Snapshots und SQL-Projektion

Der einzige normale Jenkins-Prozessor ruft den versionierten
`TOPICS/runner` mit Java 17 und dem aus G0 gebundenen Offline-Bundle auf.
Der feste Gradle-Einstieg `ingestCsv` führt die wirklichen GRETL-CsvValidatoren
für Eingang und vollständigen Snapshot mit `failOnError=true` aus. Das
Validatorbundle meldet ilivalidator 1.15.0; die Vertragsschicht verifiziert die
separat mit ili2c 5.6.9 erzeugten IMD-Metadaten. Die zur Laufzeit gelesenen
Modelle stammen ausschliesslich aus dem geprüften Runnerbundle.

Die zwei Pilotverträge verwenden die unveränderten Modelle
`SO_Bevoelkerung_Altersstruktur_20261015` und
`SO_Bevoelkerung_Gemeinde_Geschlecht_20261015`. Die separate synthetische
Typfixture beweist Text/MTEXT, Bool, geordnete Enumwerte, Ganzzahl, Dezimal,
Datum und UTC-Zeitpunkt. Ihre Werte sind keine amtlichen Daten.

- UTF-8, BOM abgewiesen, LF, exakter Header, festes Trennzeichen und
  doppelte Anführungszeichen. Ein leeres Feld bedeutet NULL; ein separates
  leeres Textliteral gibt es in diesen Verträgen nicht. Zahlen benutzen
  den Punkt ohne Locale-Raten. Datumswerte liegen zwischen 1900 und 2299;
  Zeitpunkte verlangen einen Offset oder Z, werden millisekundengenau
  nach UTC normalisiert und in Parquet als Timestamp mit Zeitzone abgelegt.
- Replace erzeugt einen vollständigen neuen Stand. Append liest das
  gebundene private Basis-CSV, prüft Bytes und normalisierten Datenhash,
  fügt Delta an und prüft den Gesamtbestand gegen das Modell. Es gibt
  kein Upsert oder stilles Rebase. Leere Ersetzungen sind für alle
  freigegebenen Verträge ausgeschlossen.
- Der normalisierte Datenhash umfasst geordnete Zeilen aus UTF-8-JSON-Arrays
  mit fachlich normalisierten Strings oder NULL und einem LF pro Zeile.
  Dieser Hash unterscheidet sich vom Original- und Ausgabe-Dateihash.
  Der private ClickHouse-Kandidat hat eine technische Ordnungsnummer; die
  abgeleitete Sicht enthält nur Fachspalten.
- XLSX schreibt Werte gestreamt, Datum als Datumzelle, Text immer als Text
  und Dezimalwerte ohne binären Zwischenwert. UTC-Zeitpunkte bleiben
  explizite ISO-UTC-Texte im XLSX, da Excel-Zahlen keine Zeitzone tragen.
  DuckDB schreibt echtes Parquet mit den geordneten fachlichen Typen.

ClickHouse-Kandidaten werden nur unter `di_data.v_<version>_<execution>`
erzeugt und synchron geladen. Typen, Zeilen und Datenhash werden aus der
realen Tabelle geprüft. Im privaten Bucket `ch.so.daten` bleiben Original
und strukturierter Bericht unter `ingestion/`; die drei Ausgaben werden
an die serverreservierten `downloads/<distribution>/data.<format>` gebunden.
Jedes Objekt wird nach dem unveränderlichen Schreibversuch vollständig
zurückgelesen und geprüft. Anwendungsseitig unveränderliche Namen und
`rclone --immutable` sind keine S3-WORM-Garantie. Es gibt keinen öffentlichen
Objektpfad ausser über die aktuelle Gateway-Autorisierung.

Die kurze PG-Transaktion bestätigt den Fachstand nach frischer Berechtigung.
Admin projiziert danach das **aktuelle PostgreSQL-Soll** unter
`di_public_sql.ds_<dataset>_i_<issue>_current`. Bis zur verifizierten
Projektion bleibt `COMMITTED`; wiederholte Abschlüsse geben dieselbe Version
zurück. Das gepinnte ClickHouse verlangt für sein atomar ersetztes View
zusätzliche Rechte in den engen `ds_`- und `_tmp_replace_`-Präfixen.
Loader und Projector haben getrennte technische Konten. Foundation-/Superset-
Konten erhalten keine Kandidaten- oder persönliche SQL-Fachberechtigung.
Archivierung entfernt nur die abgeleitete Sicht und belässt die Historie.
