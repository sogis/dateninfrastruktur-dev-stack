# SPEC_JENKINS_PLUGIN – schlanke Anlieferung, ein Job, keine Teams-YAML

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Schwerpunkt MA-G3. Referenzquellen R3/R4/R5 und S2–S5 in [SOURCES.md](SOURCES.md). Die bestehende Plugin-ID kann bleiben, damit das neue HPI technisch installiert wird; **das ist keine fachliche API-Kompatibilität**. Alte URL-, Step-, YAML- und Organisationsjobverträge entfallen.

## 1. Ziel und Paketstruktur

Neues Hauptpackage beispielsweise `ch.so.agi.jenkins.delivery`. Das Plugin ist eine Oberfläche und ein Dispatcher, kein Katalogparser, kein SQL-Authorizer und kein Dateidatenlager mit öffentlichem Browser.

```text
PLUGIN/src/main/java/ch/so/agi/jenkins/delivery/
  config/       geprüfte Backend-/Job-/Uploadkonfiguration
  identity/     aktuelle Jenkins-/OIDC-Identität und Service-Tokenclient
  client/       typisierte Admin-Ingestion-API
  web/          RootAction, Formulare, eigene Status-/Berichtsanzeige
  upload/       begrenzter persistenter Inputspool
  queue/        genau ein Job, Dispatch, Claim, technische Ausführungsidentität
  steps/        feste Pipelineintegration, keine Benutzerskripte
```

Keine neue Abstraktion für beliebige Jobtypen. Ein vorhandener geeigneter Helfer darf umziehen; keine alten Klassen nur als delegierende Hüllen erhalten.

## 2. Anmeldung und Benutzerbindung

Jenkins verwendet denselben vorhandenen Keycloak-Realm, aber einen eigenen vertraulichen OIDC-Client `jenkins-delivery`. Standardflow mit PKCE, exakte Callback-/Logout-URLs, kein Passwortgrant für Lieferanten, keine Wildcardredirects. Die genaue Jenkins-Callback-URL wird am gepinnten `oic-auth`-Plugin ermittelt, nicht geraten.

`userNameField=sub` oder eine nachweislich gleichwertige unveränderliche Identitätsabbildung. Keycloak muss für Admin- und Jenkins-Client dieselbe Personenkennung liefern; insbesondere Pairwise-Subject-Konfiguration prüfen. Bei verschiedenen Subjects kein E-Mail-/Username-Fallback, sondern belegte Identitätszuordnung oder Konfiguration korrigieren.

`JenkinsOidcActorResolver.current(request)`:

1. Aktuelle Jenkins-Authentication ermitteln; anonym, SYSTEM und technische Escape-Hatch-Authentifizierung sind keine Lieferperson.
2. OIDC-Realm und fest konfigurierten Issuer prüfen. Nur `User.current()` verwenden, nie `User.getById(request.user, ...)`.
3. Den für diesen User vorhandenen Access-Token über die **belegte** API der gepinnten OIDC-Version beziehen, z.B. `OicCredentials.getAccessToken()`. Diesen Adapter in G0 mit echten Tokens testen, keine frei erfundenen OIC-Klassen/Methoden verwenden.
4. Subject/Issuer der geprüften Tokenidentität müssen zur unveränderlichen Jenkins-User-ID passen. Der endgültige kryptografische Tokencheck erfolgt nochmals in Admin.
5. Fehlender/abgelaufener/nicht passender Token führt zu erneuter Anmeldung bzw. 401. Keine Verlängerung durch Abschalten von Expiry/Audienceprüfung und kein selbstgebauter Refresh-Token-Daemon.

Benutzer-Access-Token braucht die Ingestion-Audience. Das Jenkins-Login-**ID-Token** ist kein API-Access-Token. Token nur transient für synchrone Benutzeraufrufe verwenden, nicht in Submission, ParametersAction, Buildbeschreibungen, CPS-State, Console, AJAX-URLs oder Upload-Metadaten speichern. OIDC-Plugin-eigene verschlüsselte Tokenhaltung bleibt dessen Aufgabe.

Jenkins-API-Tokenauthentifizierung allein ersetzt keinen für die Ingestion gültigen Benutzer-Access-Token. Sofern der gewählte OIDC-Adapter solche Aufrufe überhaupt unterstützt, müssen Identität und aktueller API-Token genauso gebunden geprüft sein; kein Zugriff auf Tokens anderer Jenkinsuser. MVP-Abnahme erfolgt mit dem echten Browser-Codeflow.

