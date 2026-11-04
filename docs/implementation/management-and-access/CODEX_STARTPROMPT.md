# Codex: vollständiger Implementierungsauftrag Management und Access

> Diesen Text als ausdrücklichen Auftrag an Codex übergeben oder sein vollständiges Lesen anfordern. Arbeitsverzeichnis ist der gemeinsame Elternordner der `dateninfrastruktur-*`-Repos. Spezifikationsordner: `dateninfrastruktur-dev-stack/docs/implementation/management-and-access/`.

Du bist **Codex, verantwortlicher Implementierungsagent**. Implementiere die vereinbarte Management-/Access-Etappe tatsächlich. Liefere lauffähigen Code, Modelle, Migrationen und echte Tests. Ein weiterer Plan alleine erfüllt den Auftrag nicht.

## 1. Vor Änderungen vollständig lesen

1. Workspace-`AGENTS.md` im gemeinsamen Elternordner (soll gemäss `AGENTS.workspace.md` aktualisiert sein) sowie `AGENTS.md` aller betroffenen Repos. Bei noch aktiven Grundinstallationsverboten diese vor Produktänderungen ausdrücklich einordnen; nicht mit einem scheinbar widerspruchsfreien Zustand fortfahren.
2. `EXECUTION_PLAN.md` im genannten Ordner.
3. `SPEC_MODELS.md`, `SPEC_PERSISTENCE_AUDIT.md`, `SPEC_APPLICATIONS_GATEWAY.md`.
4. `TEST_PLAN.md`, `OPENCODE_REVIEW_PROMPT.md`, `AGENTS_ERGAENZUNG.md`.
5. Aktuelle relevante Betriebs-/Architekturdokumentation und Gitstatus in STACK/PUBLIC/ADMIN; frühere Ladephase nur soweit sie berührt wird.

**Projekt-Root für Codex ist der gemeinsame Elternordner**, nicht das Dev-Stack-Repo. Der Elternordner erhält kein `.git`. `AGENTS.workspace.md` im Dokumentationsordner ist eine verteilbare Vorlage; wirksam ist die `AGENTS.md` im tatsächlichen Workspace-Root. OpenCode wird ausschliesslich durch Codex als Reviewagent gestartet.

Vorhandene Dateien/Remotes/Nutzerarbeit erhalten. Ältere AGENTS-Sätze „noch keine Authentifizierung/Datenbank“ gelten als historische Umfangsgrenze des damaligen Auftrags, nicht als Verbot des jetzt ausdrücklich beauftragten Ausbaus. Hinweise gezielt ergänzen, alte Nachweise nicht umschreiben. Keine alten `datenportal-*`-Repos bearbeiten.

## 2. Festgelegtes Ziel

- Neue INTERLIS-Catalog-/Access-Modelle, Dataset als einziger fachlicher Rechteanker, open/restricted.
- Unverändertes ili2pg erzeugt das Fachschema; PostgreSQL ist führend; Cayenne **5.0-M3** für Adminpersistenz.
- Spring Boot **4.1.2** als bei Spezifikationserstellung aktuelle GA; vor Ausführung offiziell auf eine wirklich neuere GA prüfen und genau pinnen, keine RC/SNAPSHOT.
- Neue Admin-App, bestehendes Sodata liest nur öffentliche SQL-Sichten.
- Nachvollziehbare fachliche Entscheide plus generisches transaktionales DB-Audit mit echtem Actor.
- OIDC/Keycloak, danach **APISIX forward-auth → Java Authorization API → PostgreSQL**.
- Interner Datei-Origin liefert aus privatem S3. Keine Dateiübertragung durch Sodata/Admin, kein Lua-Plugin, keine Casbin-Policydateien.
- Keine persönliche ClickHouse-/Superset-Rechteprojektion, keine Neuerfindung der laufenden Datenladephase.

## 3. Vorgehen: MA-0, MA-A, MA-B, MA-C, MA-D, MA-E

Arbeite streng in dieser Reihenfolge. Jede Phase:

1. Kleinsten zusammenhängenden Umsetzungsumfang und betroffene Verträge bestimmen.
2. Implementieren, relevante Tests tatsächlich ausführen. Bei Defekt zuerst reproduzierende Probe.
3. Kurzen Phasenrequest mit Ausgangs-SHAs, Scope, Tests, Ergebnissen und Nichtbetroffenheiten schreiben.
4. Code, Tests und Request lokal committen; fremde Änderungen nicht einbeziehen. Kein Remote-Push/Release.
5. **Nach** Commit vollständige Revisionsliste, Spec-/Requesthash und isolierte Testpfade im Handoff erzeugen. Kein Commit enthält seinen eigenen SHA.
6. Den zweiten Agenten autonom starten und seinen Lauf begleiten.
7. `NACHARBEIT`: kleinsten begründeten Fix plus Regression, neuer Commit, erneutes unabhängiges **Delta-Review**.
8. Erst `ABGENOMMEN` für exakt diesen Kandidaten erlaubt die nächste Phase. Keine parallele Vorwegnahme der nächsten Produktphase.

MA-E enthält den abschliessenden E2E-/Gesamtintegrationsreview. Nicht dieselbe Suite anschliessend aus Formalismus nochmals unter anderem Namen ausführen.

## 4. Unabhängiger Review ist deine Aufgabe zu orchestrieren

Verwende **OpenCode 2.x, DeepSeek Flash 1017 über den vorhandenen DeepSeek-API-Zugang**. Das frühere Qwen-/Infomaniak-Verfahren gilt für diesen Auftrag nicht.

