# SPEC_INGESTION_API – verbindlicher Lieferauftrag statt freier Jobparameter

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Dieses Kapitel beschreibt die interne API und die technische Persistenz. Es sind **Zielverträge**, keine Behauptung bereits existierender Endpunkte.

## 1. Vertrauensgrenzen

Das Plugin ist ein vertrauenswürdiger Client, der Benutzer ist es nicht. Die Admin-API trifft alle fachlichen Entscheidungen erneut. Eine `submissionId` ist eine Referenz, **kein** Berechtigungstoken. Ein gültiger Diensttoken erlaubt nur die seinem Dienst zugewiesenen Aktionen; er ersetzt weder Benutzerprüfung noch die Bindung an einen konkreten Lauf.

Drei getrennte Zugriffsarten:

| API-Nutzer | Identitätsnachweis | Zweck |
|---|---|---|
| Interaktive Fachperson über Plugin | Aktueller Benutzer-Access-Token mit `iss/sub/aud/exp`, zusätzlich interner Plugin-Dienstnachweis | Liste, Auftrag anlegen/versiegeln, eigener Status, bewusster Retry/Cancel. |
| Jenkins-Dispatcher/Executor | Client-Credentials-Access-Token eines eigenen Keycloak-Clients; feste Audience und eng definierte Rollen | Offene Aufträge reservieren, Execution claimen, Ergebnisbelege melden, Abschluss anfordern. |
| Admin-Managementbrowser | Bestehender geprüfter Browser-/Gatewayweg | Lieferrechte und CSV-Konfiguration verwalten, zulässige Vorgänge ansehen. |

Keine rohe `X-User: anna`-Identität. Kein als Benutzer-ID getarnter Jenkins-Systemaccount. Kein ausschliessliches Vertrauen in einen erfolgreich angemeldeten Browser: der Benutzer-Token wird durch Admin erneut geprüft. Tokenpersistenz ist Sache des geprüften OIDC-Plugins; die Ingestion-DB und Pipelineparameter enthalten keine Tokens.

Interne API nur im Compose-Netz; APISIX darf `/internal/*` nicht öffentlich weiterleiten. Interne Netzwerkadresse allein ist keine Authentifizierung. Servicecredentials dürfen nicht über Uploadparameter gewählt werden. Timeouts/Fehler liefern 503 und bewirken keine neue Verarbeitung.

## 2. Technische Datenhaltung `di_ingest`

Explizite SQLmigrationen, enge Berechtigungen und FK-/Unique-/Checkconstraints. Kein automatisch generiertes ORM-Schema. Die benötigten Fachänderungen laufen weiterhin über Cayenne und `AuditedUnitOfWork`. Technische Zustandsoperationen dürfen parametriertes JDBC innerhalb einer bewusst gemeinsamen PG-Transaktion verwenden; kein zufälliges Mischen unabhängiger Transaktionsmanager.

### 2.1 Submission

| Feld | Bedeutung / Invariante |
|---|---|
| `id uuid` | Servergenerierte stabile Liefer-ID. |
| `dataset_id`, `issue_id` | Feste fachliche Referenzen; Ausgabe gehört zum Dataset. |
| `submitted_by`, `issuer_snapshot`, `subject_snapshot` | Tatsächlich geprüfte Person. Keine spätere Umschreibung durch Jenkins. |
| `created_at`, `sealed_at` | Serverzeiten UTC. |
| `idempotency_key`, `request_digest` | Unique je Principal und Aktion; gleicher Key/anderer Inhalt → 409. |
| `mode` | `replace` oder `append`, vom aktuellen genehmigten Vertrag erlaubt. |
| `configuration_digest`, `definition_key`, `definition_sha256`, `model_set_sha256` | Unveränderlich gebundener Verarbeitungsvertrag. |
| `original_name`, `input_size`, `input_sha256` | Bereinigter Anzeigename; Pfad wird daraus **nicht** konstruiert. Hash/Größe aus tatsächlichem begrenztem Stream, nach Seal immutable. |
| `status`, `status_version` | Zulässige Zustandsübergänge und optimistic compare-and-set. |
| `comment` | Begründung/Kommentar, begrenzt; kein ausführbarer Inhalt. |
| `base_version_id` | Beim exklusiven Dataset-Dispatch festgelegter Vorgänger, für append verbindlich. |
| `reserved_version_id` | Einmal serverseitig reservierte UUID; höchstens eine veröffentlichte Version je Submission. |
| `published_version_id`, `publication_revision` | Nach verbindlichem Commit gesetzt, danach unveränderlich. |
| `last_error_code`, `safe_message` | Bereinigte Diagnose ohne Rohdaten/Credentials. |

