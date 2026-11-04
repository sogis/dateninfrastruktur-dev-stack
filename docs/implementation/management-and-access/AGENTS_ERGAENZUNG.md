# Workspace- und Repo-AGENTS für Management/Access

Die bisherige `AGENTS.md` im gemeinsamen Elternordner stammt aus der Grundinstallation und enthält widersprechende globale Vorgaben (nur fünf Repos, kein SSO/Freigabeprozess, G01–G24 und alte Berichtspfade). **Nicht nur den neuen Auftrag darunter anhängen:** Die alten Umfangsausschlüsse müssen als historische Regeln eingeordnet werden.

Eine bereinigte, für den aktuellen Auftrag passende vollständige **Vorlage** liegt in [AGENTS.workspace.md](AGENTS.workspace.md). Der Nutzer übernimmt ihren Inhalt **einmalig in `<mutterordner>/AGENTS.md`** (vorherige Datei sichern/bei eigenen Anpassungen zusammenführen); die ZIP-Datei überschreibt die Workspace-Root-AGENTS **nicht automatisch**. Danach Codex mit dem gemeinsamen Elternordner starten. Codex kontrolliert in MA-0, ob die aktive Datei passt, und nimmt nur notwendige Anpassungen an betroffenen Repo-AGENTS vor.

Der gemeinsame Elternordner ist kein Git-Repository. `dateninfrastruktur-admin` ist das sechste Geschwisterrepo. **Codex implementiert; OpenCode 2.x/DeepSeek Flash 1017 reviewt unabhängig nach jeder Phase, durch Codex gestartet.** Für die genaue Aufgabe gelten der Gesamtplan und die SPEC-Dateien, nicht die historischen G01–G24-Gates.

Repo-spezifische Hinweise und Aufgaben:

## 2. STACK

Verantwortet Integration, eigene Laufzeitdaten und Reviewrunner. Vorhandenen Runner wiederverwenden. Nur benötigte Services prüfen. `docs/implementation/management-and-access/` ist neuer aktiver Dokumentationsordner, frühere Anforderungen/Berichte nicht rückwirkend ersetzen.

Eigene Ports, Volumes **und schreibbare Hostpfade**. Keine Volume-/Secretresets, keine öffentlichen Originpfade für verwaltete Dateien. Readiness des DB-Katalogs darf nicht von Jenkins/XTF abhängen. Eigentümer-/Migrationscredentials nicht in Apps kopieren.

## 3. PUBLIC

Ergänzen: DB-basierter Katalog aus freigegebenen Views, read-only. Bestehende Controller/VM/JTE gezielt weiterverwenden. Keine Schreiblogik für Grants, kein File-Streaming, keine Berechtigungsentscheidungen aus Snapshot/Lucene. Im DB-Modus kein stiller Fallback auf XTF; alte Rohartefakte nur ausliefern, wenn sie tatsächlich sicher und aktuell implementiert sind.

## 4. Neues ADMIN/AGENTS.md

Codex legt diese Datei bei MA-0 an und passt Pfade an. Inhalt mindestens:

- zentralen Gesamtauftrag und lokale Teilverträge vor Arbeit lesen;
- Boot-GA, Cayenne5-M3, Java25; keine JPA/Hibernate-Einführung;
- Modelle in `models/`, Fachschema via ili2pg, Zusatz-DDL/Audit als versionierte Migrationen;
- eigenes Management-DBschema, keine Writer-/Authzrollen vermischen;
- Audit-Actor/Command/DML in derselben expliziten Cayenne-Transaktion;
- neue Kontexte, keine gecachten Autorisierungsentscheidungen;
- Appdienste prüfen Authority, nicht nur die UI;
- read permissions nur am logischen Dataset;
- OIDC/JWTvalidierung, CSRF, interne API-Grenze, keine Token-/Bindinglogs;
- Authorization API entscheidet nur, liefert keine Datei;
- Reviewer ändern keinen Produktcode; testfähiger isolierter Kontext und genau bezeichnete SHAs.

## 5. Versionierung und Änderungssicherheit

Neue AGENTS-Inhalte sind Teil des Kandidaten und mitzuprüfen. Workspace-AGENTS ausserhalb der Repos **muss** mit tatsächlichem Inhalt/Hash im Handoff referenziert und im isolierten Reviewbereich bereitgestellt werden. Nicht zwei widersprüchliche aktive Arbeitsaufträge lassen. Keine globalen OpenCode-Regeln/Accounts überschreiben.
