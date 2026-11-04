# Review MA-B / 20261104T153442Z

## Urteil

**ABGENOMMEN**

Am exakten Kandidaten-SHA-Satz wurden alle Pflichtchecks M07–M13 frisch
ausgeführt, alle bestanden; eine eigene Gegenprobe wurde real ausgeführt und
bestand; der Produktbaum ist vor/nach unverändert. Offene BLOCKER/MAJOR: keine.
Zwei nicht blockierende MINOR-Hinweise sind unten dokumentiert.

## Bindung

| Element | Wert |
|---|---|
| Handoff-SHA256 | 0bbcd7e696fc0c75d4ef13e1f99438d28bb18731fe1d98458b3b2b2b3a649b87 (selbst geprüft) |
| Spezifikationsaggregat | a4b6e4708d5028dafcd2fc465bae556de47307b94dce05069a9ba3ca06a89303 (aus den 12 einzeln geprüften Dateihashes reproduziert) |
| Request-SHA256 | 7661ab331cdb3048fe38c5daa4fff4f48a3b319d24e2b2b897d89c2191da57b5 (selbst geprüft) |
| dateninfrastruktur-dev-stack | 4387c9bf702109f28542753b95e541ee2a212ae4 (base fd249186b302aa3147ebfe445767a502eab3b826, Vorfahre) |
| dateninfrastruktur-admin | 9536465ed4af211bf8b88e435baaec28fb6d01b7 (base 8cde32c04e32259b148eda553edd60c936f76abd, Vorfahre) |
| dateninfrastruktur-sodata | 8349be8aba4036ca0bb56e89cb62398e34404a5e (unverändert, base=head) |
| Workspace-AGENTS | 02e456b5a6b0b37d2fdd87314304926f77f6b675aa01cfd7ed366544aae0f091 |
| Reviewer | OpenCode v2.2.5 (Desktop-CLI .../cli/2.2.5-arm64/opencode-cli), Modell deepseek/deepseek-flash |
| Session | ses_e58cd3a23ffe1og6EzDDOtAIfg |
| Isolation | eigener git archive HEAD-Ausschnitt unter genehmigtem Temp-Pfad; je Lauf eigener PG16/PostGIS-Container mit Zufalls-Loopbackport, frischen Testcredentials, nur eigener Container/Volume entfernt |

Alle 12 Spezifikationsdateien wurden einzeln gegen den Handoff gehasht; der
Aggregatwert wurde aus genau dieser Map (json.dumps(..., sort_keys=True))
reproduziert. Alle drei Checkout-HEADs stimmen exakt mit dem Handoff überein;
git status --porcelain war vorher und nachher leer.

## Code und Zielerreichung

Gelesen wurden der vollständige Diff base..head beider geänderten Repos sowie
die neuen Quellen/Migrationen/Skripte und die unveränderten Modelle:

- **ili2pg/Cayenne-Mapping:** echtes 5.5.2-UUID-Schema mit 16 physischen
  Fachklassen; t_id aus der realen di_management.t_ili2db_seq, UUID-Attribute
  kontrolliert aus db/model-mapping.json normalisiert; IliPkGenerator
  reserviert auf der bestehenden Transaktionsconnection, keine eigene
  AUTO_PK-Welt und kein Runtime-DDL. Generierte Unterstrich-Basisklassen und
  handgeschriebene Unterklassen sind getrennt; der zweite cdbimport/cgen-Lauf
  ist byte-identisch (zusätzlich extern 56/56 Dateien gegen die committeten
  Kandidatendateien verglichen).
- **Transaktion/Actor:** AuditedUnitOfWork startet die äussere
  Cayenne-Transaktion, AuditContextWriter bindet Actor/Request/Command per
  transaktionalem SQLExec; IT belegt gleiche pg_current_xact_id(), echten
  Actor und session_user=di_writer, Rollback nach erfolgreichem ORM-Flush,
  Einerpool-Trennung Anna/Ben und Schreiben ohne Actor.
- **Audit/Migrationen:** V001–V006, BEFORE-Stempel, AFTER-I/U/D auf allen 16
  Tabellen, Redaction, Immutabilität von Entscheiden, einmaliger Widerruf,
  Rootrevision bei Childänderungen, Coverage-Verifier, Idempotenz.
- **Rollen/Public:** di_writer, di_authz, di_public ohne Owner-/DDL-/
  TRUNCATE-/Audit-Rechte; Public nur auf expliziten api_public-Views.
- **Lebenszyklus/Start/Restore:** explizites Setup, bekannter Schema-Re-run
  ohne Reimport, Vertragsfingerprint, Start ohne DDL mit eingeschränktem
  Writer-/Authz-Konto, echte Readiness 200→503→200, pg_dump/pg_restore in
  separate DB, XTF-Export/-Validierung.

