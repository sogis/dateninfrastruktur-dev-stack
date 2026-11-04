# Fachmodellvertrag – Catalog und Access

Normativer Teil von [EXECUTION_PLAN.md](EXECUTION_PLAN.md). Dies ist ein konkreter **zu implementierender Entwurf**, keine bereits kompilierte ILI-Datei. Codex erstellt die Modelle, kompiliert sie und validiert die Fixtures tatsächlich. Die freien neuen Strukturen ersetzen nicht ungeprüft die Inhalte der bisherigen Metadaten.

## 1. Modellgrenzen und Identität

In `ADMIN/models/`:

- `SO_AGI_DataInfrastructure_Catalog_20261104.ili`, Topic `Catalog`.
- `SO_AGI_DataInfrastructure_Access_20261104.ili`, Topic `Access`, importiert Catalog und deklariert nötige Topic-Abhängigkeiten.

Kein zusätzliches Base-Modell ohne echte gemeinsame Verantwortung. Kein zweiter Live-Bestand Datasheet/PublishedCatalog. Fachlich eigenständige Objekte sind Klassen mit stabilen UUID-OIDs; INTERLIS-/ili2pg-Abbildung von `INTERLIS.UUIDOID` tatsächlich prüfen. Beziehungen als Assoziationen, nicht durch beliebige TEXT-IDs ersetzen.

`t_id` ist technischer DB-Schlüssel, nicht die fachliche Identität für URLs, Grants und Austausch. Ein stabiler alter `identifier` bleibt bei einer Migration erhalten; eine neue UUID wird einmalig zugeordnet. Benutzeridentität ist `(issuer, subject)`, nicht E-Mail oder Anzeigename. Beschreibungen, Hinweise, Methoden und Begründungen sind MTEXT. Eingeschränktes Markdown ist eine Darstellungskonvention, kein beliebiges HTML.

### 1.1 Ein einziger Rechteanker

```text
Dataset (kind: standalone | series; ganzer fachlicher Datensatz)
  └── DatasetIssue (fachliche Ausgabe, z.B. Jahr 2025)
       └── DataVersion (angenommener oder korrigierter Datenstand)
            └── Distribution (CSV, Parquet, XLSX ...)
```

**Konkretisierung dieses Auftrags:** Eine Datenreihe ist `Dataset(kind=series)`, nicht eine zweite von einem abstrakten Datensatz erbende physische Klasse. Der Rechteanker ist dadurch eindeutig. Der vorhandene GUI-Begriff DatasetSeries bleibt eine Darstellungsart. Ein Einzelangebot besitzt genau eine interne Ausgabe `issueKey=default`; diese wird nicht als künstliche Serie angezeigt.

Gemeinsame Metadaten werden nur auf Dataset gepflegt. Ausgaben besitzen keine Kopien von Beschreibung, Kontakt, Eigentümer, Themen oder AccessLevel. Eine optionale `note` ergänzt die gemeinsame Beschreibung, statt sie versteckt zu überschreiben. Wiederverwendbare Schemainformationen werden referenziert.

**Keine** Grants an Issue, DataVersion oder Distribution. Ein Datasetrecht umfasst alle angebotenen verfügbaren Versionen und Formate. `prepared`/`withdrawn` ist technische Verfügbarkeit, keine zusätzliche Benutzer-ACL. Wird ein Dataset öffentlich, werden alle seine zur Auslieferung freigegebenen Distributionen öffentlich; nicht still nur die aktuelle Version. Ein fachlich anders berechtigter Ausschnitt benötigt ein eigenes Dataset.

## 2. Domains und Katalogklassen

`1` = obligatorisch, `0..1` = optional. Jede Klasse hat zusätzlich die UUID-OID. SQL-Namen entstehen aus dem tatsächlichen ili2pg-Mapping, nicht aus der Schreibweise dieser Tabelle.

### 2.1 Domains