Vor Seal sind nur Auftragsvorbereitung und Upload möglich, keine GRETL-Verarbeitung. Vom Benutzer gelieferte Hashes sind höchstens ein Plausibilitätswert; der Pluginstream bestimmt den tatsächlichen Hash, und der Job prüft ihn nochmals.

### 2.2 Execution

`id`, `submission_id`, `attempt_number`, `fence`, `dispatch_id`, `runner_principal`, `jenkins_job`, `jenkins_run_id`, `state`, `heartbeat_at`, `lease_expires_at`, `lease_secret_hash`, `started_at`, `finished_at`. Eindeutigkeit mindestens `(submission_id, attempt_number)` und `(submission_id, fence)`. Nur eine aktive Execution pro Submission; reservierter Dataset-Slot verhindert parallele Annahmen desselben Datasets.

Der zufällige Lease-Nachweis wird nur dem vertrauenswürdigen Plugin für den konkreten Lauf ausgegeben, gehasht gespeichert und in Jenkins verschlüsselt/zugriffsgeschützt gehalten. Er gehört nicht in sichtbare Buildparameter, URLs oder Artefakte. Alle Callbacks brauchen aktuellen Service-Token **und** gültige Executionbindung/Fence.

Ablaufzeit eines Lease beweist nicht, dass der alte Prozess aufgehört hat. Ein neuer Versuch darf beginnen, wenn der alte Lauf nachweislich beendet/abgebrochen ist, oder alle verbliebenen Schreibwirkungen durch getrennte Attemptpfade und zentrale Abschlussprüfung unschädlich sind. Ein unbekannter laufender CH-Query wird nicht blind als beendet behandelt.

### 2.3 Dataset-Slot / Dispatch

Eine kleine Tabelle `dataset_execution_slot` mit eindeutiger Dataset-ID, Submission-/Dispatchbindung und Zustand genügt. Kein verteilter Scheduler, kein Redis, keine neue Messagebrokerinfrastruktur. Officeübergreifend parallel, pro Dataset genau eine verbindliche Verarbeitung; alle Ausgaben dieses Datasets teilen den Slot im MVP.

`dispatch` hält den auszuführenden Auftrag dauerhaft in PG. Die Übermittlung an Jenkins ist **at least once**; Jobclaim/Fence/Receipt verhindern doppelte Fachwirkung. Keine Behauptung exakt einmaliger HTTP- oder Queuezustellung.

### 2.4 ArtifactEvidence / Event

`artifact_evidence`: Execution, Distribution-UUID, feste Objekt-Key-Zuordnung, Format, Media-Type, Bytezahl, SHA256, vollständiger Snapshotbezug; bei gleicher Execution/Slot nur identische Wiederholung. Freie URLs oder andere Bucketnamen zurückweisen.

`execution_checkpoint`: Input-/Validator-/Snapshot-/Outputbelege mit expliziten Versionen/Hashes. Nur serverseitig erlaubte Checkpointtypen. Keine riesigen ungeprüften JSON-Dokumente.