Ein lokaler Notfalladministrator darf technisch Jenkins reparieren, erhält aber daraus keinen fachlichen Upload-Grant. Die alten festen Konten `seed-user`, `agi-user`, `read-user` usw. sind keine dauerhafte zweite Identitätswelt; nach eindeutiger Inventur ihre aktiven Login-/ACL-Verwendungen entfernen. Keine pauschale Löschung fremder Jenkinsaccounts.

## 3. Jenkinsberechtigungen und Ausführung

Normale OIDC-Benutzer bekommen nur die technischen Minimalrechte zum Laden der Anlieferungsoberfläche, typischerweise `Overall/Read`. Sie erhalten **kein** `Job/Build`, `Job/Configure`, `Run/Replay`, `Job/Workspace`, `Run/Delete` oder allgemeines Lesen der gemeinsamen technischen Jobhistorie. Projekt-/Globalrechte sind additiv; alte globale Grants müssen tatsächlich entfernt werden.

Der einzige Job heisst verbindlich `di-csv-ingest`. Eine kleine technische, nicht interaktiv anmeldbare Ausführungsidentität `di-csv-executor` wird durch einen geprüften `QueueItemAuthenticator` für genau diesen markierten Job gesetzt. Nicht generell alle Jenkinsjobs auf diese Identität oder SYSTEM umstellen.

Die Jenkinsrechte des Executors sind nur für den eigenen Job, benötigte Credentials und den vorhandenen Ausführungsknoten ausreichend. Die separate Admin-API-Serviceidentität erhält nur die Ingestion-Executor-Audience/-Rollen. **Jenkins-Ausführungsrechte, Betriebssystemrechte und S3-Bucketrechte sind drei verschiedene Grenzen.** Der CSVcode ist vertrauenswürdig und fest; ein Benutzer mit Job/Configure oder Script Console wäre eine andere Sicherheitsklasse. Im lokalen Single-Container-MVP keine behauptete OS-Mandantenisolierung.

Die zentrale Provisionierung darf kurz und eng mit Jenkins-Systemberechtigung arbeiten, um den einen Job anzulegen. Der gesamte Build darf deshalb nicht ungeprüft als SYSTEM laufen. Direkte `schedule2`-Benutzung erfordert eigenständige Fachprüfung; Jenkins-ACLs werden dadurch nicht magisch ausgewertet.

## 4. Oberfläche und HTTP-Endpunkte

Neue RootAction `data-delivery`, von `/anlieferung` erreichbar. APISIX leitet auf die neue Oberfläche unter dem vorhandenen Jenkinspräfix; **kein Redirectalias** vom alten `/gretl-datenportal`, kein paralleler alter Formularkatalog.

| Oberfläche/Aktion | Inhalt |
|---|---|
| Startseite | Eigene lieferberechtigte Datasets, Suche, Officeanzeige aus Admin-API; kein Themenrepo-Scan für Metadaten. |
| Datasetformular | Bestehende Ausgabe, erlaubter Modus, Hinweis auf Autopublikation, genau eine CSV, Kommentar. |
| Absenden | `POST`, Jenkins-Crumb, Origin/SameSite-Schutz, serverseitige Prüfung vor Queueeinreihung. |
| Eigene Lieferungen | Servergefilterte Liste mit Status, Zeit, Dataset, Inputgröße und sicheren Fehlermeldungen. |
| Detail/Report | Strukturierte Validation nach Zeile/Attribut/Fehlercode; keine rohen Werte fremder Bestände, keine Gesamtkonsole. |
| Retry/Cancel | Explizite `POST`-Aktion mit aktueller Revision; zentrale Rechte-/Statusprüfung. |

In UI/JavaScript keine Storagecredentials, CH-Passwörter oder Benutzer-JWTs. Templates müssen Text escapen; vom CSV-/Kommentarfeld kommende HTMLzeichen sind keine vertrauenswürdigen Fragmente.

Keine `METADATA_FILE`, `PUBLICATION_MODE`, `RELOAD_PORTAL`, freie `ORGANISATION`, frei wählbarer Gradletask, Model-URL, S3-Key oder SQLtext im neuen Formular. Dataset/Issue/Modes werden auch bei manuell manipuliertem POST zentral validiert. Die Organisation ist die aus dem Dataset ermittelte Metainformation, nicht ein separat vertrauenswürdiger Requestparameter.

## 5. Upload: begrenzt, persistent und privat

Das Plugin nimmt CSV entgegen; Admin und Sodata müssen dafür keine grossen Datei-Streams proxyen. Defaultlimit **100 MiB** pro Datei, administrativ konfigurierbar mit dokumentiertem oberen Hardlimit; Request-/Multipart-/Spoollimits konsistent. CSV-only bedeutet keine ZIP-/XLSX-/XML-Eingabe und keine serverseitige URLabholung.

