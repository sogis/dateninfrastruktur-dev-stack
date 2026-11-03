# Technischer Stand der Grundinstallation

Stand: 3. November 2026. Kandidat `c005` (Namespace-Cleanup und
Neuveröffentlichung). Dieser Bericht ist eine Selbstdokumentation des
Implementierungsagenten, **keine unabhängige Abnahme**.

## Laufender Zustand

Der Stack läuft lokal mit dem Compose-Projekt
`dateninfrastruktur-dev-stack` und dem Runtime-Verzeichnis
`.runtime/dateninfrastruktur-dev-stack`. Der aktuelle publizierte Stand ist:

- `releaseId`: `5eda4b72-2c77-4491-b41e-e26261dbbd37`
- `datasheets`: `datasheets-5eda4b72-2c77-4491-b41e-e26261dbbd37.xtf`
- `duckdb`: `catalog-5eda4b72-2c77-4491-b41e-e26261dbbd37.duckdb`
- `catalog`: `null` (zulässiger leerer Fachkatalog)

Erreichbar über:

| Ziel | URL |
|---|---|
| Portal | http://localhost:18081/ |
| Jenkins/Anlieferung | http://localhost:18081/anlieferung |
| Öffentlicher Bucket | http://localhost:18081/ch.so.daten/ |
| Keycloak | http://localhost:18080 |
| Superset | http://localhost:18088 |
| ClickHouse HTTP/JDBC | http://localhost:18123 |

PostgreSQL hat keinen Hostport. Alle veröffentlichten Ports sind an
`127.0.0.1` gebunden.

## Belegte Komponenten

- fünf eigenständige Zielrepos aus den beauftragten Quellcommits,
- durchgängig aktive Namen im `dateninfrastruktur`-Namespace
  (`DATENINFRASTRUKTUR_*`, `dateninfrastruktur.*`,
  `dateninfrastruktur-sodata`),
- lokale Jenkins-, Sodata- und Superset-Images aus diesen Quellen,
- Jenkins 2.555.2 mit Java 21, Java-17-GRETL-Laufzeit und 77 übernommenen
  Standardplugins,
- aktives Plugin `jenkins-gretl-dateninfrastruktur-plugin` mit identischem HPI/JPI-
  SHA256,
- veröffentlichte Jenkins-Images `0.1.7` (Digest
  `sha256:20049cc968c686b411d52928496386761c8a9ea23ec585c7b45905a46c368b47`)
  und Sodata-Images `0.1.3` (nativ
  `sha256:9f0f4ecfd2e41003f67cca839f0878d5a26c0072c4c390ca977ac5d7de6cebae`,
  JVM `sha256:b313dc305e81273e11bed8ca1e76150cf24390e8b5cd508366a1d8701806664d`),
  jeweils für `linux/amd64` und `linux/arm64`,
- Seedjob und sieben generierte Organisationsjobs,
- gültige lokale Erstpublikation mit echter DuckDB,
- PostgreSQL 16.10 mit getrennten Rollen für Keycloak und Superset,
- Keycloak 26.8.1 mit Realm und drei stabilen Demoidentitäten,
- ClickHouse 26.8.36.3 mit drei Testzeilen und eingeschränkten Lesern,
- Superset 6.1.0 mit gespeicherter ClickHouse-Verbindung und echtem
  Treibertest,
- privater Bucket mit synthetischem Testobjekt und drei verweigerten
  öffentlichen Zugriffswegen.

Versionen, Digests und Prüfkommandos stehen in
`docs/implementation/grundinstallation/reports/evidence/`.

## Abnahmekriterien – Stand der Implementierungsprüfung

