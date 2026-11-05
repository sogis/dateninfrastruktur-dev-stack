# Reviewrequest MA-F4

- STACK base: `cd9b551743585860f3998a40805e3b15ada1af8a`
- ADMIN base: `02eaa8a450c7e9d88bad6a01132f67bc98a37489`
- PUBLIC base: `b1f20075be43eb4d0edf771ee1440ea0e30e1801`
- JENKINS base: `08931fa8254d096e2addcd3aee97bc1b753f087d`
- PLUGIN base: `579f3fd54432a977122afb186469fbb40d95322f`
- TOPICS base: `6b0b635f066dc8de5000e3e549b983fb772dfb33`

Umfang F17–F20, Details `F4_IMPLEMENTATION.md`. Fachschema, Auditmechanik,
Identitätsmigration, Gatewayroute und produktive Betriebs-/Restorepfade bleiben
unverändert. Diff vollständig selbst lesen; keine Produktdateien reparieren.

Selbst frisch aus STACK ausführen:
`./scripts/test-consolidation.sh --phase MA-F4`

Der Lauf verwendet nur eigene temporäre Ressourcen, dieselbe kanonische
Compose-Datei und einen neu benannten Prüfdatensatz. Er deaktiviert im eigenen
Fixture den Passwortgrant-Testclient und benutzt den normalen PKCE-Codeflow.
Nachweise siehe Implementierungsdokument; Pflicht ist insbesondere derselbe noch
gültige JWT vor/nach Widerruf sowie echter down/up mit zehn neuen Container-IDs.
Nutzerinstanz, Nutzersecrets, Originaldumps und private lokale Pläne nicht lesen.

Zusätzlich mindestens eine eigene passende Gegenprobe entwerfen und ausführen,
z.B. ein weiterer kanonischer Pfad-/Headerangriff mit vorherigem positiverlaubtem
Objekt oder abweichende Rollen-/Lifecyclebindung vor Mutation. Nur zielgerichtete
Prüfungen; unveränderte Modelle/ili2pg/komplette MA-A–E-Suites nicht neu starten.
Keinen eigenen Runtimeprozess als Dauerlösung hinterlassen. Produktintegrität vor
und nach dem Review kontrollieren.

Die F3-Abnahme liegt unter review/MA-F3-accepted.md. Der Implementierer hat danach
den eindeutig inventarisierten lokalen Bestand tatsächlich übernommen: ein neuer
PG16.10-Cluster mit drei restaurierten DBs, voller alter Auditinhalt, belegte
Identitätsübernahme und S3-Inhalts-/Metadatenvergleich; zehn gesunde Zielservices,
20 Originalquellen gestoppt und vollständig archiviert, alle Originalvolumes
behalten. Retire und LOCAL_CUTOVER_VERIFIED benötigen weiterhin den vollständigen
konkreten Fachpfad am realen Ziel. Eine isolierte F4-Abnahme bescheinigt nicht
allein die erfolgte reale Endprüfung.

Für die eigene Gegenprobe kann ein eigener kurzer Pythonwrapper `run(c,fresh=True)`
aus `test_consolidation_f4` ausführen und vor `cleanup(c)` eine weitere Probe am
noch laufenden eigenen Ziel ergänzen; `finally` muss nur den exakt eigenen Kontext
beseitigen. Das spart einen zweiten kompletten Teststack. Alle F17–F20 müssen dabei
weiter frisch ausgeführt und als solche protokolliert sein.
