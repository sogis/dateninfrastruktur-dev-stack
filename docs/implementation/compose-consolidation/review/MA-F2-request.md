# Reviewrequest MA-F2

- STACK base: `09bf4ddd7b73fa383d888fead3aaf11e6294ce56`
- ADMIN base: `3f6f0f0d526de81e84a9d496582cd9265ed180ce`
- PUBLIC base: `b1f20075be43eb4d0edf771ee1440ea0e30e1801`
- JENKINS base: `08931fa8254d096e2addcd3aee97bc1b753f087d`
- PLUGIN base: `579f3fd54432a977122afb186469fbb40d95322f`
- TOPICS base: `303b2f0be785dc5b06882612f9b8bfcd8c17b040`

Umfang: vollständige kontrollierte Migration/Rückfallprobe F09–F13.
F2_IMPLEMENTATION.md beschreibt Daten-/Identitäts-/Storage-/Secretverträge.
Die Umsetzung verwendet explizite kanonische Compose-Toolservices. Keine neue
Dauerarchitektur. Öffentliche Lifecyclewrapper und tatsächlicher Cutover gehören
weiter zu F3; deren bisherige Pfade sind noch keine abgeschlossene Umstellung.

Selbst ausführen aus STACK:
`./scripts/test-consolidation.sh --phase MA-F2`
und `python3 scripts/test_migration_safety.py`.
Für den gezielten Rollen-/Gruppenpfad ausserdem
`python3 scripts/test_migration_identity_permissions.py` ausführen.
Die Hauptprobe erstellt eigene nichtleere Quellen und einen normalen Zielstack,
verwendet niemals Nutzerdumps/Secrets und bereinigt ausschliesslich nachgewiesene
eigene Testcontainer/-volumes. Sie verwendet die bereits akzeptierte F1-Version
per git archive als alte Toolbasis (Lockdatei); kein Rücksetzen von Produktdateien.
Altes Quell-PG16.9/PostGIS3.5.2 wird explizit nur als kurzlebige Quellfixture
verwendet, Ziel ist das native PG16.10/PostGIS3.5.2-Image aus F0.

F09: drei nichtleere volle Dumps, alle Tabellen-/Auditinhalte, Owners/ACLs,
Sequenzen, PostGIS/topology/tiger/fuzzystrmatch und Rollen-/DBparameter.
F10: aktueller tatsächlicher H2-Export statt Importvorlage, Foundationpasswörter,
MA-only-User/-Client mit UUID, eindeutige aktuelle Principalumstellung, getrennte
Migrationsauditzeilen, unveränderte historische Entscheidungen; Konflikte und
gefälschter Writerkontext verweigert.
F11: acht unterschiedliche historische Objektbytes und Metadaten, Replay ohne
neue Kopien, Byte-/Metadatenkonflikt und Quelländerung abgewiesen; Origin RO und
Foundationkey privat verweigert mit jeweils funktionierendem Positivzugriff.
F12: realer Fehler nach Backup vor Aktivierung und Rückfall auf dieselben Quellen;
geänderte Quelle invalidiert Backup, Coordinatorreplay ohne Dubletten, neue
Cayenne-Schreiboperation mit fortgesetzter Sequenz; anschliessend Rückfall vor
irgendeinem Stop als ROLLBACK_UNSAFE verweigert. Runtimejobs dürfen PG nicht bauen.
F13: bestehende verschlüsselte Supersetverbindung zu ClickHouse nutzbar, Schlüssel
und Passwörter erhalten, private Archivdateien; keine Originalsecrets im Handoff.

Eigene sinnvolle Gegenprobe ausserhalb der Produktbäume zusätzlich ausführen,
z.B. gebundene Zielkonfiguration nach Planung ändern und Ablehnung vor jeglichem
Docker-Mutationsaufruf prüfen, oder andere belegte Identitäts-/ACLverletzung.
Keine F0/F1-/MA-A–E-Vollsuiten erneut starten; Produkt und Anforderungen nicht
reparieren. Alle sechs HEADs/Hashes, Workspace-AGENTS und eigenes Modell prüfen.
Nur lokale Kandidaten; LOCAL_CUTOVER_PENDING bleibt bis späterer Umstellung.