Nicht betroffen/ausserhalb MA-B: Admin-UI, OIDC/JWT/CSRF-Benutzerkette,
Portal-DB-Umschaltung, S3-/Gateway-Downloads (MA-C–MA-E). Deren Quellen wurden
nicht als erbracht gewertet.

## Selbst ausgeführte Tests

Hauptkommando (exakt der STACK-Dispatcher, der intern
test_persistence_all.py und danach compatibility.py aufruft):

    cwd:  /private/var/folders/0z/1lwhf37x0h9858xcm889mbz80000gn/T/opencode/ma-b-review-20261104T153442Z/dateninfrastruktur-dev-stack
    cmd:  ./scripts/management/test.sh --phase MA-B
    exit: 0 (erwartet 0)

Der Lauf erfolgte auf einem byte-identischen git archive HEAD-Ausschnitt der
Kandidaten, damit der Harness committete, regenerierte Artefakte nicht im
Kandidaten selbst überschreibt. Die Regenerierung wurde extern verglichen:
db/mapping-profile.json, db/audit-policy.json,
db/persistence-contract.properties, management.map.xml und alle generierten
Java-Dateien sind 56/56 byte-identisch zum Kandidaten
(evidence/reproducibility.txt).

| ID | Nachweis im Lauf | Erwartet/Beobachtet | Beleg |
|---|---|---|---|
| M07 | reales ili2pg-Schema, 16 Entitäten, drei verbundene Klassen, zweiter cdbimport/cgen identisch, ili2pg-Export + ilivalidator, UUID/MTEXT erhalten | 0/0 | evidence/test-sh-MA-B.log (Zeilen M07 PASS), evidence/reproducibility.txt |
| M08 | AuditedUnitOfWorkIT (2x): Tx-ID/Actor/DB-User, Rollback nach Flush, Einerpool, fehlender Actor, FOR UPDATE/Stale, UTC unter Pacific/Auckland | 0/0 | evidence/M07-M13-junit/first/TEST-...AuditedUnitOfWorkIT.xml (tests=1, skipped=0, failures=0) |
| M09 | I/U/D, Keyword-/Membershipinsert, Old/New/Rootbezug, Parent-vor-Child, Redaction, No-op, erzwungener Auditfehler rollt Fachmutation zurück | 0/0 | evidence/M07-M13-logs/step-5.log |
| M10 | Publicsicht positiv, Basistabellen/Audit/Grant gesperrt, Writer/Authz-Negativfälle, Immutabilität, Schema-/Versionszeiger | 0/0 | evidence/M07-M13-logs/step-5.log |
| M11 | Coverage 16 Tabellen, deaktivierter Trigger erkannt, Installer idempotent, HTTP-Readiness 200→503→200 (JUnit tests=2) | 0/0 | evidence/M07-M13-logs/step-5.log, evidence/M07-M13-junit/second/TEST-...ManagementStartupIT.xml |
| M12 | additive Revision über vorhandenen ORM-UUID-/Auditdaten, Setup-/Installer-Re-run erhält IDs/Audit, kein Reimport | 0/0 | evidence/M07-M13-logs/step-5.log |
| M13 | echter pg_dump/pg_restore in separate DB, IDs/Audit/Publicrechte erhalten | 0/0 | evidence/M07-M13-logs/step-5.log |

Zusätzlich lief im selben Kommando die MA-0-Regressionsprobe
(compatibility.py) erfolgreich: eigener PG16/PostGIS-Container, Boot/Cayenne-
Actor/Transaktion, ili2pg-UUID-Schema mit PostGIS; Exit 0, Endzeile
"PASS Boot/Cayenne/PostgreSQL actor/transaction + ili2pg UUID schema with PostGIS".

## Übernommene Nachweise

Keine. Alle Pflicht-IDs M07–M13 wurden in diesem Review neu ausgeführt; es wurde
kein fremder MA-B-Beleg übernommen.

## Eigene Gegenprobe

- **Hypothese:** Wenn "Childänderungen invalidieren die Rootrevision" nur für
  direkte Dataset-Updates gälte, bliebe Dataset.row_version bei einem
  DatasetIssue.label-Update unverändert und ein veraltetes Formular würde
  weiter akzeptiert. Zusätzlich: dürfte di_writer einen Audittrigger
  deaktivieren, wäre die Auditabdeckung zur Laufzeit abschaltbar.
- **Neuer Input/Aufbau:** eigenes Skript
  output/counterexample/probe_child_revision.py, eigener frischer PG16/PostGIS-
  Container (Label di.phase=MA-B, Zufallsport), Rollen, V001/V002/V005,
  Aggregat-Trigger wie im Setup, dann Datensatz/Amt/Ausgabe als di_writer im
  expliziten Actor-/Transaktionskontext.
