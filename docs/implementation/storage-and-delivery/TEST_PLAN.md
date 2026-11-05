# TEST_PLAN – risikobasierte Nachweise für MA-G

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Die IDs bezeichnen **Verträge**, nicht zwingend 55 einzelne Prozesse oder komplette Stackbuilds. Tests sinnvoll gruppieren und Fixtures innerhalb eines isolierten Laufs wiederverwenden. Nach Fixes nicht alles pauschal neu ausführen.

## 1. Testebenen und Beweisstandard

- Unit/Contract: Zustand, Typmapping, URI-/Identifier-/Payloadvalidierung, Rechteentscheidung und Retirementregeln.
- Echte PGintegration: ili2pg/Cayenne/Audit, Constraints, Transaktions- und Widerrufsrennen. Kein H2-Ersatz.
- JenkinsRule: RootAction, `@RequirePOST`, Credentialscope, Queue/Authenticator, Jobdefinition, direkter Buildbypass.
- Reale Composeintegration: gleiche `compose.yaml`, Images und Konfiguration wie Normalbetrieb; eigenes Projekt/Ports/Volumes/Secrets, keine Nutzer-`.env`.
- Reale Browserprobe: Keycloak-Codeflow, Plugin-CSV-Upload, Admin-Lieferrechte und Leserechte. Kein Passwortgrant als alleiniger OIDC-Nachweis.
- Echte GRETL-/CH-/S3-Proben: kein Dummyvalidator, kein vorab manuell gesetzter SUCCESS-Beleg, tatsächliche Hashes/Rows/Formate.

Negativprobe hat positiven Kontrollfall auf **existierender** Ressource. Kein 404 auf nie angelegte Datei als Berechtigungsnachweis. Jeder Pflichtlauf protokolliert Command, CWD, erwarteten/beobachteten Exit und konkrete Aussage, nicht nur „Build grün“.

## 2. MA-G0 – Verträge und Ausgangsstand

| ID | Prüfung | Pflichtbeobachtung |
|---|---|---|
| G00 | Sechs Repos, Workspace-AGENTS, tatsächliche SHAs/Dirty-State | Aktiver Stand und Nutzerarbeit bekannt; alte S2-Spez nicht als Code ausgegeben. |
| G01 | Reviewrunner/Gate | Neue G-IDs/Specdateien/alle Repos gebunden; falscher SHA, fehlender Report oder falsches Modell öffnet Gate nicht. |
| G02 | Echter Jenkins-OIDC-Tokenadapter-Spike | Aktueller User → gültiger Access-Token → Admin-Prüfung; Subjectbindung und falsche Audience negativ. |
| G03 | Echter CsvValidator/Modell/Typ-Spike | Kleines gültiges CSV positiv, ungültiges wirklich negativ; Toolversion/Transitivmodelle dokumentiert. |
| G04 | Behalten/Entfernen- und Löschgrenzen | Ein Bucketziel, erlaubter lokaler Purge, private referenzierte Dateien geschützt; keine Testprobe auf Nutzerdaten. |

## 3. MA-G1 – Storage und Catalogbereinigung

| ID | Prüfung | Pflichtbeobachtung |
|---|---|---|
| G10 | Freshsetup | Genau ein anwendungseigener privater Datenbucket, keine Websitefreigabe, dedizierter Reader/Writer. |
| G11 | Rechtepositiv/-negativ | Reader GET erfolgreich, PUT/DELETE verweigert; Writer nötige Objektoperationen positiv, Bucket-/Ownerverwaltung negativ. |
| G12 | Bypassschutz | Anonyme direkte S3-/Website-/Altpfadanfrage auf existentes Objekt liefert keine Bytes. |
| G13 | Setup-/Restartidempotenz | Keine zusätzliche Keyanlage/Rotation/Rechteerweiterung; Defaultfallback tatsächlich entfernt. |
| G14 | Nichtleere private Übernahme | Byte-/Metadaten-/PGreferenzidentität erhalten, altes Publicobjekt entfernt, privater Altbucket nach Prüfung weg. |
| G15 | Unterbrechung bei Cutover | Wiederanlauf löscht bereits übernommene neue Objekte nicht; falscher Endpoint/Instanz/Bucket-ID blockiert vor Mutation. |
| G16 | Neues Distributionmodell | ili2c/ili2pg/Cayenne/FK/UNIQUE, alte Storagefelder vollständig entfernt, Hash/UUID erhalten. |
| G17 | Bestehender Downloadpfad | open anonym positiv; restricted grant/deny/revoke mit gleichem Token, HEAD/Range/ETag weiterhin korrekt. |
| G18 | Credentials-/Imagegrenzen | Kein Writer/Adminsecret in Origin/Portal/Gateway, kein Secret im Report; normales Image startet ohne Legacy ENV. |
| G19 | Storagealtlasten | Normalsetup/Operator/Compose benötigt keine zweite Bucket-/Fresh-Migration-Betriebsart; Sourceunknown nicht still gelöscht. |