`event`: append-only Zustands-/Annahme-/Fehler-/Retryereignis mit Actor, Initiator, Zeitpunkt, Submission, Execution und Command-ID. Keine Heartbeatvollprotokollierung und keine Tokenwerte. Diese Historie erklärt den Prozess; der fachliche Audittrigger erklärt die tatsächlichen Tabellenänderungen.

## 3. Zustandsmaschine

| Zustand | Bedeutung | Zulässiger nächster Schritt |
|---|---|---|
| `UPLOADING` | Auftrag autorisiert, Input noch nicht versiegelt | `READY`, `CANCELLED`, `UPLOAD_FAILED` |
| `READY` | Hash/Größe und Vertrag gebunden | `QUEUED`, `CANCELLED`, `REJECTED_AUTHORIZATION` |
| `QUEUED` | Dispatch reserviert; Queuezustellung kann wiederholt werden | `VALIDATING`, kontrolliert zurück nach `READY`, `CANCELLED`, `REJECTED_AUTHORIZATION` |
| `VALIDATING` | Job hat exklusiv geclaimt und Input bestätigt | `STAGING`, `REJECTED_VALIDATION`, `FAILED_RETRYABLE`, `REJECTED_AUTHORIZATION` |
| `STAGING` | Kandidat/Snapshot/Outputs werden privat aufgebaut | `READY_TO_COMMIT`, `FAILED_RETRYABLE`, `REJECTED_VALIDATION`, `REJECTED_AUTHORIZATION` |
| `READY_TO_COMMIT` | Alle Nachweise vorhanden, noch keine fachliche Veröffentlichung | `COMMITTED`, `FAILED_RETRYABLE`, `REJECTED_AUTHORIZATION`, `CONFLICT` |
| `COMMITTED` | PG-Fachcommit erfolgt; Dateien und immutable CH-Version sind vorhanden | `PUBLISHED` oder Projektion bleibt offen mit Fehlerdiagnose |
| `PUBLISHED` | PG und erwartete CH-current-Projektion stimmen | terminal; kein erneutes Commit |
| `FAILED_RETRYABLE` | Kein neuer Fachcommit, klarer technischer Fehler | explizit autorisierter Retry mit neuer Execution |
| `REJECTED_VALIDATION`, `REJECTED_AUTHORIZATION`, `CONFLICT`, `CANCELLED`, `UPLOAD_FAILED` | Kein neuer veröffentlichter Stand | keine implizite Reaktivierung; neuer Auftrag bzw. ausdrückliche neue Prüfung |

Ein `COMMITTED`-Auftrag darf bei einem Jenkins-/HTTP-Fehler **nicht** wieder zu „fehlgeschlagen, nie veröffentlicht“ gemacht werden. UI zeigt „Angenommen; SQL-Aktualisierung ausstehend“. Wiederanlauf repariert die abgeleitete SQLsicht. Ein nach dem Fachcommit entzogener Liefergrant macht bereits angenommene Daten nicht rückwirkend ungültig.

## 4. Interaktive API

Präfix `/internal/ingestion`. Alle mutierenden Requests JSON mit begrenzter Größe und `Idempotency-Key`; keine GET-Mutation. `application/problem+json` bzw. ein einheitlicher Problem-DTO mit maschinenlesbarem Fehlercode. Schema-/Versionkennung in jedem Plan, **keine** parallele Legacy-API.

