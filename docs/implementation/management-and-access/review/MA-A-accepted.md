# Review MA-A / 20261104T143229Z

## Urteil

**ABGENOMMEN**

Unabhängig geprüft am exakten Handoff-SHA-Satz. Die MA-A-Pflichtchecks
M03–M06 wurden in diesem Review selbst ausgeführt, eine eigene Gegenprobe
wurde ausgeführt, und der Produktstand ist unverändert. Keine BLOCKER-,
MAJOR- oder MINOR-Produktbefunde. MA-A öffnet damit das Gate zu MA-B; MA-B
bis MA-E werden hier nicht abgenommen.

## Bindung

- Phase: `MA-A`, Kandidat `20261104T143229Z`.
- Handoff SHA-256: `d536c1bdbc31a601fb6d97daad56170bfac964232f293b174e151e30fe4456d3`.
- Spezifikations-Aggregat SHA-256: `dcbf3f954b42885b3ca26aa247b875f03761aabc016e8e3a6145edd3c1318aad`.
- Request SHA-256: `001e6be1a237dbf2b35093f34ab63d7d303e70f20ad55bc86d052ca5b4a920dd`.
- Workspace-AGENTS SHA-256: `02e456b5a6b0b37d2fdd87314304926f77f6b675aa01cfd7ed366544aae0f091`.
- Repositories exakt aus dem Handoff, live nachgelesen:
  - `dateninfrastruktur-dev-stack` = `266696b296d06f2a3c9ab9e7d206a8502a2ada2a`
  - `dateninfrastruktur-admin` = `8cde32c04e32259b148eda553edd60c936f76abd`
  - `dateninfrastruktur-sodata` = `8349be8aba4036ca0bb56e89cb62398e34404a5e`
- Reviewer: OpenCode `v2.2.5` (CLI-Prozess
  `.../ai.opencode.desktop/cli/2.2.5-arm64/opencode-cli run --standalone`),
  Provider/Modell `deepseek/deepseek-flash`, Session
  `ses_e59062b15ffeyNI28YzGahRzAq` (aus dem Session-Kontext).
- Isolierung: eigener Review-Workspace unter
  `.runtime/management-review/MA-A/20261104T143229Z/workspace`; eigener
  `git archive HEAD`-Prüfstand unter `output/scratch/admin-ma-a`; eigene
  Gegenproben unter `output/scratch`; keine Original-`.env`, kein Secret und
  kein Benutzerdienst gelesen oder verändert. Für MA-A war kein
  PostgreSQL-/Compose-Dienst nötig; es wurde kein Container gestartet.

Alle 12 Spezifikationsdateien, das Aggregat, der Request, die Workspace-AGENTS,
alle drei HEADs und alle getrackten Dateien wurden unabhängig geprüft:
`output/evidence/binding-verification.txt`. Der Handoff-Hash, der
Request-Hash, der Aggregat-Hash, der AGENTS-Hash und alle drei HEADs stimmen;
alle drei Arbeitsbäume sind sauber.

## Code und Zielerreichung

Geprüft wurden die neuen INTERLIS-2.4-Modelle und ihre Artefakte in ADMIN:
`SO_AGI_DataInfrastructure_Catalog_20261104.ili` und
`SO_AGI_DataInfrastructure_Access_20261104.ili`, die positiven/negativen
XTF-Fixtures, `models/constraints.md`, der gepinnte Vokabular-Referenzcopy
`models/vendor/SO_AGI_DataCatalog_Base_20260529.ili` sowie
`scripts/test_models.py` / `scripts/model_fixtures.py` und `db/toolchain.json`.

- **Identität und Rechteanker:** Beide Modelle nutzen `OID AS
  INTERLIS.UUIDOID`; das IMD16 bestätigt `INTERLIS.UUIDOID` für alle echten
  Klassen. `Dataset` ist der einzige Katalogzielpunkt von `AccessRequest`,
  `AccessDecision` und `AccessGrant`; es gibt keine Grants an Issue, Version
  oder Distribution. `CatalogAction` verweist auf Version/Distribution nur als
  ausdrücklich erlaubten Ereigniskontext (SPEC_MODELS §3.7), nicht als
  Rechteziel.