## 4. MA-G2 – Modelle, Lieferrechte und Aufträge

| ID | Prüfung | Pflichtbeobachtung |
|---|---|---|
| G20 | INTERLIS-Constraints/Freshschema | Neue Capabilities, CSV-Konfiguration, Zuweisung/Entzug gültig; negative Scope-/Zeit-/Beziehungsfixtures abgelehnt. |
| G21 | Upgrade nichtleerer DB | Fach-IDs, bestehende Grants/Decisions und historische Auditzeilen identisch; Mapping-/Runtimefingerprint/XTF-Roundtrip passend. |
| G22 | Office-/Dataset-/Gruppenrechte | Aktuelle gültige Wege erlaubt, fremdes Dataset, inaktiver Principal, Ablauf/Entzug abgewiesen; keine Datensatzleserechte aus submit. |
| G23 | Delegation/Verwaltungsgrenze | `manage_submitters` darf nur submit_data im eigenen Scope vergeben; kein publish/manage_access/Selbsteskalationspfad. |
| G24 | Benutzer-/Serviceauthentifizierung | Falsche Signatur/Issuer/Audience/Tokenart/Servicecredential negativ; fremde Person per Header unmöglich. |
| G25 | Submission/Seal/Idempotenz | Gleicher Key/Inhalt gleiche Submission; anderer Inhalt 409; fremdes Seal, Hashwechsel, Issue-Mismatch abgewiesen. |
| G26 | Zustandsmaschine/Claims | Nur erlaubte Übergänge; ein Claim; doppelte Callbacks idempotent; stale Fence abgelehnt. |
| G27 | Widerrufskonkurrenz | Entzug/Membership/Principaldisable vor Finalprüfung blockiert; definierte Commitreihenfolge im parallelen Test belegt. |
| G28 | Audit/Connection | Echter Actor + Initiator + Submission, gemeinsam mit Fachmutation; Rollback nach Flush vollständig, Poolleck ausgeschlossen. |
| G29 | Status-/Report-/Publicviewgrenze | Lieferant sieht eigene sichere Berichte, keine fremden Logs/Dateien/Grants; Publicviews enthalten keine Ingestiondetails. |

## 5. MA-G3 – Plugin und eine technische Pipeline

| ID | Prüfung | Pflichtbeobachtung |
|---|---|---|
| G30 | Echter OIDC-Browserflow | Exakter Client/Callback, stabile Subjectbindung, kein lokaler Name-/E-Mailfallback; verlorenes Token verlangt Login. |
| G31 | Ein Job / keine Seedwelt | Ein eigener `di-csv-ingest`, keine Organisations-/Seedjobs aus normalem Provisioning, Kollision mit fremdem Job bleibt erhalten. |
| G32 | Direkte Jenkins-Bypässe | Lieferant kann weder Build-API/Replay/Configure noch fremde Runs/Workspace/Artefakte nutzen; gefälschter Marker/Parameter abgelehnt. |
| G33 | Uploadgrenzen | Echte Datei, Größe im Stream begrenzt, Pfad-/Symlink-/Doppelpart-/NUL-/XSSfälle, CSRF-negativ, tatsächlicher Hash. |
| G34 | Plugin→Admin-Zugriffsprüfung | Liste und Submit frisch; manipulierte Dataset-/Issue-/Modeauswahl bleibt verboten, auch nach UIanzeige. |
| G35 | Queue-/Restartrecovery | Timeout/Controllerrestart nach Seal/Queueack, duplizierte Zustellung, genau eine claimende Execution. |
| G36 | Technische Ausführungsrechte | Eigener QueueItemAuthenticator/Fachserviceclient; Build nicht ungeprüft SYSTEM, Credentials nicht allgemein lesbar. |
| G37 | Run-/Log-/Tokenhygiene | Kein User-JWT/Refresh-/Storage-/CHsecret in Parametern/CPS/Log/Status, keine Rohdatenarchivierung. |
| G38 | Parallelitätsverdrahtung | Verschiedene Datasets können parallel, gleicher Dataset-Slot exklusiv; kein globaler Repolock. |
| G39 | Plugin/Config-Retirement | Teams-/ACL-/Formular-/Stepaltklassen und aktive Kontenpfade entfernt; normaler Neustart rekonstruiert nichts Altes. |

