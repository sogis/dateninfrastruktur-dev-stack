# SPEC_CLEANUP_CUTOVER – Entfernung ist Teil der Funktion

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Kein Dauerbetrieb mit altem und neuem Modus. Kein „retired“-Wrapper, der beim Aufruf bloss eine Meldung ausgibt, wenn der Code/Vertrag nun tatsächlich ersatzlos entfallen kann.

## 1. Behalten, ersetzen, löschen

Die folgende Liste wird in G0 gegen die tatsächlichen Repositories vervollständigt. `RETIREMENT_MATRIX.md` nennt pro Element: tatsächlicher Pfad, Aufrufer, Ersatz oder ersatzloser Wegfall, neue Regression, Phase und Nachweis. Keine Datei aufgrund eines blossen Namens löschen.

| Bereich | Konkrete Bereinigung |
|---|---|
| STACK `compose.yaml` | Nur ein Datenbucket, neue Writer-/Readerkonfiguration; obsolete Default-/Managed-/Public-Credentials entfernen; keine Legacy manifest/reload ENV an Jenkins. |
| `setup-compose.py`, `compose_runtime.py` | Fresh/Migration-Berechtigungszweige und Fallbacks entfernen. Ein einziger aktiver Setupvertrag. |
| Alte Garage-Browser-/Websitekonfiguration | Aus aktiven Images/Services/Tools entfernen; kein öffentlicher Origin. |
| `di-managed-private` | Referenzierte Daten übernehmen, Bucket und zugehörige allein dafür existierende Keys/Aliase entfernen. |
| Veraltete Foundation-Smoke-Buckets | Nur nach eindeutigem Nachweis reiner eigener Testfixtures entfernen; fremde Inhalte nicht pauschal löschen. |
| ADMIN `Distribution.storageProfile`, `legacyAccessUrl` | ILI, SQL, Cayenne, DTOs, Tests und Serialisierung bereinigen; keine ignorierten alten JSONparameter. |
| ADMIN `legacy`-Importer/-Operator | Aus aktivem Command-/Web-/Imagepfad entfernen, sobald einmalige Herkunftsübernahme abgeschlossen. Kein ewiger `legacy-import`-Subcommand. |
| ADMIN separate `managed_runtime.py`, `identity_runtime.py` usw. | Verbliebene Legacy-/Meldungslauncher löschen, keine neuen Containerpfade. Normale Schema-/Audittools mit explizitem DBziel erhalten. |
| PUBLIC `CatalogSnapshot`/Manifest-XTF/DuckDB-Loader | Tatsächlich obsolete Laufzeitpfade, Parser, Reload-/Artefaktcontroller, zugehörige Configschalter und unbenutzte Dependencies entfernen. DB-Readmodel/VMs/Seiten erhalten. |
| PUBLIC `CatalogArtifactController` etc. | Kein Gesamt-XTF/DB-Dump als aktueller Publickatalog ausliefern. Historische Quellen nicht als neue API publizieren. |
| PLUGIN `GretlDatenportalRootAction`, Generator/Seed/Scanner | Durch neue schlanke Anlieferung ersetzen; keine Delegationsklassen unter altem Package. |
| PLUGIN `TeamDirectory*`, `PermissionConfiguration*`, `GretlDatenportalAuthorizationSynchronizer` | Löschen, sofern nur alter Fachautorisierung dienend. Keine zweite Rechteprojektion. |
| PLUGIN `Dataset*Parser`, `DefaultGuiDefinitionFactory`, Gui/Yaml-Mergecode | Alte Metadaten-/Formularerkennung entfernen; neue UI/validierter CSVvertrag statt übernommener Altkomplexität. |
| PLUGIN `prepareDatenportalWorkspace` und alte Step-Aliase | Entfernen; neuer Run benutzt ein festes versioniertes Runnerbundle mit eigener Workspacekopie. |
| JCasC | Lokale alte Lieferantenkonten, Seedteams, Organisations-ACLs und alte Lockdefinition entfernen; ein OIDC-Realm, neue Credentialreferenzen, ein CSV-Job. |
| TOPICS `gretl-datenportal-teams.yaml`, Organisations-`permissions` | Entfernen. Technische CSVdefinitionsdateien dürfen weiterhin deklarativ sein, aber nicht als Teamdatenbank. |
| TOPICS `shared/Jenkinsfile` | Durch einen festen CSVjob ersetzen; keine alten METADATA_FILE-/PUBLICATION_MODE-/RELOAD_PORTAL-Pfade. |
| TOPICS `datenportal-publication.gradle`, `publication.properties`, alter Katalog-SQL-/XSL-Export | Alte Livepublikation vollständig entfernen. Tatsächlich wiederverwendbare Validator-/Formatkonverter sauber in den neuen Runner ziehen. |
| Alte Datasheet-/PublishedCatalog-Dateien | Einmalige Herkunftsfixtures ggf. eng archivieren; keine Discovery-/Startup-/Publishabhängigkeit. Fachliche CSV-Datenmodelle ausdrücklich behalten. |
| Root-/`scripts/management`-Doppelwrapper | Ein kanonischer Betriebsweg; reine Kompatibilitätsaliases entfernen. Reviewwerkzeuge dürfen weiter unter ihrem vorhandenen Pfad leben. |
| `migration_*`, `consolidation.py`, Recovery-Compose-Generator | Nach abgeschlossener MA-F-/MA-G-Umstellung nicht mehr als normaler Operator-/Startpfad ausliefern. Benötigte generische File-/Composehelfer zuerst entkoppeln, alte Betriebsvarianten entfernen. |
| Tests | Entfallene Verträge ersetzen, nicht verdeckt deaktivieren. Tests der neuen Rechte-/Fachlogik behalten. Historical reviews nie nachträglich „reparieren“. |
| Build-/Imagekontext | Keine COPY-Anweisung auf entfernte Altpfade; alte HPI-/CSV-/Keydateien nicht via Dockercontext wieder einpacken. |