- **Serie/Ausgabe/Version:** `Dataset(kind=standalone|series)` trägt die
  gemeinsamen Metadaten; `DatasetIssue`, `DataVersion` und `Distribution`
  enthalten keine Kopien von Titel, Beschreibung, Kontakt, Eigentümer oder
  `accessLevel`. Themen/Keywords sind normalisierte Zuordnungen; Schemata und
  Attribute sind getrennt referenziert. Die vollständigen Kind-Attributmengen
  wurden unabhängig aus dem IMD geprüft (`output/evidence/M04-evidence.txt`).
- **Workflow:** `AccessRequest`, unveränderlicher `AccessDecision`,
  beendbarer `AccessGrant` und `CatalogAction` sind getrennte Klassen. Die
  Modellconstraints erzwingen u. a. halb offene Intervalle, Scope-XOR,
  Gruppe/Member-Typen, Antragsteller=user, Request-Bezug für approve/deny,
  Grant nur aus approve/direct_grant sowie `revokedAt` zusammen mit
  `revocationDecision`. Regeln, die ILI nicht vollständig prüfen kann
  (current-Zeiger, ein pending Request, Immutabilität, Authorityprüfung,
  Dateiverfügbarkeit, Audit-Coverage), sind in `models/constraints.md`
  ausdrücklich MA-B-SQL bzw. MA-C-Service zugeordnet und nicht als bereits
  implementiert ausgegeben.
- **Audit:** Alle 9 Katalogklassen + 11 Katalogassoziationen und alle 7
  Accessklassen + 22 Accessassoziationen tragen `!!@ di.audit=full`
  (20 bzw. 29 Annotationen). `!!@ di.audit.redact=true` steht nur auf
  `Principal.displayName`.
- **Vokabulare:** Der gepinnte Vendor-Base-Copy hat SHA-256
  `fbb1bccc0e84795284f9fb1a3c0be9e6db516c3c4b8ae43ad2f856cf70948431`;
  `Origin`, `Theme` und `MaintenanceFrequencyCode` sind im Katalogmodell
  zeichengleich. `models/` enthält genau zwei aktive `.ili`-Modelle; der
  Vendor-Copy ist Referenz, kein drittes Modell.
- **Werkzeuge/Fixtures:** Die Tools werden gemäß `db/toolchain.json`
  heruntergeladen und SHA256-geprüft; der Test ruft die Fixture-Generierung
  (`fixture()`/`write()`) in `model_fixtures.py` nicht auf, sodass ein
  geänderter Sollwert die Negativdateien nicht still heilen kann. Der positive XTF deckt Standalone/Serie/Draft, mehrere Formate,
  prepared/withdrawn, Antrag/Genehmigung/Ablehnung/Direktvergabe/Widerruf,
  Gruppe sowie aktive/zukünftige/abgelaufene/widerrufene Grants ab.

Nicht Gegenstand und nicht behauptet: SQL-Mapping/ili2pg-Schema, Cayenne,
Transaktionen, Audit-Trigger, Service-Autorisierung, UI, öffentlicher
DB-Katalog, Dateiexistenz, Downloads und Legacy-Import (MA-B bis MA-E). Die
STACK-Änderung ist reine Dokumentation (Request/Work-Queue); PUBLIC ist
unverändert.

## Selbst ausgeführte Tests

Pflichtmenge des Handoffs: **M03, M04, M05, M06** (MA-A). Das eine
Produktkommando `python3 scripts/test_models.py` führt alle vier Nachweise in
einem Lauf; die vier PASS-Marker wurden aus demselben Lauf belegt. Ausgeführt
wurde es auf einem exakten `git archive HEAD`-Prüfstand von ADMIN, damit der
Kandidatenbaum unverändert bleibt.

