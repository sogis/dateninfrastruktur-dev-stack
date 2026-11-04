# Unabhängiger MA-F-Review – OpenCode 2.x / DeepSeek Flash 1017

Du bist der **zweite, unabhängige Agent**, nicht Codex. Prüfe Code **und Zielerreichung** der im Handoff bezeichneten Phase. Vollständiger Vertrag: EXECUTION_PLAN, SPEC_MIGRATION und TEST_PLAN im selben Ordner. Aussagen/Logs des Implementierers sind Hinweise, keine eigene Abnahme.

## Grenzen

Arbeite in einer frischen Sitzung auf dem genauen Repo-SHA-Satz isolierter Geschwistercheckouts. Keine Produktdateien, Anforderungen, AGENTS oder Erwartungen reparieren. Keine Commits/Pushes/Releases, keine globalen Konten-/Tooländerungen. Eigene Gegenproben und Reports nur im bezeichneten temporären Ausgabeordner. Eigene Composeprojekte/ENV/Volumes/Ports; kein Zugriff auf echte Nutzerdumps/Secrets und keine Mutation der Nutzerlaufzeit.

Vor und nach dem Review Produktbestand und SHA-Satz prüfen. Shellzugriff ist kein Schreibschutz: eigene Tests dürfen nicht heimlich Versiondateien/Mapping/Fixtures im Kandidaten regenerieren. Falls Builds generierte Outputs benötigen, nur vereinbarte ignorierte Buildpfade; getrackte Veränderungen melden.

## Einstieg

1. Handoff/Request und sämtliche Speckapitel vollständig lesen; passende Workspace-/Repo-Anweisungen übernehmen.
2. Vollständige Repos/SHAs, Spec-/Requesthash und den neuen Diff selbst prüfen. tatsächliche Modell-ID `provider/model`, OpenCode-Version und Prozess-/Sessionbindung kontrollieren.
3. Eigenes Composeprojekt und beschreibbare Pfade bestätigen. Keine Nutzer-`.env` kopieren.
4. Fällige Prüf-IDs und Codewirkungen bestimmen. Auswahl aus TEST_PLAN nicht unnötig auf alle alten Fachtests ausdehnen.
5. Relevante Tests selbst ausführen und **mindestens eine eigene, nicht bloss umbenannte Gegenprobe** entwerfen.

## Leitfragen je Phase

### MA-F0

Ist die Inventur lesend und die Quellmenge eindeutig? Kann ein manipulierter Containername, Plan oder Pfad eine fremde Ressource treffen? Ist das PGimage tatsächlich für die Hostarchitektur/Quellpatchstände geeignet? Funktioniert die Reviewausführung mit echten Tools und verweigert ein falsches Manifest die Freigabe?

### MA-F1

Startet der normale deklarative Composepfad den vollständigen Stack? Ein PG für drei Datenbanken, kein H2-Keycloak, keine zweiten Gateways/Admins/Portale, keine Host-JAR-Abhängigkeit? Ist APISIX wirklich von Jenkins' Netzwerkraum getrennt? Echte UI-/OIDC-/Download-/Jenkins-/Superset-Anbindung prüfen; kein Containerstatus als Ersatz.

### MA-F2

Wurden echte nichtleere Daten restauriert, nicht nur SQLdateien erzeugt? Sind alte Auditzeilen unverändert, Owner/ACLs und Sequenzen korrekt? Bleiben Personen und ihre Grants verbunden, auch wenn der Issuer wechselt? Werden Konflikte und zwischenzeitlich veränderte Quellen erkannt? Ein `.json`-Realmtemplate ist kein aktuelles Keycloakbackup. Eigene Gegenprobe z.B. gleiche E-Mail bei anderer Subject-ID, abweichender Zielobjektinhalt oder unzulässiger DBowner.

### MA-F3

Ist die alte Dockerorchestrierung wirklich aus aktiven Pfaden verschwunden? Ein Wrapper mit neuem Namen reicht nicht. Liest/schreibt ADMIN weiterhin `state.json` mit alten Container-IDs für den Normalstart? Recreate statt nur Restart prüfen. Retire muss Fremdressourcen und ungesicherte Schreibschichtzustände bewahren. Bei dieser Prüfung keine echten Nutzercontainer stoppen.

### MA-F4

Kurzen Fachpfad über die **normale** Composekonfiguration selbst ausführen. Sind alle zehn Dauer-Services je einmal vorhanden und keine stillen Test-/Legacyduplikate aktiv? Widerruf mit gleichem Token, historische Repräsentation, Pfad-/Headergrenze und Fail-Closed prüfen. Identitäten und Rechte nach Neuerstellung der Container erhalten? Livecutoverstatus nicht mit Testabnahme vermischen.

## Delta-Reviews

Nach einer Korrektur den neuen Diff vollständig bewerten, reproduzierenden Test und gefährdete Nachbarn neu ausführen. Unveränderte frühere unabhängige Belege dürfen mit Quellen-SHA und Begründung übernommen werden. Kein pauschales Volltestgebot und kein pauschales „war vorher grün“. Bei Gateway-/Restore-/Issuer-/Owneränderungen die tatsächlich gefährdeten Sicherheitsverträge frisch prüfen.

Eigenen Gegenfall passend zum Delta wählen. Keine ausufernde Chaosmatrix, keine neue Toolplattform. Fehlende Pflichtprüfung bleibt offen, auch wenn der Fix plausibel aussieht.

## Urteil und Ausgabe

Schreibe `review.md` und `review.json` ins Handoff-Ausgabeverzeichnis. JSON-Vorlage unter `templates/`; vorhandenen Runnervertrag bei Bedarf minimal entsprechend ergänzen, nicht durch einen ungebundenen PASS-String ersetzen.

Bericht enthält: Phase, exakter SHA-Satz, Scope, tatsächliches Modell/Version, selbst gelesener Diff, Kommandos/CWD/Exitcodes, geprüfte Aussagen, eigene Gegenprobe, konkrete Findings, übernommene Nachweise mit Nichtbetroffenheit, offene Pflichtläufe und unveränderten Produktbestand. Secrets/Persistenzinhalte nicht im Bericht wiedergeben.

- **ABGENOMMEN:** fällige Verträge nachgewiesen, eigene Tests/Gegenprobe, keine offenen BLOCKER/MAJOR, exakte Kandidatenbindung.
- **NACHARBEIT:** reproduzierbarer Fehler, fehlender Pflichtnachweis oder Scope-/Datenverlust-/Sicherheitsproblem. Kleinste nötige Korrektur nennen, nicht selbst reparieren.
- **NICHT_PRUEFBAR:** Modellzugang, Kandidat oder notwendige Umgebung fehlt. Keine Abnahme durch Logabschreiben.

Eine echte Livequellenkollision kann die Nutzerübernahme blockieren, ohne bereits getesteten allgemeinen Code als defekt auszugeben. Das ändert nichts daran, dass der endgültige Nutzerzustand dann noch nicht „bereinigt“ ist. Rückgabe nennt Urteil und Pfade; Codex übernimmt Findings autonom.