| Domain | Vertrag |
|---|---|
| AccessLevel | `open`, `restricted` |
| PublicationStatus | `draft`, `in_review`, `published`, `archived` |
| DatasetKind | `standalone`, `series` |
| Availability | `prepared`, `available`, `withdrawn` |
| DistributionFormat | `csv`, `xlsx`, `parquet`, `other` |
| Identifier | TEXT*255, stabil, katalogweit eindeutig |
| Sha256 | TEXT*64, genau 64 kleine Hexzeichen; passende Validator-/SQL-Regel ergänzen |
| SafeFileName | TEXT*128; ASCII `[A-Za-z0-9][A-Za-z0-9._-]*`, nicht `.` oder `..`, keine Pfade |
| EventTime | UTC-Zeitpunkt; INTERLIS-/SQL-Zeitzonenabbildung explizit dokumentieren |

Origin, Theme und MaintenanceFrequencyCode aus dem bestehenden Base-Modell übernehmen, soweit verwendet. Keine unangekündigte Umbenennung fachlicher Codes. Alte unklare Zugangscodes werden durch einen expliziten Importvertrag auf open/restricted überführt. DATE für fachliche Datumswerte, EventTime für Vorgänge und Gültigkeit.

### 2.2 Office

| Attribut | Typ/Kardinalität |
|---|---|
| identifier | 1 Identifier, UNIQUE |
| name | 1 TEXT*255 |
| abbreviation | 1 TEXT*32, UNIQUE |
| email | 0..1 URI, mailto-Konvention |
| phone | 0..1 TEXT*64 |
| website | 0..1 URI |
| active | 1 BOOLEAN |

Owner und Publisher sind unterschiedliche Office-Referenzen. Keine Löschkaskade historischer Verantwortung. Mitgliedschaft in einem Amt ist nicht automatisch eine Freigabebefugnis.

### 2.3 Dataset

| Attribut/Referenz | Typ/Kardinalität | Bedeutung |
|---|---|---|
| identifier | 1 Identifier, UNIQUE | stabiler Rechte-/Katalogbezug |
| kind | 1 DatasetKind | Einzelangebot oder Reihe |
| title | 1 TEXT*255 | gemeinsamer Titel |
| description | 1 MTEXT | gemeinsame Beschreibung |
| ownerOffice, publisherOffice | je 1 Office | Datenherr und Bereitsteller |
| contactName, contactUnit | je 0..1 TEXT*255 | Kontakt, keine Identitätsquelle |
| contactEmail | 1 URI | fachlicher Kontakt |
| contactPhone, contactUrl | 0..1 TEXT*64 / URI | optional |
| accessLevel | 1 AccessLevel | Zugriff auf Inhalte |
| publicationStatus | 1 PublicationStatus | Redaktion/Metadatensicht |
| origin, frequency | 0..1 entsprechende Domain | Herkunft, bei Reihe Rhythmus der Ausgaben |
| issued, modified | 0..1 / 1 DATE | fachliche Publikations-/Änderungsdaten |
| licenseUri | 0..1 URI | vorhandene/vereinbarte Nutzungsbedingungen, keine erfundene Lizenz |
| surveyMethod, furtherUses, auxiliaryData | je 0..1 MTEXT | gemeinsame Hinweise |
| dataAvailableFrom | 0..1 TEXT*255 | vorhandenen Inhalt bewahren |
| currentIssue | 0..1 DatasetIssue | muss zu diesem Dataset gehören |

Themen und Keywords als normalisierte Zuordnungen `DatasetTheme(dataset, theme)` und `DatasetKeyword(dataset, keyword)`, eindeutiges Paar pro Dataset. Auch diese physischen Tabellen müssen auditiert werden. Bei BAG-Abbildung muss der Installer die tatsächlichen Hilfstabellen berücksichtigen; die konkrete Modellierung ist im Mappingprofil festzuhalten.

Dataset.kind nach Publikation nicht still ändern. Reparenting von Issues nicht als gewöhnliches Metadatenupdate erlauben. currentIssue ist ein einzelner Verweis, kein Boolean, der widersprüchlich bei mehreren Ausgaben wahr sein kann.

### 2.4 DatasetIssue