| ID | Kommando (CWD) | Erwartet/Beobachtet | Inhalt | Beleg |
|---|---|---|---|---|
| M03 | `python3 scripts/test_models.py` (`.../output/scratch/admin-ma-a`) | 0 / 0 | ili2c 5.6.9 kompiliert beide Modelle nach IMD16; ilivalidator 1.15.0 validiert `valid-workflows.xtf` mit `--allObjectsAccessible --forceTypeValidation`; `M03 PASS` | `output/evidence/M03-evidence.txt` (Rohlogs `M03-ili2c-compile.log`, `M03-ilivalidator-valid-workflows.log`) |
| M04 | `python3 scripts/test_models.py` (dasselbe CWD) | 0 / 0 | IMD16-UUID-OIDs, AccessRequest/Decision/Grant nur mit `Catalog.Dataset`, keine Metadatenkopien auf Kindern, `accessLevel` nur auf Dataset, genau zwei aktive Modelle; `M04 PASS` | `output/evidence/M04-evidence.txt` (inkl. unabhängigem IMD-Parse) |
| M05 | `python3 scripts/test_models.py` (dasselbe CWD) | 0 / 0 | Fünf echte Negativ-XTF, jeweils mit der beabsichtigten semantischen Error-Zeile: Dataset.Constraint1, AccessGrant.Constraint1, AuthorityAssignment.Constraint2, GroupMembership.Constraint3, Distribution.Constraint2; kein Tool-Fehler; `M05 PASS` | `output/evidence/M05-evidence.txt` (fünf Rohlogs) |
| M06 | `python3 scripts/test_models.py` (dasselbe CWD) | 0 / 0 | Approval mit Request, DirectGrant ohne Request, Revoke-Referenz, Unicode/Zeilenumbrüche, vollständige Audit-Annotationen, Redaction nur auf `displayName`, identische Altvokabulare; `M06 PASS` | `output/evidence/M06-evidence.txt` |

Ergänzend geprüft (nicht als Pflicht-ID gezählt): Bindung/Hashes
(`binding-verification.txt`), vollständige IMD-Struktur
(`M04-independent-imd-check.txt`), Audit-/Vokabularzählung und
Fixture-Feldwerte (`M06-evidence.txt`). Der Testlauf war deterministisch
(deterministische UUIDv5-Fixtures); Rohbelege pro Compiler/Validatorlauf
liegen zusätzlich unter `output/scratch/admin-ma-a/.runtime/model-tests/`.

## Übernommene Nachweise

Keine. Dies ist das erste unabhängige MA-A-Review; es wurde kein früherer
MA-A-Beleg übernommen. M00–M02 wurden nicht erneut ausgeführt, weil MA-0
bereits unabhängig am Kandidaten `20261104T141858Z` abgenommen ist und MA-A
den MA-0-Runner/Compatibility-Spike sowie die Versionen nicht ändert. Die
Nichtausführung ist daher `NOT_REQUIRED`, nicht `NOT_EXECUTED`.

## Eigene Gegenprobe

- **Hypothese:** Die Modelle behaupten den Dataset-Rechteanker und die
  Entscheid-/Scope-Constraints nur; ein manipuliertes XTF, das einen Grant auf
  eine `DatasetIssue` zeigt, ohne Request genehmigt, eine Authority ohne
  Office-/Dataset-Scope anlegt oder einen Grant aus einem Revoke-Entscheid
  baut, würde trotzdem validieren.
- **Input/Manipulation:** `output/scratch/counterexample_ma_a.py` erzeugt vier
  mutierte Kopien von `valid-workflows.xtf` außerhalb aller Produktbäume:
  (1) `AccessGrantDataset.dataset` → `series-2025` (DatasetIssue),
  (2) `approval.request` entfernt,
  (3) `authority-publish.office` entfernt (kein Scope),
  (4) `grant.grantingDecision` → `revocation` (kind=revoke).
- **Kommando/CWD:** `python3 output/scratch/counterexample_ma_a.py`, CWD
  `output/scratch/admin-ma-a`.
- **Erwartung:** Alle vier Dateien werden vom echten Validator abgelehnt;
  Probe 1 als falsche Zielklasse für die Rolle, Proben 2–4 mit den exakten
  Mandatory-Constraint-Namen; kein Compiler-/Toolfehler als Ersatz.