## 6. MA-G4 – reale CSVverarbeitung

| ID | Prüfung | Pflichtbeobachtung |
|---|---|---|
| G40 | CsvValidator vollständig ausgeführt | Pflichtfelder, Typen, Header, Schema/Hash, Null/UTF8/Quotes; ungültig oder fehlender Prüflauf niemals angenommen. |
| G41 | Replace-Historie | Zwei vollständige Stände, alte Dateien/CHdaten unverändert, current nur nach Fachcommit neu. |
| G42 | Append-Historie | Alt+Delta vollständig, Gesamtvalidierung, modellwidrige Kollision verworfen, Retry nicht doppelt angefügt. |
| G43 | Ausgabeformate | CSV/XLSX/Parquet echte Formate/Typen/Zeilen, führende Nullen/Decimal/UTC/MTEXT, Exceltext statt Formel. |
| G44 | Private CH-/S3-Kandidaten | Vor Commit weder Download noch normale SQL-/Supersetaccounts lesen Kandidaten; technische Positivprobe vorhanden. |
| G45 | Daten-/Planhashbindung | Inputwechsel, falsche Distribution-/CH-ID, result aus fremder Execution oder falschem Modell abgelehnt. |
| G46 | Teilausfälle vor Commit | Validator/CH/S3/Adminausfall: alter gültiger Stand erhalten, keine Teilveröffentlichung und kein blindes Overwrite. |
| G47 | Verlorenes Commitack/SQLprojektion | Ein PGcommit, eine Version; COMMITTED korrekt erkannt; Projector repariert, alter Worker dreht current nicht zurück. |
| G48 | Fachlich berechtigte Autopublikation | submit genügt nur bei eingerichteter Autopublikation/published; ausgeschaltete/entworfene/archivierte Ressourcen abgelehnt. |
| G49 | Umfangs-/Scopeprüfung | Ein GRETL-Ablauf für zwei Schemata; keine freien Userjobs/SQL/URLs und keine neue persönliche ClickHouse-Rechteprojektion. |

## 7. MA-G5 – Abschluss im normalen Compose

| ID | Prüfung | Pflichtbeobachtung |
|---|---|---|
| G50 | Frischer installierbarer Gesamtstand | Build aus sechs Checkouts, explizites Setup, ein PG/ein Bucket/ein CSVjob, keine Host-JAR-Nebenwelt. |
| G51 | Fachlicher Ende-zu-Ende-Lauf | Admin vergibt submit, User OIDC→Plugin→CSV→GRETL→PG/CH/S3→Sodata; tatsächliche neue Daten statt vorbereiteter Testpublikation. |
| G52 | Zwei verschiedene Entzüge | Lieferrecht verhindert neue/noch nicht committete Lieferung; Leserechtentzug verhindert Download mit altem Token. Rechte nicht verwechselt. |
| G53 | Queue/Race/Parallelfälle | Fremde Parameter, zwei gleichzeitige Datasets, gleiche Datasetlieferungen, wiederholte Requests und alter Callback sicher. |
| G54 | Vollständiger Recreate | `down` ohne -v und neuer `up`: neue Container-IDs, gleiche Identitäten/Rechte/Dateien/Versionen/Audit; erneutes Login/Upload möglich. |
| G55 | Betriebsgrenzen | Origin/Authz/PG-Ausfall fail closed; keine internen Hostports/Tokenlecks, keine alte öffentliche Route. |
| G56 | No-legacy statisch+dynamisch | Retirementmatrix vollständig, keine Legacyflags/Aliase/Jobs/Buckets/Teams/Manifestabhängigkeit im Produktweg. |
| G57 | Erhalt bestehender Komponenten | Betroffene Jenkins-/CH-/Superset-/Sodata-Funktion gezielt; keine beliebigen Foundationdaten zurückgesetzt. |
| G58 | Cleanup / Isolation | Eigene Testcontainer/Keys/Objekte sauber entfernt, Nutzerprojekte unangetastet; normale Topologie weiterhin genau einmal. |
| G59 | Dokumentation / tatsächlicher Cutover | Neuer Bedienweg korrekt; Codeabnahme, ausgeführte lokale Umstellung und echte Blocker sauber getrennt. |