| Attribut/Referenz | Typ/Kardinalität | Regel |
|---|---|---|
| dataset | 1 Dataset | einzige Elternzuordnung |
| issueKey | 1 TEXT*128 | UNIQUE je Dataset, standalone=`default` |
| label | 1 TEXT*255 | z.B. 2025 |
| publicationStatus | 1 PublicationStatus | keine Zugriffsstufe |
| referenceDate | 0..1 DATE | Stichtag |
| startDate, endDate | je 0..1 DATE | auch offenes Intervall zulässig |
| note | 0..1 MTEXT | zusätzliche Erläuterung, keine Serienbeschreibungskopie |
| issued, modified | 0..1 / 1 DATE | fachliche Daten |
| currentVersion | 0..1 DataVersion | Version derselben Ausgabe; available |

Stichtag XOR Intervall, Start ≤ Ende falls beide Grenzen vorhanden. Fehlende zeitliche Abdeckung bei nichtzeitlichem Einzelangebot zulässig; kein erfundenes Jahr. Titel der Ausgabe aus Dataset.title und label ableiten. Geänderte Datenstruktur wird durch DataSchema referenziert, nicht durch erneut kopierte Metadatenlisten.

### 2.5 DataSchema und AttributeDefinition

`DataSchema`: identifier UNIQUE, optional modelName TEXT*255, modelUri URI, modelVersion TEXT*100, modelSha256 Sha256, description MTEXT. Eine von verfügbaren Versionen verwendete Definition nicht nachträglich überschreiben; neue Definition = neues Objekt. Fehlende historische Modellhashes bleiben unbekannt.

`AttributeDefinition`: 1 DataSchema; name TEXT*255, dataType TEXT*255, ordinal positiver Integer, mandatory BOOLEAN; optionale description MTEXT, unit TEXT*255, codeList URI. UNIQUE `(schema,name)` und `(schema,ordinal)`. Mehrere Datenversionen können dieselbe Definition referenzieren. Kein vollständiger Attributeditor nötig, Import und Darstellung müssen die Informationen erhalten.

### 2.6 DataVersion

| Attribut/Referenz | Typ/Kardinalität |
|---|---|
| issue | 1 DatasetIssue |
| versionKey | 1 TEXT*128, UNIQUE je Issue; vorhandene Lieferungskennung, falls vorhanden |
| sequence | 1 positiver Integer, UNIQUE je Issue |
| schema | 0..1 DataSchema |
| availability | 1 Availability |
| acceptedAt | 0..1 EventTime, Pflicht für available |
| sourceSha256 | 0..1 Sha256 |
| objectCount, attributeCount | je 0..1 nichtnegativer Integer |
| validationStatus | 1 `unknown|success|fail` |
| validationAt, validationErrors | 0..1 EventTime / nichtnegativer Integer |
| validationReportKey | 0..1 TEXT*1024, intern |
| sourceReference | 0..1 TEXT*1024, Herkunft/Jobkennung ohne Credentials |

Keine Fachdatenzeilen in PostgreSQL duplizieren. DataVersion beschreibt angenommene Lieferungen und technische Metadaten, nicht den Inhalt aller ClickHouse-Tabellen. `fail` darf nicht available werden. Unbekannte Altprüfinformationen nicht in success umdeuten.

acceptedAt aus tatsächlich bekanntem Lieferungsvorgang; nicht Neuimportzeit als historische Prüfung behaupten. Nach available sind Identität, Schema, Hash und Lieferungsdaten unveränderlich; Rücknahme als withdrawn mit begründetem Vorgang. Korrektur erzeugt neue DataVersion. Keine systemübergreifende ACID-Transaktion mit ClickHouse/S3 behaupten.

### 2.7 Distribution

| Attribut/Referenz | Typ/Kardinalität |
|---|---|
| version | 1 DataVersion |
| format | 1 DistributionFormat |
| fileName | 1 SafeFileName |
| mediaType | 1 TEXT*255, kontrollierte Zuordnung |
| availability | 1 Availability |
| byteSize | 0..1 nichtnegative Ganzzahl; available verlangt belegten Wert |
| sha256 | 0..1 Sha256; available verlangt belegten Wert |
| storageProfile | 1 TEXT*80, logische technische Anbindung |
| objectKey | 1 TEXT*1024, interner unveränderlicher Schlüssel |
| legacyAccessUrl | 0..1 URI, ausschliesslich Migration, kein öffentlicher Fallback |