- **Beobachtung:** **4/4 Erwartungen erfüllt.**
  - `grant-targets-issue`: Exit 1, `wrong class ... Catalog.DatasetIssue ...
    for role ... AccessGrantDataset.dataset`.
  - `approve-without-request`: Exit 1, `AccessDecision.Constraint2`.
  - `authority-no-scope`: Exit 1, `AuthorityAssignment.Constraint2`.
  - `grant-from-revoke`: Exit 1, `AccessGrant.Constraint3`.
  - Kein `Exception`, `compiler failed` oder `incompatible values`.
- **Schlussfolgerung:** Der Rechteanker ist strukturell typgeprüft, und die
  drei geprüften Geschäftsregeln werden tatsächlich vom Validator erzwungen,
  nicht nur von der Testdatei behauptet. Kein Defekt gefunden. Belege:
  `output/evidence/counterexample-evidence.txt`, `CE-*.log`.

## Findings

Keine BLOCKER-, MAJOR- oder MINOR-Produktbefunde.

Nicht blockierende Beobachtungen (kein Produktfehler, keine Nacharbeit):

- Die M04-Testprüfung auf fehlende Metadatenkopien zählt ausgewählte
  Dataset-Attributnamen auf den Kindern auf. Die unabhängige IMD-Prüfung hat
  zusätzlich die vollständigen Kind-Attributmengen und alle
  Assoziationszielpunkte untersucht; die Aussage ist damit unabhängig gedeckt.
- Die M05-Stringprüfung sucht den Constraint-Namen im Log. In allen fünf
  Fällen wurde verifiziert, dass der Name auf der tatsächlichen `Error:`-Zeile
  steht und nicht nur auf einer informativen `validate ...`-Zeile.
- Die ADMIN-README erwähnt im MA-0-Abschnitt noch, dass Fachmodelle erst nach
  dem MA-0-Gate folgen; der direkt folgende MA-A-Abschnitt dokumentiert die
  nun gelieferten Modelle. Das ist eine historische Formulierung, keine
  falsche Implementierungsbehauptung.

## Integrität und Grenzen

- **Produktstand:** `before.json` (Handoff-Zeitpunkt) gegen den Zustand nach
  diesem Review: 114 STACK-, 29 ADMIN- und 917 PUBLIC-Dateien verglichen,
  **0 geändert, 0 fehlend**; alle drei HEADs unverändert; alle drei
  `git status --porcelain` leer. Belege:
  `before.json`, `output/evidence/integrity-after.txt`.
- **Eigene Ressourcen:** `output/scratch/admin-ma-a` (exakter
  `git archive HEAD`-Prüfstand inkl. heruntergeladener Tools und Rohlogs),
  `output/scratch/counterexample_ma_a.py`,
  `output/scratch/counterexample-fixtures` (vier mutierte XTF + Logs) und
  `output/evidence`. Keine Container, Volumes, Ports oder Benutzerdienste
  verblieben; für MA-A wurde kein PostgreSQL gestartet.
- **Pflichtstatus:** M03–M06 sind alle `EXECUTED`/`PASS`; keine
  `NOT_EXECUTED`-Pflicht. M00–M02 und M07–M33 sind für dieses Gate
  `NOT_REQUIRED` und werden nicht als abgenommen behauptet.
- **Ehrliche Grenzen:** Dieses Urteil gilt nur für MA-A am genannten SHA-Satz.
  Es enthält keine Aussage über ili2pg-Schemaabbildung, Cayenne-PK/OID,
  Transaktionen/Rollback, Audit-Trigger/Coverage, Service-Autorisierung,
  OIDC/CSRF, öffentliche Views, Datei-Bytes, Gateway oder Downloads. Der
  Modellvalidator belegt keine automatische SQL-Constraint-Übersetzung; die
  Folgepflichten sind in `models/constraints.md` korrekt offen ausgewiesen.
  Keine Revisionssicherheits- oder Produktionszertifizierung wird behauptet.


Original review.json SHA256: `0706b077cee00cbb8e091bbea1e6efaecbf693f2c14e5bcaf1a6a0450d63a02a`.
ACCEPTED.json SHA256: `9fc9bd7fbd68926e53476b0f0d6677528ceabc15defe3d86953d89f741041bb5`.