| Methode / Pfad | Request | Ergebnis / Pflichtprüfung |
|---|---|---|
| `GET /datasets` | Paging, optionale Suche | Nur aktuell lieferfähige Datensätze des Users, passende Ausgaben und erlaubte Modi; Definitionhash und Revisionsbezug. |
| `POST /submissions` | `datasetId`, `issueId`, `mode`, `expectedConfigurationDigest`, `comment` | 201 mit ID/Status; Rechte/Status/Scope/Konfiguration frisch prüfen. |
| `POST /submissions/{id}/seal` | `inputSize`, `inputSha256`, `originalName`, Pluginspool-Nachweis | Owner + aktuelles Lieferrecht; innerhalb Uploadlimit; einmaliger Übergang nach READY. |
| `GET /submissions/{id}` | – | Nur eigener aktiver Lieferant oder zuständiger Lieferantenmanager; sichere Status-/Fehler-/Versioninfos. |
| `GET /submissions` | Paging/Filter | Gleicher Scope, keine globale Jenkins-Runliste. |
| `POST /submissions/{id}/cancel` | `expectedStatusVersion`, `reason` | Nur vor Commit, aktuelle Actorprüfung; aktiven Worker fence-invalidieren und stoppen, keine Datenlöschung. |
| `POST /submissions/{id}/retry` | `expectedStatusVersion`, `reason` | Rechte frisch; nur retryfähiger unveränderter Auftrag, sonst neue Submission nötig. |
| `GET /submissions/{id}/report` | – | Bereinigte strukturierte Validatorinfos; kein Rohlog-/Objektpfadzugriff auf fremde Daten. |

Ein fremder UUID-Aufruf wird abgewiesen, auch wenn der Nutzer dieselbe Organisation lesen darf. `read_data` verleiht kein Recht auf Lieferprovenienz. Auftragsgröße und Filename begrenzen; Fehlermeldungen dürfen keine privaten Existenzdetails anderer Datasets verraten.

Fehlercodes mindestens `NOT_AUTHORIZED`, `PRINCIPAL_INACTIVE`, `CONFIGURATION_CHANGED`, `ISSUE_NOT_AVAILABLE`, `MODE_NOT_ALLOWED`, `INPUT_TOO_LARGE`, `INPUT_MISMATCH`, `IDEMPOTENCY_CONFLICT`, `DATASET_BUSY`, `INVALID_STATE`, `STALE_EXECUTION`, `VALIDATION_FAILED`, `ARTIFACT_CONFLICT`, `PUBLICATION_CONFLICT`, `DEPENDENCY_UNAVAILABLE`.

## 5. Dispatcher-/Executor-API

Eigenes Serviceclient-Audience/Role-Profil, keine breit administrativen Keycloak-Rechte. Dienst- und Browserdecoder unterscheiden; ein Benutzer-JWT kann keinen Executorendpoint bedienen und umgekehrt.

| Methode / Pfad | Vertrag |
|---|---|
| `POST /dispatch/reserve` | Nächsten/konkreten READY-Auftrag unter Dataset-Slot reservieren; alte Rechte/Konfiguration frisch prüfen. Liefert `dispatchId`, `submissionId`, fester Jobname. |
| `POST /dispatch/{id}/queued` | Bekannten Queuebezug melden; idempotent bei identischer Bindung. Keine beliebige Job-URL als Autoritätsquelle. |
| `POST /executions/claim` | Nur gültiger Dispatch, richtiger Job, richtige Jenkinsinstanz, noch kein Gewinner. Liefert Execution/Fence/Lease sowie unveränderlichen Plan. |
| `POST /executions/{id}/heartbeat` | Lease verlängern; nur aktuelle Execution, keine Zustands-/Rechteänderung. |
| `POST /executions/{id}/checkpoint` | Erlaubter Schritt, monotone Folge, Belege gegen Plan prüfen. Niemals `status=PUBLISHED` als freie Angabe akzeptieren. |
| `POST /executions/{id}/complete` | Streng typisierter ResultManifest; Nachweise/Plan/Fence/Userrechte/Vertragsfingerprint prüfen, dann Fachcommit. |
| `POST /executions/{id}/fail` | Bereinigter Fehler, Retryklassifikation serverseitig; Zustand COMMITTED/PUBLISHED niemals zurückstufen. |
| `GET /dispatch/reconciliation` | Noch nicht eindeutig zugestellte Aufträge der eigenen technischen Jenkinsinstanz; keine Daten-/User-Tokenausgabe. |