`IncomingUploadStore` unter einem eigenen privaten Bereich im persistenten Jenkins-Home:

```text
$JENKINS_HOME/data-infrastructure/uploads/<submission-uuid>/input.csv
```

- Submissions zunächst anhand des Datasetpfads/Usertokens zentral anlegen; Autorisierung vor umfangreicher Dateiverarbeitung.
- Multipartstream direkt in eine zufällige private Tempdatei schreiben, Größe während des Lesens begrenzen, SHA256 berechnen. Kein `readAllBytes()` für die gesamte Datei.
- Dateiname ist nur Anzeige, Pfad immer serverbestimmt. Keine Symlinks, `..`, absolute Pfade, NUL oder doppelte Dateiparts akzeptieren.
- Nach fsync/atomarem Abschluss serverseitige Spoolzuordnung persistieren und Auftrag versiegeln. Ein nicht fertig geschriebener Upload wird nie READY.
- Absturz nach Dateischreiben/vor Seal ist ein UPLOADING-Auftrag mit privatem Rest, kein erfolgreicher Auftrag. Der Reconciler kann ihn gefahrlos als unvollständig kennzeichnen.
- Job materialisiert genau diese Datei per Jenkins `FilePath` in seinen eigenen Runworkspace und vergleicht Hash/Größe erneut.
- Keine generelle Artefaktarchivierung von CSV, XLSX, Parquet oder ganzen `build/outputs/**` in öffentlich/jobweit lesbaren Jenkinsarchiven.
- Terminale Spoolreste werden nur anhand ihrer eigenen Submissionzuordnung und definierter Frist bereinigt; ursprüngliche Dateien einer publizierten Lieferung sind zuvor privat in S3 archiviert. Kein generisches Workspace-/Home-Löschen.

MIME und Dateiendung sind Vorprüfungen, nicht die eigentliche CSV-/INTERLIS-Validierung. Formelartige Zeichenketten bleiben bei CSV semantisch Text; XLSX-Export darf daraus keine Formeln erzeugen.

## 6. Dispatcher und genau ein technischer Job

`CsvJobProvisioner.ensureJob()` erstellt/aktualisiert ausschliesslich `di-csv-ingest` mit eigener Markerproperty und festem Jenkinsfile. Bei Namenskollision mit einem fremden Job abbrechen, nicht übernehmen. Kein Cron-Seed zur Berechtigungssynchronisierung; neue Datasets sind nach DBänderung direkt im Formular sichtbar.

Normale Builds erhalten eine plugininterne `DeliveryQueueAction(submissionId, dispatchId)` und eine Benutzer-Ursprungsreferenz für Diagnose. Vertrauliche Werte stehen nicht in `ParametersAction`. Ein diagnostischer Submission-ID-Parameter darf nicht selbst die Ausführung legitimieren.

`DeliveryQueueDecisionHandler`/fester erster Pipelinestep verweigert Aufrufe ohne gültigen zentralen Dispatch und passende Marker. **Beides prüfen:** ein gefälschter interner Marker aus nicht autorisiertem API-/Replaypfad sowie ein echter Marker mit fremder/abgelaufener Submission darf keine Fachwirkung haben. Ein Jenkinsadministrator bleibt eine vertrauenswürdige Betriebsrolle, aber versehentliches `Build Now` erzeugt dennoch keine erfundene Lieferung.

Dispatchrecovery ist eine kleine begrenzte Hintergrundaufgabe im bestehenden Plugin, kein eigener Dienst: offene READY-Aufträge beim Backend reservieren, Queue anhand stabiler Action prüfen und fehlende Zustellungen wiederholen. Ein Netztimeout führt nicht zur Neuanlage eines anderen Auftrags. Defaultabstand z.B. fünf Sekunden; konkrete Einstellung dokumentieren, keine harte Millisekundengarantie.

`disableConcurrentBuilds()` und der bisherige globale Lock `datenportal-topic-repository` entfallen. Jeder Run besitzt eigene Dateien und einen festen Code-/Vertragsstand. Datasetweite Konkurrenz regelt der Backend-Slot; zwei verschiedene Datasets müssen mit den vorhandenen Executors parallel möglich sein.

## 7. Konkrete Klassen und Methoden