URL-Vertrag: `/downloads/<Distribution-UUID>/<fileName>`. Privater S3-Key: `downloads/<Distribution-UUID>/<fileName>`. Der interne Origin ist nur auf dieses Prefix ausgerichtet. Originalarchive/Validatorberichte/Audit liegen ausserhalb des auslieferbaren Prefixes. Keine ungeprüfte URL aus einem Benutzerformular abrufen.

UNIQUE `(storageProfile,objectKey)`. Nach Bereitstellung Dateiinhalt nicht unter derselben Distribution-ID austauschen. Dateiname allein ist keine Identität. SQL-Views exportieren weder objectKey noch Bucket-/Origininformationen. Nicht verfügbare Distributionen liefern keine Datei, auch wenn ein Grant existiert.

## 3. Access-Modell

### 3.1 Principal

Felder: kind `user|group|service`, issuer TEXT*1024, subject TEXT*255, displayName optional TEXT*255, active BOOLEAN, provisionedAt EventTime. UNIQUE `(issuer,subject)`.

Kein neuer kantonaler Benutzerstamm: externe Identität referenzieren. Keine Tokens/Passwörter. Lokale Gruppen verwenden eine eigene Namespace, z.B. `urn:so:agi:di:local-groups`, und werden nicht als AIO-Gruppen ausgegeben.

### 3.2 GroupMembership

1 group:Principal(kind=group), 1 member:Principal(kind=user|service), validFrom, optional validUntil, revokedAt, revokedBy, reason. Keine verschachtelten Gruppen im MVP. Intervalle halb offen. Änderung einer Mitgliedschaft kann mehrere Datenrechte beeinflussen und muss auditiert sein.

Gruppenpflege ist eine eigene administrative Befugnis, nicht automatisch Teil des Datenherrnrechts für ein Dataset. Für den MVP reicht eine explizite Bootstrap-/Operatorfunktion plus ein bestehendes Testteam; eine allgemeine IAM-Gruppenoberfläche ist nicht beauftragt.

### 3.3 AuthorityAssignment

Felder: principal (Person/Gruppe), **genau ein Scope** office oder dataset, capability `manage_metadata|publish|manage_access`, validFrom, optional validUntil/revokedAt, zuordnender Actor und Begründung.

Office-Scope gilt für Datasets mit dieser ownerOffice. Dataset-Scope nur dort. `manage_metadata` darf keine Grants oder AccessLevel ändern. `manage_access` darf Anträge entscheiden und Rechte direkt vergeben/entziehen. Veröffentlichung/Archivierung benötigt publish. Änderung open/restricted benötigt manage_access und publish; Demo-Claudia besitzt beides.

Verwalten ist nicht Lesen: AuthorityAssignment verleiht kein implizites READ_DATA. Plattformbootstrap ist eng begrenzter technischer Vorgang und kein pauschaler Download-Superuser. Keine neue zwingende Vieraugenregel erfinden: Selbstentscheid wäre nur bei tatsächlicher Zuständigkeit zulässig und sichtbar zu protokollieren; eine spätere organisatorische Einschränkung ist separate Policy. Die Demo nutzt zwei verschiedene Personen.

### 3.4 AccessRequest

Dataset (1), applicant:Principal(kind=user) (1), reason MTEXT (1), requestedAt (1), optional requestedValidUntil, status `pending|approved|denied|cancelled`.

Nur Antrag **für sich selbst**. applicant aus verifizierter Identität, nicht aus Formular. Bei open `NO_GRANT_REQUIRED`, keine künstliche Anfrage. Maximal ein pending Antrag je Dataset/Applicant; zusätzlicher partieller SQL-Unique-Index. Abgeschlossene Ablehnung erlaubt einen neuen begründeten Antrag. Antrag allein erteilt kein Recht. cancel nur eigener pending Antrag.

### 3.5 AccessDecision – unveränderlich

Dataset, beneficiary:Principal, actor:Principal, decidedAt, reason MTEXT, commandId UUID obligatorisch. kind `approve|deny|direct_grant|revoke`. Optional request und supersedes.