Queue-HTTP-Timeout: Dispatcher sucht anhand stabiler Dispatch-ID und `DeliveryQueueAction`, nicht blind ein zweites anderes Submissionobjekt erzeugen. Doppelte Queuezustellung kann auftreten, aber nur ein Claim gewinnt. Eine Wiederausführung bindet wieder dieselbe Originaldatei und denselben technischen Vertrag; bei geänderter Konfiguration ist ein neuer fachlicher Auftrag erforderlich.

## 6. Plan- und Ergebnis-DTOs

`CsvExecutionPlan` enthält ausschliesslich serverbestimmte und validierte Felder:

```text
schemaVersion, submissionId, executionId, fence
initiatorPrincipalId (kein Token), datasetId, issueId, reservedVersionId
mode, baseVersionId, definitionKey, definitionSha256
modelFiles[{relativePath, sha256}], modelSetSha256, qualifiedTableName
csvDialect, orderedColumns, rowKeyDefinition, fullSchemaDigest
input{size, sha256, privateSpoolReference}
outputs[{distributionId, format, objectKey, fileName, mediaType}]
clickhouse{candidateDatabase, candidateTable, publicationName}
limits{maxBytes, maxRows, maxCellBytes, timeoutSeconds}
```

Der technische Runner ergänzt lokale feste Credentialbindings und Arbeitsverzeichnisse, niemals vom Browser kommende Zugangsdaten. `objectKey` muss exakt zum vorgesehenen Distribution-/Format-Slot passen. `candidateTable` stammt aus erlaubten IDs, nicht aus Dataset-Titeln.

`CsvResultManifest` bindet dieselben IDs/Fence/Planhash, Inputhash, Validatorversion und Ergebnis, Modellsethash, Quell-/Gesamtzeilen, fachlichen Datenhash, CH-Schema-/Zeilenbeleg, je Output tatsächliche Hashes/Größen und den verwendeten Runner-/Repo-/Imagehash. Timeouts oder Fehler werden nicht als success manifestiert. Maximalgrößen/Listenlängen und unbekannte Felder strikt behandeln.

## 7. Klassen-/Methodenplan ADMIN

| Klasse / Methode | Verantwortung |
|---|---|
| `IngestionUserController` | Interaktive Endpunkte; geprüfter Actor, keine vom Body übernommene Identität. |
| `IngestionExecutionController` | Service-/Executionendpunkte; Actor aus Service-JWT, Auftrag aus DB. |
| `IngestionSecurityConfiguration` | Separate Filterketten, feste Audience/Issuer/Algorithmen, Plugin-Dienstnachweis, 401/403/503. |
| `SubmissionService.create(...) / seal(...) / cancel(...) / retry(...)` | Fachlich autorisierte Zustandsoperationen und Idempotenz. |
| `SubmissionRepository.insert(...) / findForActor(...) / compareAndSetState(...)` | Parametrisierte SQL, eindeutige IDs und aktuelle Revisionen. |
| `DatasetExecutionSlotRepository.reserve(...) / release(...)` | Exklusive Datasetverarbeitung mit belegtem Besitzer; keine fremde Slotfreigabe. |
| `DispatchService.reserve(...) / confirmQueue(...) / reconcile(...)` | Persistenter Dispatch, at-least-once-sichere Jobbindung. |
| `ExecutionService.claim(...) / heartbeat(...) / recordCheckpoint(...) / fail(...)` | Fence/Lease und erlaubte Transitionen. |
| `CsvExecutionPlanFactory.create(submission, execution, definition)` | Keine frei bestimmbaren Targets; exakt genehmigtes Schema. |
| `ResultEvidenceValidator.validate(plan, result)` | Struktur, IDs, Fingerprints, Größen, Counts, Pflichtformate und Validatorergebnis. |
| `PublicationService.complete(execution, result, command)` | Wiederholbarer verbindlicher PG-Fachcommit; entscheidet selbst. |
| `ClickHousePublicationProjector.project(datasetId, revision)` | Aktualisiert aus **aktuellem PG-Soll** die abgeleitete current-Sicht; keine ältere Callbackrevision durchsetzen. |
| `PublicationReconciler.reconcilePending(limit)` | Nur offene COMMITTED-Projektionen; keine Rohdaten-Neuladung/erneute fachliche Annahme. |
| `SubmissionQueryService.detail/list/report(...)` | Scopegefilterte fachliche Anzeige ohne Roh-Jenkinslogs. |
| `IngestionEventRecorder.append(...)` | Nachvollziehbarer Zustand/Actor/Initiator; keine Secrets. |

