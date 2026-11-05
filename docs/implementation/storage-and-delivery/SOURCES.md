# Quellen, Ausgangsstand und Abgrenzung

**Stand der Spezifikation: 05.11.2026.** Die Architektur-/Klassen-/APIverträge in diesem Paket sind neue, aus der Diskussion abgeleitete Sollvorgaben. Sie sind nicht aus einem Frameworkhandbuch übernommen und nicht bereits implementiert. Repoquellen wurden über den GitHub-Zugriff gelesen; keine lokale Nutzerlaufzeit wurde verändert oder in dieser Sitzung getestet.

## 1. Belegter MA-F-Ausgangssatz

Diese SHAs stammen aus dem vorliegenden MA-F-Abschlussstand. Codex muss in G0 die tatsächlichen lokalen Heads, Branches und uncommittierte Arbeit neu feststellen; nicht blind auf diese SHAs zurücksetzen.

| Kürzel | Repository | Belegter SHA |
|---|---|---|
| STACK | sogis/dateninfrastruktur-dev-stack | `744a771bc16dcc42ad53a03fea17613ab294831a` |
| ADMIN | sogis/dateninfrastruktur-admin | `6009fb04063f16fcdb2ea6b3d9153e9553c9e4f1` |
| PUBLIC | sogis/dateninfrastruktur-sodata | `b1f20075be43eb4d0edf771ee1440ea0e30e1801` |
| PLUGIN | sogis/dateninfrastruktur-jenkins-gretl-plugin | `579f3fd54432a977122afb186469fbb40d95322f` |
| JENKINS | sogis/dateninfrastruktur-jenkins-dev | `08931fa8254d096e2addcd3aee97bc1b753f087d` |
| TOPICS | sogis/dateninfrastruktur-themenrepo | `6b0b635f066dc8de5000e3e549b983fb772dfb33` |

Der aktuelle STACK-Branch wurde bei der Erstellung erneut mit diesem SHA gelesen. Aktuelle Einzeldateien wurden zusätzlich gelesen; das ist kein eigener End-to-End-Test. Unbekannte lokale S2-Implementierungen oder andere Branches sind ausdrücklich in G0 zu prüfen.

## 2. Repositorybelege

### R1 – Konsolidierter Stack

`https://github.com/sogis/dateninfrastruktur-dev-stack/tree/744a771bc16dcc42ad53a03fea17613ab294831a`

Relevante Dateien: `compose.yaml`, `services/garage/setup-compose.py`, `scripts/compose_runtime.py`, `services/apisix/routes.template.json`, `services/jenkins/jenkins-stack.yaml`, `scripts/compose_operator.py`, `docs/operations.md`, `docs/implementation/compose-consolidation/LOCAL_CUTOVER.md`.

Belegt: gemeinsame Compose-Laufzeit, vorhandene Storage-/Origin-/Gatewaykonfiguration und noch alte Bucket-/Credentialbezüge. Die neue Single-Bucket-Bereinigung ist eine neue Anforderung, nicht bereits durch MA-F abgenommen.

### R2 – Modelle, Fachrechte, Audit und Registrierung

`https://github.com/sogis/dateninfrastruktur-admin/tree/6009fb04063f16fcdb2ea6b3d9153e9553c9e4f1`

Relevante Dateien: `models/SO_AGI_DataInfrastructure_Catalog_20261104.ili`, `models/SO_AGI_DataInfrastructure_Access_20261104.ili`, `access/AuthorityService.java`, `catalog/DeliveryRegistrationService.java`, `catalog/RclonePrivateObjectVerifier.java`, `docs/schema-lifecycle.md` unter den bestehenden Pfaden.

Belegt: vorhandene Capabilities, Gruppen-/Office-/Datasetbezüge, StorageProfile/LegacyURL und die Registrierung einer verfügbaren Version mit zunächst unbekanntem Validierungsstatus. Daraus folgt die gezielte Neufassung des CSV-Abschlussvertrags; der Sourcecode allein garantiert noch keinen neuen Anlieferungsprozess.

### R3 – Bisheriges Jenkins-Plugin

`https://github.com/sogis/dateninfrastruktur-jenkins-gretl-plugin/tree/579f3fd54432a977122afb186469fbb40d95322f`

Relevante Klassen unter `src/main/java/ch/so/agi/jenkins/gretldatenportal/`: `GretlDatenportalRootAction`, `GretlDatenportalJobGenerator`, `GretlDatenportalAuthorizationSynchronizer`, `PermissionConfiguration`, `TeamDirectory`, `StartFormValidator`. Weiter `README.md` und `pom.xml`.

Belegt: Organisationsjobs, Teams/YAML, projectMatrix und separate Prüfung im Formular. Daraus wird nicht ohne eigenen Test eine konkrete ausnutzbare Sicherheitslücke behauptet; das neue Design ersetzt diese Berechtigungsarchitektur absichtlich.

### R4 – Themenrepo / gemeinsamer alter Ablauf

`https://github.com/sogis/dateninfrastruktur-themenrepo/tree/6b0b635f066dc8de5000e3e549b983fb772dfb33`

Relevant: `shared/Jenkinsfile`, `shared/gretl-datenportal-teams.yaml`, `shared/gretl-datenportal-defaults.yaml`, Organisations-YAML, `shared/gradle/datenportal-publication.gradle` und vorhandene Datenmodelle/Validierungs-/Exportfunktionen.

Belegt: gemeinsamer Verarbeitungsablauf, alter Metadaten-/Manifestpublikationsvertrag und dessen ausdrückliche Sperre im DB-Katalogmodus. Geeignete Datenverarbeitungsfunktionen sind wiederverwendbar, alte Katalog-/Autorisierungsverträge nicht.

