# Lokaler Endcutover MA-G

Status: **Ausstehend bis zur unabhängigen MA-G5-Abnahme.**
Der isolierte Review benutzt künstliche Daten und private Testcredentials.
Sein Ergebnis ist keine Aussage über einen bereits umgestellten Nutzerstack.

Der [lokale Storagecutover](LOCAL_STORAGE_CUTOVER.md) ist bereits erfolgt:
genau ein privater Bucket, 16 referenzierte Dateien mit 13 756 unveränderten
Bytes und Metadaten. Dieser einmalige Purge wird nicht wiederholt. Der
aktuelle lokale Compose-Kontext ist an Projekt, Instanz und benannte
persistente Volumes gebunden. Er wird vor dem Endcutover erneut inventarisiert.

Für den Endcutover werden der bekannte Datenbank-Fingerprint und die
erhaltenen Tabellen, Identitäten, Zugriffsrechte und Auditzeilen vor und nach
der einmaligen Schemaübernahme verglichen. Die alte Installation bleibt
bis zum Vorliegen der überprüfbaren Ausgangsbindung in Betrieb. Anschliessend
werden die eindeutig markierten Jenkinsjobs mit ihren Historien archiviert,
die gezielten Keycloak-Clients und ClickHouse-Dienstrechte eingerichtet und
der abgenommene Stack mit den gebundenen Volumes gestartet. Nicht zugeordnete
Jobs, Konten und Volumes bleiben erhalten.

Die ausgeführten Schritte, Nachweise und gegebenenfalls konkrete Hindernisse
werden hier erst nach dem tatsächlichen lokalen Lauf eingetragen.
