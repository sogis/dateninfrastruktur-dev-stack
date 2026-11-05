# MA-F4: Endabnahme am gemeinsamen Compose-Verbund

`./scripts/test-consolidation.sh --phase MA-F4` baut eine ausdrücklich isolierte,
kurzlebige Testinstanz aus derselben Compose-Datei, denselben Images, Vorlagen
und Setupwerkzeugen wie der Normalbetrieb. Sie wird danach anhand ihres exakten
Kontexts beseitigt. Keine andere Architektur und keine Nutzersecrets.

`python3 scripts/test_consolidation_f4.py --env <private-runtime.env>` prüft einen
bereits übernommenen lokalen Zielverbund. Dieser Modus startet keine zweite
Instanz und führt kein Cleanup aus. Er erzeugt ausschliesslich einen neuen,
zufällig benannten `maf-f4-*`-Prüfdatensatz samt eigenem Amt und Dateien. Vorhandene
Datensätze, Grants, Decisions und Auditzeilen werden nicht ersetzt oder entzogen.
Der technische Lieferprincipal und belegte Benutzer werden wiederverwendet;
Zuständigkeiten werden nur für das neue Prüfamt ergänzt. Testdaten bleiben als
bezeichnete Nachweise erhalten. Kein Datenlöschkommando ist Teil der Prüfung.

F17: echte PKCE-Authorization-Code-Anmeldung mit dem normalen vertraulichen
Gatewayclient, kein Passwortgrant-Testclient. Im Browser Metadaten ändern und
öffentlich sehen, Anna stellt Antrag, Claudia genehmigt genau diesen Antrag,
Datei herunterladen, genau dessen Grant widerrufen. Dasselbe vorher erfolgreiche,
noch gültige Ziel-JWT muss sofort für alle aktuellen/historischen Dateien 403
liefern. Audit zeigt Speichern/Genehmigen/Widerrufen. Bens separat neu erteilte
Freigabe dieses Prüfdatensatzes bleibt als positiver Recreate-Sentinel bestehen.

F18: historische CSV/XLSX-Bytes und Hashes, HEAD/Range/ETag, unberechtigter Benutzer,
Pfadmehrdeutigkeit, gefälschte Header und interne API. Stop nur der eigenen
Authorization API muss 503 ergeben; nach Start wieder 200. Ein kurzlebiger
Compose-Tooljob beobachtet die Header hinter unverändertem OIDC/forward-auth.
Nur der Downloadupstream wird vorübergehend auf den Beobachter umgelegt. Die
exakten normalen Routebytes werden im finally-Block wiederhergestellt und der
Beobachter gestoppt. Keine Credentials oder Headerwerte in Messberichten.

F19: retained Jenkinslogin/Jobliste und eigens bezeichnete Datei; harmloser echter
Gradle-Tasks-Aufruf ohne Publikation. Vollständige Zeilen-/Schemaprüfsummen der
kleinen vorhandenen ClickHouse-Tabellen; existierende verschlüsselte Superset-
Verbindung tatsächlich benutzen. Vorher-/Nachher-Snapshot von Managementtabellen,
Audit, Sequenzen und Sicherheitskatalog, Benutzer-UUIDs und Secrethash vergleichen.
Öffentliches `down` ohne -v und `up --skip-build`: alle zehn Container müssen neue
IDs haben. Neues echtes Login, aktive und widerrufene Rechte sowie Dateien prüfen;
zusätzliche Metadatenänderung muss nach Recreate mit fortgesetzter Auditsequenz
funktionieren.

F20: genau zehn gesunde Defaultservices eines echten Composeprojekts. Keine
Host-JARs, internen Hostports oder zweite Gateway-/Admin-/PG-Instanz. Keine
laufenden Tool-/Beobachtercontainer am Ende. Das Tool bescheinigt nur den konkret
geprüften Kontext. Die echten Legacyquellen und der lokale Retirestatus werden
separat anhand des gebundenen Migrationsplans ausgewiesen.

Produktive Compose-, Gateway-, Restore-, Identitäts-, Schema- und Fachlogik sind
gegenüber dem akzeptierten F3-Stand unverändert. Die Änderungen sind Endabnahme,
optionale Namensgebung/Wiederverwendung im expliziten Testfixture und der
Testlauncher. Deshalb keine neue vollständige MA-A–E- oder F0–F3-Wiederholung.

Eigene gezielte Läufe: F17/F18 Browserpfad bestanden nach einer Korrektur der
neuen Test-Codeflowabfangung (Location am Login-POST statt Redirect erneut routen).
Danach F18 Ausfall/Headerbeobachter bestanden. Für den harmlosen GRETL-Test wurden
das bestehende Init-Skript und ein privates /tmp-Buildverzeichnis berücksichtigt;
anschliessend nur F19/F20 neu ausgeführt und bestanden, einschliesslich deaktiviertem
neuem Client-Sentinel und zusätzlicher auditierter Änderung nach Recreate.
Keine Produkt-/Gateway-/Fachvertragsänderung. Der Reviewer führt den endgültigen
vollen MA-F4-Lauf frisch aus. Eigene Rohbelege: `.runtime/maf-f4-browser-delta.log`,
`maf-f4-security-recreate.log` (F18-Teil), `maf-f4-recreate-final.log`.
