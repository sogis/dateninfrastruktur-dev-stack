# Tatsächlicher lokaler G1-Storagecutover

Ausgeführt am 2026-11-05 im bereits aktiven, eigentumsgebundenen lokalen
Composeprojekt. Kein fremder Endpoint, kein Volume-Reset, kein Produktpush.
Unabhängig akzeptierte Code-/Migrationskandidaten vor dem ersten schreibenden
Schritt: G1-Läufe `20261105T160802Z` und `20261105T162915Z`.

- Vorher lesend: Container-/Volume-/Instanz-/Bucketidentitäten, alle PG-Referenzen,
  tatsächliche S3-GET-Hashes samt benötigten Content-Metadaten und alte Keybindungen.
- Vier ausdrücklich freigegebene alte Zielobjekte einmalig entfernt. 16 private
  Referenzen mit zusammen 13 756 Bytes vollständig und byte-/metadatengleich
  übernommen. Die bekannte Canary und der hashgebunden nachgewiesene 51-Byte-
  Foundation-Smoke sind die einzigen als entbehrlich behandelten Sourcefixtures.
- Explizites bekanntes MA-F→G1-Schema-/Metadatenupgrade, keine Fachdaten-Seeds.
  Projekt/Volumes, Objektkeys, Distribution-UUIDs und fachliche Rechte erhalten.
- Normale Dienste mit neuer privater Garage-/Reader-Origin-Konfiguration neu
  erstellt. Dieselben gültigen Tokens liefern vor/nach dem Wechsel 32 erfolgreiche
  Downloads, acht 401 und acht 403 auf den 16 registrierten Dateipfaden.
- Erst nach vollständiger Runtimeprüfung Sourcebucket, Smoke-Bucket und vier alte
  Anwendungsschlüssel entfernt. Tatsächlich genau `ch.so.daten` und die zwei
  dedizierten Reader-/Writeridentitäten. Alle alten Keys und Anonymous-GET liefern
  auf einem **existierenden** privaten Zielobjekt403.
- Vorher-/Nachherhashes aller 16 Fachtabellen (ausgenommen die zwei vereinbart
  entfernten Storagefelder), vollständiger historischer Auditzeilen, fünf
  Keycloak-Identitätstabellen und vorhandener Jenkinsjobdefinitionen identisch.
- Zehn gesunde Dienste, drei bestehende PostgreSQL-Datenbanken. Wiederholtes
  normales Setup erhält ENV/Reader-/Writerkonfiguration/Keyreferenzen bytegleich
  und verändert die Auditgeschichte nicht.

Rohbelege, gebundener Plan, dauerhaftes Journal (`RETIRED`), Objektmetadaten,
Tokenproben und Checkpointhashes bleiben ausschliesslich privat unter
`STACK/.runtime/dateninfrastruktur/ma-g1-cutover/`. Keine Secrets oder Original-
Dateiinhalte wurden in Git oder einen Reviewer-Handoff übernommen.

Die einmaligen aktiven Host-/Tool-Einstiege und der Docker-COPY sind danach
entfernt. Die unveränderte Engine und eng benannte synthetische Regressionfixtures
liegen nur unter `tests/ingestion/retired/`; sie werden nicht ins normale Image
gepackt. Der lesende Probentreiber bleibt als Testhilfe. Kein Normalstart führt
Purge, automatische Schemaänderungen oder fachliche Seeds aus. Der weitere
CSV-/Rechte-/Jobauftrag G2–G5 ist hiervon getrennt und noch nicht angenommen.
