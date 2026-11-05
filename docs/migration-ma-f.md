# MA-F: lokale Übernahme und Rückfall

Die Übernahme ist eine ausdrückliche Operatoraktion. Normalstart führt sie nie
implizit aus. Erst nach den unabhängigen F0/F1/F2- und F3-Codeabnahmen darf der
Implementierer die eindeutig identifizierte eigene lokale Instanz umstellen.
Reviewer verwenden ausschliesslich eigene synthetische Quellen.

```sh
python3 scripts/consolidation.py inventory --output .runtime/consolidation/current.json
python3 scripts/consolidation.py prepare --inventory .runtime/consolidation/current.json --output .runtime/consolidation/migration.json
python3 scripts/consolidation.py cutover --plan .runtime/consolidation/migration.json --apply
```

Vorher das kurze Wartungsfenster ankündigen. Cutover baut benötigte Images vor der
Schreibpause, prüft alle IDs/Labels/Mounts, stoppt nur ausgewählte Schreiber,
sichert vollständige Datenbanken und aktuelle gestoppte H2-Daten, restauriert in
neuem PGvolume, gleicht Identitäten auditiert ab und kopiert private S3-Objekte.
Anschliessend werden die restlichen Quellen gestoppt und deren zusammengeführte
Dateisysteme mit Docker export vollständig privat gesichert. Das vermeidet die
Abhängigkeit von später neu getaggten oder fehlenden Ursprungsimagemanifesten.

PostgreSQL-Dumps enthalten ganze DBs, Owners/ACLs/Sequenzen/Audit. Rollen werden
kontrolliert zusammengeführt, nie beide Globaldumps blind eingespielt. H2 wird aus
dem tatsächlichen aktuellen Dateisystem gesichert und offline exportiert. Das
Ziel verwendet die Foundation-Keycloak-DB; Personen nur bei belegten UUIDs,
Foundation-Credentials bei Überschneidungen. Historische Decisions/Audit bleiben
unverändert; die aktuelle Principalbindung erhält ein eigenes Migrationsevent.
Alte Tokens mit altem Issuer verlangen nach dem Wechsel einen neuen Login.

Ein aktueller Sourcecheckpoint wird vor Übernahme erneut geprüft. Geänderte
Quelle, Identitäts-/Objektkonflikt oder unbekanntes befülltes Ziel blockiert.
Ein bereits vorhandener fremder Zielruntimebereich wird nicht überschrieben.
S3-Copy schreibt nur fehlende identische Objekte, löscht nichts und überschreibt
keinen Konflikt. Origin ist read-only, Legacy-Schlüssel bleibt privat gesperrt.

## Aktivierung und Retire

Nach gesundem kanonischem Start werden Schema, Identitäten, sämtliche übernommenen
Objektbytes/Metadaten, Jenkinskonto und vorhandene verschlüsselte Supersetverbindung
geprüft. Der Zielkontext wird aktiv; der abschliessende Benutzerfachpfad und Retire
werden getrennt nachgewiesen. Ein Healthstatus allein ist kein vollständiger
`LOCAL_CUTOVER_VERIFIED`-Nachweis.

```sh
python3 scripts/consolidation.py retire --plan .runtime/consolidation/migration.json --apply
```

Retire verlangt genau die geplante vollständige Ressourcenliste und verifizierte
Dateisystem-/Konfigurationsarchive. Vor jeder Entfernung erneut ID/Label/Mount und
gestoppten Zustand prüfen; keine forcierte Entfernung laufender Dienste. Alte
Restartpolicies werden deaktiviert, dann nur exakte Container entfernt, niemals
mit `-v`. Alle benannten und anonymen Originalvolumes bleiben in einem privaten
Retentionmanifest. Foundation-Garage-/Jenkins-/ClickHouse-/Supersetvolumes werden
weiterbenutzt; alte PG-/MA-Garagevolumes bleiben als Rückfallbestand erhalten.

Private Archive, Quellinspect, Bindkonfigurationen, ursprüngliche feste und dynamisch
zugewiesene Hostports und der konkrete `recovery.compose.json` liegen unter
`<runtime>/migration/retirement`. Dateien 0600, Verzeichnisse 0700. Für einen
expliziten Recoverylauf werden nötige ursprüngliche Dateirechte nur in geschützter
Stagingablage hergestellt; Originalarchive bleiben unverändert. Repoverzeichnisse
werden erhalten, nicht blind kopiert oder gelöscht. Keine Nutzersecrets in Reports.

## Rückfallgrenze

```sh
python3 scripts/consolidation.py rollback --plan .runtime/consolidation/migration.json --apply
```

Vor neuen fachlichen Zielwrites wird der vollständige Managementzustand gegen die
bekannte Übernahmebaseline geprüft. Vor Retire startet der Rückfall dieselben
ursprünglichen Container in Namespace-Abhängigkeitsreihenfolge. Nach Retire prüft
er alle Archive/Volumes, importiert ihre Dateisysteme mit ursprünglicher Architektur
und rekonstruiert die gesicherte Konfiguration über den privaten Recovery-Compose-
Verbund. Dabei bleiben Secrets, Ports, aktuelle H2-Daten und Volumezuordnungen erhalten.
Der normale Zielstart wird während eines aktiven Rückfalls ausdrücklich blockiert.

Nach neuen fachlichen Writes ist ein schlichtes Zurückstarten der Quellen kein
verlustfreier Rückfall: `ROLLBACK_UNSAFE` erfolgt vor Stop/Neuerstellung. Zuerst
neuen Zielzustand sichern und ausdrücklich abgleichen. Kein automatischer Reset,
kein Discard und keine Komplettbereinigung. Endgültige Speicherbereinigung und
Produktions-/externe S3-Änderungen gehören nicht zu MA-F.