| ID | Stand | Kurzbeleg |
|---|---|---|
| G01 | LOKAL_GEPRUEFT | fünf Ziele und Quellcommits dokumentiert; Quellarbeitsbäume unverändert |
| G02 | LOKAL_GEPRUEFT | kein `jenkins-home`, keine Quellsecrets, Lizenzen plus `LICENSE.upstream` |
| G03 | LOKAL_GEPRUEFT | aktive Builds/Mounts/Images und Konfiguration im neuen Namespace; nur dokumentierte Kompatibilitätsnamen und historische Bilder bleiben |
| G04 | LOKAL_GEPRUEFT | Jenkins- und Sodata-Images aus Zielquellen gebaut; Plugin als `jenkins-gretl-dateninfrastruktur-plugin`; IDs/Architektur belegt |
| G05 | LOKAL_GEPRUEFT | 77 Plugins, Plugin aktiv, HPI/JPI-Hash gleich, JCasC ohne unbekannte Symbole |
| G06 | LOKAL_GEPRUEFT | lokaler Modus ohne AD, Seed SUCCESS, Jobs und Formularressourcen vorhanden |
| G07 | LOKAL_GEPRUEFT | GRETL-/Modellbundle, Erstpublikation, DuckDB, Sodata-Readiness |
| G08 | LOKAL_GEPRUEFT | Editor/Docs entfernt, Explore aus, Admin-Sperren wirksam |
| G09 | LOKAL_GEPRUEFT | nur lokale S3-/Manifest-/Reload-Ziele; Git-Writeback aus |
| G10 | LOKAL_GEPRUEFT | Tags, Digests, Plattform, Treiber, Snapshot-Einschränkung dokumentiert |
| G11 | LOKAL_GEPRUEFT | getrennte PostgreSQL-Rollen; Fremdzugriffe verweigert |
| G12 | LOKAL_GEPRUEFT | Realm, drei IDs, Discovery, JWKS, Issuer dokumentiert |
| G13 | LOKAL_GEPRUEFT | Leser erlaubt; restriktive Tabelle, INSERT, DDL, GRANT, anonym verweigert |
| G14 | LOKAL_GEPRUEFT | JDBC 0.9.0 über Hostport tatsächlich ausgeführt; DBeaver-Anleitung |
| G15 | LOKAL_GEPRUEFT | Superset-Metadaten, Treiberabfrage, Login |
| G16 | LOKAL_GEPRUEFT | privates Objekt berechtigt lesbar; anonym, Public-Key, Gateway verweigert |
| G17 | LOKAL_GEPRUEFT | Loopback-Ports, PostgreSQL intern, eigene Volumes/Hostpfade |
| G18 | LOKAL_GEPRUEFT | Frischstart aus neuen eigenen Volumes; Wrapper-JAR und neues Plugin-Artefakt enthalten |
| G19 | LOKAL_GEPRUEFT | Wiederanlauf erhält Secrets, IDs, Verbindung, Testzeile; keine Seedduplikate |
| G20 | LOKAL_GEPRUEFT | paralleler Reviewstack auf eigenen Ports/Volumes; Arbeitsinstanz unverändert |
| G21 | LOKAL_GEPRUEFT | `--registry-only`, fehlende Plugin-/Sodataquelle mit Exitcode und Meldung |
| G22 | LOKAL_GEPRUEFT | Root-README mit Start/Stop/URLs/JDBC/Grenzen/Diagnose/Bereinigung |
| G23 | LOKAL_GEPRUEFT | Ablage, Anweisungs-Hashes und Kandidatenmanifest c005 nach Abschnitt 0/8.1 |
| G24 | NOT RUN | vom Nutzer für den Namespace-Cleanup ausdrücklich nicht angefordert |

## Grenzen

- Keycloak ist nicht als OIDC-Login in Portal, Jenkins oder Superset
  integriert. Ein Keycloak-Benutzer erzeugt keine Anwendungsrechte.
- Sodata hat keine neue Portal-Datenbank und keinen Freigabeprozess.
- Explore ist deaktiviert; es gibt keine fachliche ClickHouse-Pipeline,
  Historisierung oder Dashboards.
- Superset läuft mit einem lokalen Administrator und ohne Redis/Celery.
- Die GRETL-Abhängigkeiten sind `5.0.0-SNAPSHOT`; das aufgelöste Manifest und
  die JAR-Hashes liegen als Beleg vor, ein bitidentischer Neubau ist ohne
  Lock-Initiative nicht garantiert.
- Die mit c004 eingeführte Plugin-Umbenennung auf
  `jenkins-gretl-dateninfrastruktur-plugin` bleibt bestehen; die alte
  Maven-Snapshot-Koordinate `jenkins-gretl-datenportal-plugin` bleibt entfernt.
- Der Kandidat c005 stellt die aktiven Umgebungsvariablen, Konfigurations-
  schlüssel und den Sodata-Artefaktnamen auf `dateninfrastruktur` um. Die
  Jenkins-Images `0.1.7` und die Sodata-Images `0.1.3` enthalten diese Stände;
  ältere Images bleiben ausschliesslich als historische Artefakte bestehen.
- Java-Pakete, JCasC-Symbol, Pipeline-Schritt, Seedjob, Pipeline-Lock,
  Scannerdateien, Containerpfade und fachliche INTERLIS-Namen bleiben bewusst
  unverändert. Die verbleibenden Vorkommen sind in `docs/legacy-names.md`
  begründet.
- Eine unabhängige Agentenvalidierung von c005 war auf ausdrücklichen
  Nutzerwunsch nicht Teil dieses Auftrags. G24 bleibt daher `NOT RUN`; der
  Status lautet **lokal geprüft, keine unabhängige Abnahme angefordert**.