Ein bestehender Projekt-/Artefaktname mit `dateninfrastruktur` ist keine Altlast. Ein lizenzpflichtiger Herkunftsverweis auf `datenportal` ebenfalls nicht. Die Abnahme bewertet aktive Zuständigkeiten und erreichbaren Code, nicht ausschliesslich ein blindes Wort-Grep.

## 2. Sodata-Umstellung ohne Featurezerstörung

Vor dem Entfernen der Loader eine Featurematrix erstellen: Suche/Facetten/Pagination, Datasetdetail, Serien/Ausgaben, aktuelle und historische Downloads, kontakt-/strukturbezogene Anzeige. Diese Funktionen müssen im DB-Modus erhalten bleiben. Kein komplett neues Portal und kein Entfernen der Suchfunktion als vermeintliche Bereinigung.

Nicht benötigte Explore-/WebR-/DuckDB-Laufzeitteile, die aus dem früheren Datenportal stammen und bereits durch die separate Datenwerkstatt abgelöst werden sollen, nur dann aus diesem Auftrag entfernen, wenn sie im aktuellen Portal tatsächlich deaktiviert/obsolet sind und keine neue fachliche Funktion verloren geht. Keine Datenwerkstattintegration beginnen. Unklare aktive Benutzerfunktion in G0 dokumentieren und gegen Scope entscheiden, nicht zufällig löschen.

`DATENINFRASTRUKTUR_CATALOG_SOURCE_TYPE=manifest|fixture|database` wird keine öffentliche Mehrfachbetriebsart mehr. Die Produktanwendung benutzt DB. Testfixtures werden über Testinfrastruktur bereitgestellt, nicht über einen Produktionsfallback. `current.json`-Ausfall kann den Start nicht mehr beeinflussen.

## 3. Jenkins-Runtimebereinigung

Inventarisieren: eigener Seedjob, generierte Organisationsjobs, Markerproperties, Pipelines, globale/projectMatrix-ACLs, Credentials, lokale Testaccounts, Lockresources und Pluginconfig. Nur eindeutig eigene Altobjekte entfernen. Der HPI-Upgrade darf nicht einen scheinbar neuen Seedjob neben den alten Jobs erzeugen.

Nach G3-Codeabnahme und bevor die Nutzerinstanz neue Anlieferungen akzeptiert:

1. Eigene alte Lieferjobs sperren und laufende Builds geordnet beenden; keine fremden Jobs abbrechen.
2. Fachlich benötigte frühere Status-/Auditdaten liegen in PG/Git; keine automatische Migration alter Buildlogs in das neue Fachmodell erfinden.
3. Alte eigene Jobs/config/ACLs/Secrets gezielt entfernen. Normales Jenkins-Home und fremde Jobs bleiben erhalten.
4. OIDC-Realm/Client und den einen markierten CSVjob installieren, Rechte an echter Anmeldung testen. Notfallzugang des Operators gesichert halten.
5. Direkte Build-/Replay-/Log-/Artefaktwege mit einem normalen Lieferantenkonto negativ testen.
6. Neustart und Recreate dürfen keine alten Seeder-/Organisationsjobs oder Konten erneut provisionieren.

Ein generischer technischer Jenkinsimage-Build aus PLUGIN/JENKINS muss von frischem Checkout funktionieren. Alte Artefakt-/Installationsskripte, die HPI-Dateien kopieren, an den einzigen neuen Vertrag anpassen, nicht beide IDs auf Dauer installieren.

## 4. Lokaler Cutover ist nicht das Review

Reviewer arbeiten immer in isolierten Checkouts und eigenen kurzlebigen Compose-Projekten mit künstlichen Credentials. Sie löschen **keine** Objekte im tatsächlichen Nutzerbucket. Codeabnahme und reale Nutzerumstellung werden getrennt ausgewiesen.