approve/deny verlangen passenden Request und stimmen in Dataset/Beneficiary überein. direct_grant braucht keinen Antrag. revoke wird vom betroffenen Grant als revocationDecision referenziert. UPDATE/DELETE eines bestehenden Entscheids verboten. Korrektur = neuer nachvollziehbarer Vorgang, kein stilles Umschreiben.

### 3.6 AccessGrant

Dataset (1), beneficiary:Principal (1), permission ausschliesslich `read_data`, grantingDecision (1; approve/direct_grant), validFrom (1), validUntil (optional), revokedAt und revocationDecision optional.

```text
wirksam zum Zeitpunkt t:
  begünstigter Principal aktiv
  UND validFrom <= t
  UND (validUntil fehlt ODER t < validUntil)
  UND revokedAt fehlt
```

revokedAt bedeutet sofortiger Widerruf, keine vorgemerkte zukünftige Sperre. validUntil muss nach validFrom liegen. Kein Statusflag active als zweite widersprüchliche Wahrheit. grantingDecision, Dataset, beneficiary und ursprüngliche Gültigkeit nicht nachträglich umdeuten. Verlängerung benötigt expliziten neuen Entscheid; Widerruf setzt nur seine einmaligen Enddaten. Ein beendeter Grant wird nicht reaktiviert.

Mehrere legitime Wege sind möglich: direkt plus Gruppe. Entzug eines einzelnen Grants entfernt nicht andere Freigaben. UI zeigt daher „dieser Grant widerrufen“ und die weiter bestehende effektive Berechtigung getrennt. Identische direkte Wiedervergabe liefert vorhandenen Grant/ALREADY_GRANTED, nicht unbemerkt eine Verlängerung.

### 3.7 CatalogAction

Kleine Klasse für fachliche Katalogaktionen: Dataset, actor, performedAt, actionCode `publish|archive|change_access_level|withdraw_version|withdraw_distribution`, reason MTEXT, commandId. Optionale Referenz auf betroffene untergeordnete Ressource ist **Ereigniskontext**, kein neues Rechteziel.

Normale Titel-/Beschreibungskorrekturen benötigen keine neue Event-Sourcing-Struktur; technische Auditzeilen mit actionCode/commandId reichen. Unveränderliche fachliche Entscheide und technische Auditdaten sind unterschiedliche Ebenen.

## 4. Veröffentlichung und Entwurfsgrenzen

Metadatenstatus und Dateiverfügbarkeit sind getrennt. published+restricted ist öffentlich auffindbar, aber nicht anonym herunterladbar. Drafts/in_review/archived werden im öffentlichen MVP-Katalog nicht ausgegeben; eine spätere Archivansicht ist nicht automatisch beauftragt.

Für bereits publizierte Metadaten bedeutet die Aktion **„Speichern und veröffentlichen“** eine unmittelbar sichtbare, autorisierte Änderung. Diese Etappe baut keine parallel bearbeitete geheime Entwurfsrevision eines bereits publizierten Objekts. Ein gewöhnlicher Entwurfseditor darf nicht nebenbei ein publiziertes Objekt ändern. Mehrstufige redaktionelle Revisionen sind ein gesonderter Ausbau.

Ein Dataset kann als Metadatenangebot published sein, obwohl noch keine auslieferbare Version existiert; dann keine Downloadaktion anzeigen. Ein verfügbare Distribution verlangt dagegen published Dataset/Issue und available DataVersion. Die Modell-/Service-/DB-Regeln unterscheiden das.

## 5. Technische Zusatzfelder, Audit und Invarianten

`--createStdCols` und zusätzliches `row_version BIGINT` bleiben technische SQL-Ergänzungen, nicht Pflichtbestandteil des INTERLIS-Fachmodells. Fachliche Entscheidungs-/Gültigkeitszeiten bleiben im Modell. row_version schützt paralleles Editieren, nicht die fachliche Datenhistorie.

Neue Metaattributkonvention, **keine eingebaute ili2db-Funktion**:

```ili
!!@ di.audit=full
CLASS Dataset =
  ...
END Dataset;
```