| Klasse | Methoden / Vertrag |
|---|---|
| `DeliveryPluginConfiguration` | `validate()`, `backendBaseUri()`, `serviceCredentialId()`, `uploadLimits()`; feste interne URI, keine Benutzerwerte; keine Tokens im `toString`. |
| `JenkinsOidcActorResolver` | `current(request) -> UserTokenContext`, `requireSubjectMatch(...)`; nur aktueller User, validiertes OIDC-Setup. |
| `ServiceTokenClient` | `acquire(scope)`, `invalidateOn401()`; vorhandene Jenkins Credentials, begrenzter Token-Lifetimecache nur für Authentifizierung, keine Permission-Caches. |
| `IngestionApiClient` | `listEligible`, `create`, `seal`, `getStatus`, `retry`, `cancel`, `reserve`, `claim`, `checkpoint`, `complete`; typisierte DTOs, bounded HTTP, kein blindes „2xx bedeutet fertig“. |
| `DeliveryRootAction` | `getIndex`, `getDataset`, `doSubmit`, `doRetry`, `doCancel`, `doStatus`, `doReport`; mutierende Staplerhandler mit `@RequirePOST`. |
| `DeliveryFormValidator` | `validateSelection(...)`, `validateUploadMetadata(...)`; Backend bleibt finale Autorität. |
| `IncomingUploadStore` | `createTemporary(id)`, `receiveBounded(stream,limit)`, `seal(id,evidence)`, `copyToRun(...)`, `removeOwnedTerminal(...)`; Dateisystemgrenzen und Hash. |
| `CsvJobProvisioner` | `ensureJob`, `verifyDefinition`, `retireOwnedLegacyJobs`; persistente Marker, keine globalen Name-prefix-Deletes. |
| `DeliveryDispatcher` | `dispatch(submissionId)`, `findQueuedDispatch`, `reconcilePending`; zentral reservieren, Queue-Ack, doppelte Zustellung harmlos. |
| `DeliveryQueueAction` | Nur IDs/Dispatchbezug; keine OIDC-/Storagecredentials. |
| `DeliveryRunBindingAction` | Execution/Fence und verschlüsselter Lease-Nachweis; nicht exportierte geheimnistragende Getter. |
| `DeliveryQueueAuthenticator` | `authenticate(task)` nur beim eigenen markierten Job; technische Minimalidentität, kein SYSTEM-Fallback. |
| `ClaimDeliveryStep` | Claim/Plan/FilePathmaterialisierung/erneuter Inputhash; sonst Buildabbruch ohne Load. |
| `RunCsvDeliveryStep` | Fester Wrapper zum generischen GRETL-Task, keine Benutzer-Shellzeichenkette; Workdir/Timeout/Exitcode. |
| `CompleteDeliveryStep` | Manifest lokal lesen/limits prüfen, ans Backend melden; COMMITTED/PUBLISHED korrekt unterscheiden. |
| `DeliveryRunListener` | Start/Ende/Abbruch/Controllerrestart mit Backendzustand abgleichen; kein statusloses „SUCCESS“ bei ungeklärtem Commit. |
| `DeliveryReportPresenter` | Nur bereinigte fachliche Statusdaten; HTMLescaping und Scope. |

Klassen dürfen bei echtem Zusammenhang zusammengefasst werden. Keine Funktionsverdopplung im Plugin und Admin: Fachrechte/Zustandsmaschine liegen in Admin; Plugin orchestriert nur den technischen Jenkinsablauf.

## 8. Feste Pipeline

Ein versioniertes Jenkinsfile aus dem Plugin oder TOPICS-Runnerbundle, nicht aus frei gewähltem Benutzerbranch. Verantwortlichkeiten:

```text
claimDelivery
  → materializeVerifiedInputAndPlan
  → runCsvDelivery (genau ein fester GRETL-Task)
  → submitResultEvidence
  → await/reconcile publication result
finally
  → report technical failure only if not already committed
  → wipe own temporary credential files / workspace-sensitive remnants
```

Kein Benutzer-Token in `withEnv`, keine dynamische Groovy-Auswertung, kein `sh "$USER_INPUT"`. Technische CH-/Storagecredentials über feste Credentials-IDs nur für diesen Job binden. Ein Plugin-Pipelinestep kann die Admin-Callbacks im Controller erledigen; der GRETL-Prozess braucht keinen PG-Writer und keinen allgemein privilegierten Admin-API-Token.

Ein ResultManifest ist auch nach Jenkins-SUCCESS noch kein fachlicher Commit, bis die Backendbestätigung vorliegt. Umgekehrt kann nach verlorenem Ack ein fachlicher Commit vorliegen, obwohl Jenkins einen technischen Fehler sieht. Abfrage und Reconciliation lösen dies auf.

## 9. Image, JCasC und installierte Altzustände