In MA-0:

- reale OpenCode-Version, CLI-/lokalen Servicezugang und `run --help` prüfen;
- vorhandene Provider-/Modellkennung nachweisbar zum gewünschten DeepSeek-Stand auflösen; keine Kennung erfinden und keinen stillen Aliaswechsel;
- bestehende Authentifizierung weiterverwenden, keine APIkeys exportieren/anzeigen und keine neuen Pflicht-ENV-Secrets verlangen, wenn Account funktioniert;
- vorhandenen Runner `scripts/step2/review-phase.sh`/gleichwertig wiederverwenden bzw. schmal erweitern; nur falls keiner existiert einen kleinen Runner erstellen;
- frische Reviewkontexte, isolierte Geschwistercheckouts und eigene Runtimekonfiguration sicherstellen;
- eigene testfähige projektlokale Agentenkonfiguration entsprechend der **installierten** 2.x-Version, keine ungeprüften V1-Permissions und keine globalen Account-/Permissionänderungen;
- echten Reviewer-Datei-/Shell-/Testzugriff und negative Gateprobe ausführen. Nicht erst nach MA-E feststellen, dass autonome Reviews nicht möglich sind.

Reviewer darf lesen, bauen, testen und eigene Gegenproben ausserhalb des Produktbaums schreiben. Er repariert keine Produktdateien. Shellfreigaben sind keine echte OS-Sandbox: isolierte Ressourcen und Vorher-/Nachhervergleich bleiben Pflicht. Test-/Setup-Skripte müssen auf die angegebenen eigenen Ressourcen begrenzt sein.

Der normale Ablauf enthält **keinen manuellen Modellwechsel oder Reviewstart durch den Nutzer**. Tatsächlicher nicht auflösbarer Modell-/Tool-/Zugangsblocker: konkrete Diagnose, `AWAITING_INDEPENDENT_REVIEW`/`NICHT_PRUEFBAR`, kein Weitergehen und kein umbenanntes Selbstreview. Unabhängige Arbeiten innerhalb derselben Phase können fortgesetzt werden.

## 5. Risikobasierte Nacharbeit statt kompletter Testwiederholung

Vor jedem neuen Review eine kurze Delta-Testauswahl: Änderung → mögliche Auswirkungen → neu laufende Tests → übertragbare frühere Belege. Nutze TEST_PLAN.

Beispiele: Summen-/Modellfeldfix verlangt betroffene Modell-/Mappingtests, nicht automatisch Keycloak/Superset. Authz-/Token-/Pfadfix verlangt relevante echte Sicherheitsintegration, nicht nur Unit-Tests. Ein Framework-/Transaktionswechsel ist breiter und darf nicht wie eine Dokumentationskorrektur behandelt werden.

Der Reviewer darf seine frühere erfolgreiche Prüfung unveränderter Bereiche referenzieren, wenn Vertrag, Test, Produktcode und relevante Abhängigkeiten unverändert/anwendbar sind. Reproducer, betroffene Verträge und eine relevante eigene Gegenprobe laufen neu. „Alles grün laut altem Bericht“ genügt nicht.

## 6. Kritische Fallen

- Actor mit Cayenne-DML in **derselben physischen Connection und äusseren Transaktion**. `@Transactional` alleine beweist das nicht.
- `session_user` ist technischer DBuser, nicht Browserperson; volle Identität im Audit.
- Tabellen/PK-Sequenzen aus realem ili2pg-Mapping, keine geratene Schemaabbildung.
- Alle Relationship-/Hilfstabellen auditieren, nicht nur die Rootklasse.
- Kein Rechtscache, kein langlebiger ObjectContext, kein Grant aus alten JWTrollen.
- Request→Decision→Grant→Audit atomar; keine teilweise erfolgreiche Genehmigung.
- Sodata read-only, Selbstbedienung schreibt über Adminbackend.
- Browsercookie am Gateway bleibt CSRF-relevant, auch wenn intern Bearer weitergereicht wird.
- Öffentliche Downloads müssen anonym funktionieren; restricted benötigt gültige Identität/Recht.
- Datei-ID und tatsächlich gelesener Originpfad müssen exakt zusammenpassen.
- Alte öffentliche URL ist ein Bypass; keine wirksame Einschränkung behaupten, solange sie existiert.
- Alle verfügbaren historischen Distributionen erben dasselbe Datasetrecht; keine versteckten Sonder-ACLs.
- Kein eigenes Lua-Authz-Plugin und keine neue Policy-Synchronisation bauen.
- Bestehende private `.env` und uncommittete Nutzerarbeit niemals ins Review oder Git kopieren.

## 7. Artefakte und Abschluss

Eine `WORK_QUEUE.md` reicht. Phasenrequests nach `review/MA-X-request.md`; konkrete Handoffs/Rohbelege nach ignoriertem `.runtime/management-review/MA-X/<run-id>/`. Bereinigte Reviewberichte können nach Abschluss mit separatem Nachweiscommit versioniert werden. Das Urteil bleibt an den geprüften Produktcommit gebunden.

Am Ende: tatsächlich funktionierende URLs/Startkommandos, Quellstände, übernommene und neu ausgeführte Belege, offene Grenzen. Keine Rechtszertifizierung, Native-Kompatibilität oder ClickHouse-/Superset-Synchronisation behaupten, die nicht geprüft/implementiert ist.

**Beginne jetzt mit Lesen und MA-0. Setze danach den Gesamtauftrag ohne gewöhnliche Zwischenrückfragen bis MA-E um, immer mit dem verbindlichen unabhängigen Phasengate.**