## 8. Risikobasierte Wiederholung nach Korrekturen

Jeder Korrekturrequest enthält nur eine kleine Tabelle `Änderung → gefährdete Verträge → jetzt ausführen → begründet übernehmen`. Pflicht ist der reproduzierende Test plus tatsächliche abhängige Sicherheits-/Datenverträge. Der Reviewer entscheidet unabhängig, ob die Auswahl ausreicht.

| Änderung | Frisch prüfen | Nicht automatisch wiederholen |
|---|---|---|
| Text/Label in Pluginformular | Template/escaping und betroffener UIpfad | PGmigration, vollständiger CHloader, S3cutover |
| CSV-Dateinamenprüfung | Parser/Traversal und Upload-zu-Key-Bindung | Gesamte Fachrechte-UI |
| Storage-Key/Policyänderung | Reader/Writer/Anonymous/Altkey + ein realer Download | Alle INTERLIS-Fachfixtures |
| Modellspalte/Enum/FK | compile/ili2pg/Cayenne/Upgrade/Audit und betroffene Services | Unveränderte PKCEbrowsermatrix |
| Authority-/Gruppen-/Principalprüfung | erlaubte/verbotene Wege, Queue-/Commitrevocation, Race | Formatexport ohne Relevanz |
| OIDC-/Tokenadapter | echter Login/Audience/Issuer/Subject sowie Direktbypässe | Snapshot-Typmatrix |
| Queue-/Lease-/Retrycode | Duplicate/Restart/Stalefence und ein Commitpfad | Alle Sodatafacetten |
| APPEND-/Typmapping | Replace/Append/Gesamtvalidator/Export/Hashes | Jenkins-Realmbootstrap |
| Fachcommit/Projector | Crashfenster, idempotente Version, aktuelle Rechte, alter Worker | Unveränderte Storage-Migration |
| Build-/Image-/Dependencyänderung | relevante echte Runtime-/Plugin-/Loaderproben | Unberührte vollständige Plattformtestmatrix |
| Reportformat ohne Codeänderung | Gateparser + Bindung/Integrität | Bereits belegte erfolgreiche Fachtests |

Bei der **ersten Abnahme** einer Phase werden alle fälligen Phasenverträge nachgewiesen. Bei Delta können unbetroffene erfolgreiche unabhängige Einzelbeobachtungen am gebundenen Quellen-SHA übernommen werden. Niemals ein altes Gesamtergebnis als Freigabe geänderter Sicherheitslogik verwenden. Übernommene Belege nennen Reporthash, Check-ID und konkrete Nichtbetroffenheit.

## 9. Eigene Gegenprobe des Reviewers

Pro Phase mindestens eine tatsächlich ausgeführte, zum Risiko passende zusätzliche Gegenprobe. Beispiele: gleiche E-Mail/anderes Subject; gültiger Slot mit fremder Execution; Entzug kurz vor Commit; abgebrochener Bucketcopy mit bereits kopierten Zielobjekten; fremder Jenkinsjob gleichen Namens; Array statt erwarteter DTOzeichenkette; neues Contentobjekt unter einem schon reservierten Key.

Keine künstliche Ausweitung auf eine riesige Chaosmatrix. Ein sinnvoller selbst gewählter Angriff auf die Annahmen ist wichtiger als hundert Wiederholungen derselben Positivprobe.

## 10. Ehrliche Ergebnismeldung

`EXECUTED` nur mit tatsächlich ausgeführtem Kommando und Beleg. `CARRIED` nur mit gebundenem früherem eigenem Nachweis. `NOT_EXECUTED`/offene Pflichtprobe verhindert `ABGENOMMEN`. Dockerhealth, kompilierte YAML oder HTTP200 allein beweisen keinen fachlichen Datenfluss.

Ein G3-Probeprozessor und eine Vorabfixture dürfen nicht als G4/G5-End-to-End-Ergebnis ausgegeben werden. Die finale CSV muss über den neuen realen Uploadweg kommen und die beobachteten Tabellen-/Dateiwerte neu erzeugen.