- **Erwartung:** Kind-Update row_version +1 und Kind-Auditzeile mit
  Root-Dataset-UUID; No-op ohne Änderung; direktes Dataset-Update +1;
  DISABLE TRIGGER als Writer verweigert, Trigger bleibt O.
- **Beobachtet:** 2→3 (Kind-Update), aggregate_dataset_oid = Dataset-UUID,
  3→3 (No-op), 3→4 (direktes Update), ALTER TABLE ... DISABLE TRIGGER
  mit "must be owner of table groupmembership" verweigert, tgenabled=O.
  Exit 0; eigener Container im finally nur nach Labelprüfung entfernt.
- **Schlussfolgerung:** Beide Verträge halten; kein Defekt gefunden.
- **Beleg:** output/evidence/counterexample-child-revision.log (Rohausgabe,
  inkl. Exit 0) und output/evidence/counterexample-result.json.

## Findings

### MA-B-REV-01 — MINOR (nicht blockierend)
- **Datei/Methode:** scripts/normalize_cayenne_uuid.py, ManagementRuntime,
  SchemaContractHealthIndicator (kein CayenneMappingVerifier).
- **Vertrag:** SPEC_PERSISTENCE_AUDIT §4 nennt
  CayenneMappingVerifier.verifyPhysicalMapping(connection, profile);
  §2.1 verlangt die Prüfung des aufgelösten Mappings beim Setup.
- **Beobachtung:** Das physische Mapping ist indirekt über den Hash von
  db/model-mapping.json in persistence-contract.properties, den DataMap-Hash
  beim Start und die t_id-Typ-/Default-Prüfung gebunden; ein spaltenweiser
  Abgleich information_schema gegen das Profil fehlt.
- **Minimaler Fix:** schmaler, rein lesender verifyPhysicalMapping-Vergleich
  (Spalten/Typen/Defaults) gegen db/model-mapping.json, aufgerufen bei
  explizitem Setup bzw. Readiness.
- **Nicht blockierend:** Das aktuelle Mapping wurde real reproduziert
  (56/56 byte-identisch) und alle M07–M13-Verhalten bestanden.

### MA-B-REV-02 — MINOR (nicht blockierend)
- **Datei/Methode:** scripts/contract_fingerprint.py (Zeilen 13–19).
- **Vertrag:** Unbekannter/abweichender Bestand muss ohne Reimport/Reset
  abgelehnt werden; ein abgelehnter Vorgang soll keine Produktdatei ändern.
- **Beobachtung:** Die Datei db/persistence-contract.properties wird
  geschrieben, **bevor** der DB-Fingerprint verglichen und bei Abweichung
  abgebrochen wird. Die DB wird weiterhin verweigert und es läuft kein DDL,
  aber ein fehlgeschlagener Upgrade-Versuch hinterlässt eine geänderte
  getrackte Datei.
- **Minimaler Fix:** Digest zuerst im Speicher berechnen, mit
  di_ops.contract_fingerprint() vergleichen und die Datei erst nach
  erfolgreicher Prüfung/Entscheidung schreiben.

## Integrität und Grenzen

- **Produktstand vorher/nachher:** alle drei Repos am selben HEAD, leere
  git status --porcelain, gleiche Tree-SHAs; die 98 Admin-Dateihashes sind
  vor/nach identisch (evidence/integrity-before.txt,
  evidence/integrity-after.txt, evidence/admin-tracked-hashes-*.txt).
- **Eigene Ressourcen:** keine di-ma-Container nach den Läufen; die Skripte
  entfernten ausschliesslich ihre eigenen, labelgeprüften Container inklusive
  anonymer Volumes. Temporärer Arbeitsausschnitt und Gradle-Cache liegen
  ausserhalb der Produktbäume.
- **Secrets:** keine Original-.env, keine Credentialdateien, keine Tokens
  gelesen oder in Berichte/Logs kopiert; Testcredentials waren frisch und
  zufällig.
- **Grenzen:** M13 prüft einen begrenzten Restore in eine separate DB derselben
  eigenen Instanz, kein allgemeines Backup-/HA-Konzept. Audit ist keine
  Rechtszertifizierung und schützt nicht gegen DB-Owner/Superuser; GUC-Werte
  sind kein kryptografischer Identitätsnachweis. UI/OIDC/Gateway/Downloads
  folgen MA-C–MA-E und wurden hier nicht bewertet.
- **Pflichtstatus:** M07–M13 = EXECUTED/PASS; keine NOT_EXECUTED-Pflicht,
  keine begründeten NOT_REQUIRED-Ausnahmen in dieser Phase.


Original review.json SHA256: `9569137adacdb581ea4a5e84c9b4932ea828ed32409649d454ba8231aab7b60b`.
ACCEPTED.json SHA256: `f9be1903190d43095111a1ee10640ed6a4894d9011229956a5563c6a0ac1e9f9`.