Zusätzlich `di.audit.redact=true` auf explizit nicht im Audit zu speichernden Attributen. Keine unkontrollierte `audit=none`-Ausnahme für sicherheitsrelevante Klassen. Zugehörige Tabellen von Assoziationen/Collections erben die Auditpflicht. Externer Installer und Trigger sind in SPEC_PERSISTENCE_AUDIT beschrieben.

`models/constraints.md` ordnet Regeln tatsächlich ausführbaren Stellen zu:

| Regel | Primäre Durchsetzung |
|---|---|
| Pflichtfelder, Domains, Kardinalitäten | ILI/Validator plus generierte NOT NULL/FKs |
| OIDs, Identifikatoren, Zuordnungspaare | ILI UNIQUE soweit möglich plus DB Unique |
| genau ein Authority-Scope, Zeitintervalle | Modellconstraint + SQL CHECK |
| current-Zeiger gehört zum Elternobjekt | Service + kontrollierter DB-Constrainttrigger |
| Decisions/Grants nicht umdeuten | Fachservice + DB-Schutztrigger/Rechte |
| ein pending Request | partieller Unique-Index + idempotenter Service |
| gültiger Akteur/Zuständigkeit | verifizierter Login, Serviceprüfung innerhalb Schreibtransaktion |
| Datei erst nach tatsächlich bestätigter Ablage available | Registrierungsservice, nicht bloss Existenz eines Keystrings |
| Auditabdeckung aller physischen Fachtabellen | Installer + Coverage-Prüfung in pg_catalog |

Nicht behaupten, ili2pg übersetze automatisch jeden INTERLIS-Constraint in DDL. Tatsächliches Schema prüfen, zusätzliche Regeln versioniert ergänzen.

## 6. Legacy-Übernahme

Bisherige Modelle liefern Eingangsmetadaten, keine zweite laufende Änderungsquelle. Einmaliger Java-Import mit `--dry-run` und Konfliktbericht, danach explizites apply mit technischer Actoridentität.

- Tatsächliche lokale Datei/Hash und Modellquelle dokumentieren. Kein erfundener Download.
- Identifier erhalten; UUID-Mapping einmal persistieren. Gleicher Import erzeugt keine Duplikate und überschreibt spätere Adminänderungen nicht.
- open→open; übrige bekannte alte Zugangscodes→restricted, Warnung. Unbekannte Codes stoppen, nicht open raten.
- Serienmaterialisierungen normalisieren; identische Offices/Themen/Schemadefinitionen zusammenführen.
- Widersprüche zwischen Serien- und Ausgabemetadaten nicht per first-wins oder silent-null beseitigen. Konfliktbericht; betroffenen Apply nicht ausführen. Eine bewusste Migrationsregel kann im Plan ergänzt werden.
- Keine Copy-Paste-Beschreibung als künstliche issue.note. Legitime zusätzliche Erläuterungen erhalten.
- Alte Download-URL zunächst nur Migrationsreferenz; Datei erst available nach Übernahme/Prüfung im eigenen privaten Speicherweg.
- Fehlende Prüf-/Lieferungswerte unbekannt lassen, keine Werte aus Importzeit oder Modellname erfinden.
- Vollständiger dry-run des verfügbaren Katalogs und reale Migration repräsentativer Standalone-/Serienfälle. Ungeklärte Datenkonflikte transparent, keine global geschwächte Modellregel.

## 7. Minimale Modelldaten für Tests

Deterministische Demo-UUIDs; keine echten vertraulichen Daten. Offices AFIN/AGI und fremdes Amt; Anna/Ben/Claudia sowie unzuständige Dora; technische Bootstrap-/Importidentität. Ein open Dataset, ein restricted Series-Dataset mit zwei Ausgaben und mehreren verfügbaren Ständen, ein Draft. Mehrere Formate, prepared und withdrawn Datei. Direkter Grant und lokale Gruppe; aktiv, zukünftig, abgelaufen und widerrufen. Anfrage→Genehmigung, Ablehnung, Direktvergabe und Entzug.

Wenige parametrisierte Fälle statt vollständigem Kreuzprodukt. Modellvalidierung muss echte fachliche Positiv-/Negativaussagen prüfen, nicht bloss Compiler-Exit 0.