Bestehende `DeliveryRegistrationService`-Kernoperationen refaktorieren statt eine parallele Veröffentlichung einzuführen. Neuer CSVabschluss braucht weder einen `manage_metadata`-Grant des Lieferanten noch einen freien globalen `publish`-Grant des Workers. Er wird durch gültiges `submit_data`, genehmigte Autopublikation und den gebundenen Ausführungsvertrag legitimiert. Die vorhandene Operatoraktivierung darf keinen Bypass für diese Checks bilden.

## 8. Fachcommit und Cross-Store-Konsistenz

Vor `complete` liegen vollständig verifizierte Dateioutputs und ein vollständiger **privater immutable** ClickHouse-Kandidat vor. Netzwerk-/Hashprüfungen finden ausserhalb der kurzen Fachtransaktion statt; die Belege sind danach an unveränderliche Keys und Execution gebunden.

Die PG-Transaktion:

1. Autorisierungs-Guard und Dataset/Submission in fester Reihenfolge sperren.
2. Erneut Principal aktiv, gültiges `submit_data`, aktive Konfiguration/Autopublikation, Dataset/Ausgabe published, gleiche Modell-/Definitionhashes und unveränderter Ausgangsstand prüfen.
3. Execution/Fence und vollständig erfolgreiche Ergebnisse prüfen; ein bereits vorhandener Commit derselben Submission wird identisch zurückgegeben.
4. Version/Distributionen mit `success/available`, vollständigen Counts/Hashes und Provenienz anlegen; `currentVersion` setzen. Historische Outputs/Versionen bleiben.
5. Fachliche `CatalogAction`, generisches Audit, Submission `COMMITTED` und ausstehende CH-Projektion **atomar in PG** speichern.
6. Commit. Erst danach Erfolg der fachlichen Annahme antworten. HTTPverlust nach diesem Schritt wird durch Abfrage/Idempotenz erkannt.

Danach projiziert `ClickHousePublicationProjector` die aktuelle PG-Revision. Ein erfolgreicher Abschluss ergibt PUBLISHED. Während des begrenzten Projektionsfensters können der neue Datei-/Katalogstand und die bisherige CH-current-Sicht auseinanderliegen. Das ist ausdrücklich **keine** Cross-DB-Atomarität. Der vollständige neue CH-Snapshot ist bereits vorhanden; die UI zeigt offene SQLaktualisierung, kein falsches „alles fertig“. Neue Jobs desselben Datasets warten bis die Projektion eindeutig abgeschlossen oder kontrolliert repariert ist.

Nur der zentrale Projector darf die stabile CH-current-Sicht ändern. CSV-Executions schreiben ausschliesslich eigene Kandidaten. Ein alter/abgelaufener Worker kann deshalb niemals nachträglich einen jüngeren aktuellen Stand zurückdrehen. Der Projector liest bei jedem Retry die aktuelle PG-Zielrevision; doppelte ältere Aufrufe sind No-op bzw. werden überholt. Pro Dataset nur ein Projector mit überprüftem Queryabschluss; bei unbekannt weiterlaufender Query keinen zweiten widersprüchlichen Austausch starten.