### R5 – Jenkinsimage

`https://github.com/sogis/dateninfrastruktur-jenkins-dev/tree/08931fa8254d096e2addcd3aee97bc1b753f087d`

Vorhandene Image-/HPI-/GRETL-/Offline-Toolchain ist Ausgangsbasis. Der neue OIDC-/Pluginvertrag benötigt einen echten neuen Imagebuild; keine implizite Verwendung eines früheren `:local`-Images.

### R6 – GRETL CsvValidator

`https://github.com/sogis/gretl/blob/main/gretl/src/main/java/ch/so/agi/gretl/tasks/CsvValidator.java`

Der gelesene Task bietet Header-, Quote-/Separator- und Encodingparameter. Er kann bei fehlender Eingabedateiliste ohne Validierung zurückkehren; der neue Wrapper muss deshalb Existenz, genau erwartete Inputs und tatsächlich ausgeführte erfolgreiche Validierung beweisen. Konkrete ausgeführte GRETLversion und Implstand in G0 pinnen.

### R7 – Vorhandener autonomer Reviewrunner

`https://github.com/sogis/dateninfrastruktur-dev-stack/blob/744a771bc16dcc42ad53a03fea17613ab294831a/scripts/management/review-phase.py`

Begleitend `review_gate.py`, `reviewer-agent.md`, `test_review_gate.py`. Belegt: isolierte Checkouts, vorhandene Desktop-2.x-CLI, Modellbindung, tatsächliche Tools/Session und Delta-Checks. Nur um MA-G-Routing/Dateihashes/Checks erweitern.

## 3. Technische Primärquellen

### S1 – Garage S3-Kompatibilität / Administration

`https://garagehq.deuxfleurs.fr/documentation/reference-manual/s3-compatibility/`  
`https://garagehq.deuxfleurs.fr/documentation/reference-manual/cli/`

Garage verwendet ein eigenes Rechteverfahren. Keine volle AWS-IAM-Prefix-/ACL-/WORM-Semantik unterstellen. Die Dokumentation selbst verlangt bei ernsthaften Entscheidungen eigene Verhaltenstests. Die Spez verlangt deshalb echte Positiv-/Negativproben auf dem gepinnten Image, nicht bloss auf Dokumentationsannahmen.

### S2 – Jenkins OpenID Connect Plugin

`https://plugins.jenkins.io/oic-auth/`  
`https://github.com/jenkinsci/oic-auth-plugin/blob/master/docs/configuration/README.md`  
`https://javadoc.jenkins.io/plugin/oic-auth/org/jenkinsci/plugins/oic/OicCredentials.html`

Belegt sind OIDC-Anbindung, konfigurierbarer Benutzerclaim und ein Tokenzugriffsmodell. Dokumentations-/Suchstände zeigten unterschiedliche Pluginversionen; deshalb keine ungesicherte „aktuellste“ Version in der Spez pinnen. G0 prüft die konkret kompatible veröffentlichte Version und ihren Code.

### S3 – Jenkins Permissions / Remote Access

`https://www.jenkins.io/doc/book/security/access-control/permissions/`  
`https://www.jenkins.io/doc/book/using/remote-access-api/`

Jenkins-Jobrechte sind keine fachliche Dataset-/Parameterautorisierung. Der zentrale Lieferauftrag und die Prüfpunkte sind eine neue Architekturvorgabe, kein natives Jenkinsfeature.

### S4 – Jenkins Build Authorization

`https://www.jenkins.io/doc/book/security/build-authorization/`

Builds laufen ohne entsprechende Konfiguration standardmässig mit SYSTEM-Authorisierung. Das ist nicht identisch mit der Identität der anliefernden Person. Der neue Job muss seine technische Ausführungsidentität nachweislich begrenzen; ein spezieller Authenticator im eigenen Plugin ist vorzuziehen gegenüber unbedachter Einführung einer weiteren Abhängigkeit.

### S5 – Jenkins CSRF / Credentials

`https://www.jenkins.io/doc/book/security/csrf-protection/`  
`https://www.jenkins.io/doc/book/security/credentials/`

Mutierende eigene Pluginendpunkte benötigen serverseitige Rechte-/CSRFprüfungen. Credentialmaskierung allein ist kein Schutz vor absichtlich auslesbaren Artefakten oder CPS-State. Diese Grenzen sind mit tatsächlichen Tokenwerten nur intern zu prüfen; Belege müssen bereinigt sein.

### S6 – ClickHouse EXCHANGE

`https://clickhouse.com/docs/reference/statements/exchange`

Austauschoperationen haben Enginevoraussetzungen. Nicht als verteilte Transaktion mit PG oder S3 auslegen. Die konkrete gewählte Snapshot-/Sichtenumstellung am bestehenden ClickHouse prüfen.

### S7 – ClickHouse CREATE VIEW

`https://clickhouse.com/docs/reference/statements/create/view`

SQLsichten sind eine mögliche abgeleitete aktuelle Datenprojektion. Berechtigungs- und Aktualisierungsverhalten werden am gepinnten Server nachgewiesen; die Spez behauptet keine atomare Mehrsystempublikation.

## 4. Abgrenzung

Eigene Designentscheidungen dieses Pakets: konkrete interne API, Submission-/Executionzustände, zwei Liefercapabilities, kleiner Autorisierungs-Guard, Idempotenz-/Fencevertrag, ein Job, Snapshotsemantik und Testabnahme. Quellen belegen benötigte Funktionen/Grenzen, nicht die gesamte neue Architektur.

Weder die Dokumente noch eine grüne statische Paketprüfung sind ein fachlicher Test, ein unabhängiger Codereview oder eine Compliance-/Produktionszertifizierung. Dafür gelten die konkreten MA-G-Gates.