JENKINS baut das neue HPI aus genau dem Kandidatenrepo. Kein Wiederverwenden eines alten lokalen Images als impliziter Beweis. OIDC-Plugin und transitiver BOM-/Corebedarf fest pinnen; Build- und Laufzeitversionen aufzeichnen. JVM21 für Jenkins/Plugin und Java17 für GRETL dürfen nebeneinander bestehen; Admin bleibt Java25.

JCasC enthält genau einen OIDC-Realm, technische Basisrechte, Plugin-Backendadresse, Credentialreferenzen und den festen Job. Keine Teams, kein Seeder-Team, keine Organisationsjobliste. Bestehendes Jenkins-Home wird nicht gelöscht. Alte vom Plugin verwaltete Jobs/Properties/Configurations werden einmalig inventarisiert, nach sicherem Stop entfernt und nicht beim Neustart rekonstruiert. Unbekannte manuelle Jobs unangetastet lassen und als ausserhalb des Auftrags dokumentieren.

Pluginname/Anzeige und URL werden auf Dateninfrastruktur-Anlieferung bereinigt. Dieselbe HPI-ID darf als Upgradeziel bestehen, aber ohne alte Java-Step-Aliase und ohne deserialisierende Kompatibilitätshüllen. Alte Builds/Jobs, die diese Klassen benötigen, werden nur im klaren bekannten Legacyumfang retired; keine fremden Jobs mit `name.startsWith(...)` löschen. Historische Nachweise bleiben in Git, nicht als aktive Ausführungsoption.

## 10. Phasenabnahme

G3 prüft OIDC und API mit echten Keycloakidentitäten, JenkinsRule-Unit-/Securitytests und realem Browser. Ein test-only Probeprozessor darf die Jobverdrahtung belegen, markiert aber nichts als fachlich veröffentlicht und ist nicht im normalen Image/Defaultjob auswählbar. Bis G4 bleibt die reale CSV-Annahme im Nutzerbetrieb kontrolliert deaktiviert. Ab G4 ist ausschliesslich der echte GRETL-Weg aktiv.

Pflichtfälle: gleicher Anzeigename bei anderem Subject, abgelaufener/falscher Audience-Token, manipulierte Dataset/Issue-ID, direkte Build-API/Replay, normaler Nutzer liest fremde Joblogs oder Uploadpfade, duplizierter Dispatch, Controllerrestart nach Seal. Alle werden am passenden Gate tatsächlich geprüft.

## 11. Konkrete Konfigurations- und Startgrenzen

Neue JCasC-Symbolik z.B. `diDelivery`, Pipeline-Steps z.B. `diClaimDelivery`, `diRunCsv`, `diCompleteDelivery`. Nach Implementierung genau einen Satz Namen verwenden; alte `gretlDatenportalJobs`-/`prepareDatenportalWorkspace`-Aliase nicht mitführen. Die konkreten Namen in Root-README, Provisioner, Tests und Templates müssen übereinstimmen.

APISIX führt für `/jenkins/*` kein zweites eigenes Browser-OIDC vor Jenkins ein. Jenkins-OIDC und Portal-OIDC benutzen denselben IdP und getrennte Clients. Keycloak-SSO vermeidet eine zweite Passwortabfrage; Cookie-/Callback-/Tokenkontexte bleiben getrennt. Externer Issuer/Authorization-URL und containerintern erreichbarer Token-/JWKS-Endpunkt sind bewusst auseinanderzuhalten. `localhost` im Jenkinscontainer ist nicht Keycloak. In G0 unterstützte Discovery-/Backchannel-/Manual-Konfiguration des gepinnten Plugins beweisen, nicht Issuer/TLS/Audienceprüfungen ausschalten.

Der bestehende Gateway muss Multipartgröße und Timeout für den neuen Uploadweg unterstützen. `client_max_body_size`, Pluginlimit und Reverse-Proxytimeout konsistent einstellen, mit begrenztem Overhead für Multipart. Kein global unbegrenzter Body. Form-/Hiddenparameter bleiben untrusted; wenn umfangreiches Multipartparsing sonst vor der Berechtigungsprüfung stattfindet, Dataset/Issue aus einer separaten autorisierten Auftragsvorbereitung binden und den anschliessenden Stream nur dieser Submission zuordnen.

Ein Run benutzt das **versionierte geprüfte Runnerbundle** seines Kandidaten. Kein frischer beweglicher Checkout von `main` nach Auftragserstellung, der plötzlich anderen Code oder andere Modelle ausführt. Bundle-/Repo-/Imagehash gehören in Plan/Ergebnis. Keine Token-/Secretwerte in den Hashinput aufnehmen, der öffentlich protokolliert wird.