Codex darf nach jeweiliger unabhängiger Abnahme den eindeutig identifizierten lokalen Entwicklungsbestand gemäss den konkreten Lösch-/Übernahmegrenzen umstellen. Vorher ankündigen, welche eigenen Dienste kurz unterbrochen werden. Keine weitere Rückfrage für bereits ausdrücklich freigegebene alte `ch.so.daten`-Objekte; bei fremder Instanz, unklaren privaten Objekten oder widersprüchlicher Identitätsbindung dagegen nicht raten. Übrige unabhängige Arbeit fertigstellen und einen engen echten Blocker nennen.

Die bestehende MGMT-DB wird migriert, nicht neu mit synthetischen Daten ersetzt. Bereits vorhandene Grants, Decisions, Versionsreferenzen und Audithistorie müssen erhalten bleiben. Tokens dürfen nach einem echten OIDC-Clientwechsel neue Anmeldung verlangen; Personenbezüge dürfen nicht durch Anzeigenamenheuristik wechseln.

## 5. Keine Kompatibilität versus einmaliger Upgrade

Zulässig: ein explizit auf den bekannten Ausgangsstand beschränktes Upgrade mit Version-/Fingerprintprüfung, das vorhandene Fachobjekte erhält. Nicht zulässig: bei jedem Start alte und neue Spalten/Keys/Jobnamen ausprobieren, still migrieren, `legacy=true` akzeptieren oder Fehler durch altes Publikationsverhalten kaschieren.

Einmalige MA-G-Umstellungswerkzeuge werden bis zum erfolgreichen Cutover isoliert gebaut/getestet. Danach aus Defaultimages, aktiven Compose-Toolprofilen und allgemeinen CLI-Subcommands entfernen. Benötigte Quellen/Belege bleiben über den eingefrorenen Phasencommit und Reviewhistorie zugänglich; kein offener Recoveryserver. Historische SQLmigrationen, die die aktuelle Datenbank versionskontrolliert erklären, sind nicht pauschal „Kompatibilitätscode“ und dürfen als inaktive Historie bleiben.

Eine **bereits installierte aktuelle** Version muss weiterhin klar auf eine notwendige explizite Migration hinweisen, statt bei unbekanntem Schema zu starten. „Keine Kompatibilität“ bedeutet fail closed bei unbekanntem alten Stand, nicht unvalidiertes Starten.

## 6. Statische und dynamische Altlastenprüfung

`RetirementVerifier.verify()` erhält einen kleinen expliziten Katalog, z.B. `contracts/retirement-rules.json` als Entwicklungs-/Abnahmevertrag. Es prüft:

- aktive Compose-/ENV-/JCasC-/Image-/CLI-Einstiege;
- Java-/Groovy-/Python-Imports und Builddependencies;
- Plugin-Routen/Steps, generierte Jobs und tatsächlich installierte Konfiguration;
- produktive Tests/Fixtures versus ausdrücklich historische Doku;
- aktives S3-Key-/Bucketinventar und laufende Container;
- unerwartete neue Kompatibilitätswörter/Schalter, ergänzt durch eine manuelle Diffprüfung.

Nur präzise freigegebene Historicalpfade ausnehmen. Nicht ganz `docs/**`, `tests/**` oder `scripts/**` pauschal ausschliessen. Neue aktuelle READMEs dürfen keine Befehle auf entfernte APIs empfehlen. Beispiele, Sources und diese Spez dürfen alte Namen als Entfernungsvorgabe nennen; das ist kein aktiver Produktpfad.

Dynamisch: altes Form/Step/Buildziel ist nicht erreichbar bzw. liefert kontrolliert 404/403/Fehler **ohne** Kompatibilitätsverarbeitung; alter Bucket nicht mehr vorhanden; neues Normalsetup kennt nur neuen Vertrag. Negativtest allein auf einen nie existierenden alten Pfad genügt nicht: zuvor tatsächlich benutzten Weg aus Inventur/Fixture heranziehen.

## 7. Abschliessende Dokumentation

`docs/operations.md`: ein frischer Setupweg, ein Normalstart, ein Rechtebootstrap, ein CSV-Vertrags-Onboarding, ein Uploadweg, Status/Retry/Fehlerdiagnose. Keine vier alten Startanleitungen nebeneinander. `README.md` verweist dorthin.

`LOCAL_CUTOVER.md` der neuen Etappe dokumentiert belegte alte/neue Instanz-/Daten-/Objektzahlen, unveränderte Auditbasis, umgestellte Benutzer-/Datasetbezüge, durchgeführten Endpfad und keine aktiven Altjobs/-buckets/-container. Secrets/CSVinhalte bleiben privat. Kein voller Backupbetrieb, keine CI und kein HA-Projekt als Nebenarbeit.