Die für den Projector nötige technische CH-Verbindung ist getrennt vom allgemeinen Writer und vom Browserkontext. Sie darf nur die vorgesehenen Sichten auf freigegebene Snapshots verändern; keine persönlichen Userrechte vergeben. Das ist ein internes Modul in Admin, **kein** neuer Dienst.

## 9. Fehler- und Entzugssemantik

- Nach Seal Datei ausgetauscht: Jobhash passt nicht → reject, keine Load-/Commitwirkung.
- Nutzerrecht während Queuezeit entzogen: Claim lehnt ab.
- Nutzerrecht während Validierung/Upload entzogen: Verarbeitung kann technisch auslaufen; `complete` lehnt vor Commit ab. Kandidaten bleiben unzugänglich.
- Letzter erfolgreicher Grant wurde revoked, aber anderer gültiger Gruppen-/Officegrant besteht: Recht bleibt effektiv erlaubt. Tests müssen vollständige Berechtigungswege berücksichtigen.
- Autorisierungs-/PG-Ausfall: keine Annahme und keine neue Veröffentlichung; Retry braucht frische Prüfung.
- S3/CH-Erfolg mit verlorenem HTTPack: existente konkrete Artefakte prüfen; nicht blind nochmals appendieren oder überschreiben.
- PGcommit erfolgreich, CHprojektion fehlerhaft: COMMITTED bleibt, nur Projektion reparieren. Keine „Rollback“-Löschung veröffentlichter Dateien.
- Benutzer klickt doppelt: gleicher Idempotenzkey ergibt denselben Auftrag. Neue bewusste Lieferung identischer Bytes ist nicht pauschal verboten; append-Kollisionen werden fachlich validiert. Dateihash allein ist kein universeller Lieferidentifikator.

## 10. Serialisierung, Timeoutantwort und Uploadkonkurrenz

Idempotenz-/Planhashes werden über eine **versionierte deterministische UTF-8-Kanonisierung** der typisierten DTOs gebildet: feste Feldnamen/-reihenfolge, definierte Nullbehandlung, keine nichtdeterministische `Map.toString()`-/Java-`hashCode()`-Signatur. Binär- und Dezimaldaten nicht vorher in Float umwandeln. Testvektoren im Contracttest festhalten.

`complete` liefert bei sofort fertiger Projektion 200/PUBLISHED, bei verbindlich erfolgreichem PGcommit und noch offener SQLprojektion 202/COMMITTED. Wiederholter identischer Request liefert dieselbe Version; ein anderer ResultDigest für dieselbe bereits committete Submission ist ein Konflikt. Ein Commitfehler ohne Erfolg liefert keinen 2xx-Scheinstatus. UIpolling benutzt die sichere Status-API, nicht eine Vermutung aus Jenkins-Exitcode.

Für denselben UPLOADING-Auftrag darf nur ein aktiver begrenzter Stream die finale Inputdatei versiegeln. `IncomingUploadStore` benötigt einen atomaren Besitz-/Zustandsschutz. Ein zweiter paralleler Upload darf eine bereits versiegelte Datei weder ersetzen noch truncaten. Gleicher Idempotenzkey mit anderer Datei wird spätestens bei Seal als Konflikt erkannt. Ein abgebrochener Teilupload darf nicht über seine deklarierte Content-Length als vollständig gelten.

Ergebnisbelege sind **Attestierungen des vertrauenswürdigen Ausführungsdienstes** nach tatsächlichen Read-back-/Hash-/Typprüfungen, keine magischen unabhängigen Storagebeweise. Admin hat absichtlich keinen allgemeinen S3-Schlüssel. Die Sicherheitsprüfung verhindert, dass ein Lieferant sich als Executor ausgibt oder beliebige Artefakte annehmen lässt. Eine vollständig kompromittierte Plattform-/Runneradministration bleibt ausserhalb dieser MVP-Vertrauensgrenze; das wird nicht als kryptografisch ausgeschlossen behauptet.
