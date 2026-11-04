# Quellen, Versionsprüfung und Einordnung

Stand der Spezifikation: **4. November 2026**. Quellen wurden zur Architektur-/APIprüfung gelesen. Daraus folgt keine hier durchgeführte Runtime-Abnahme. Tatsächliche lokale Stände und Releases in MA-0 erneut feststellen, nicht auf historische SHAs zurücksetzen.

## 1. Versionen

| Gegenstand | Beleg / Konsequenz |
|---|---|
| Spring Boot 4.1.2 | [Offizielle Veröffentlichung 23.10.2026](https://spring.io/blog/2026/10/23/spring-boot-4-1-2-available-now/), [Referenzdokumentation](https://docs.spring.io/spring-boot/). Bei Prüfung neueste stabile Linie; Preview4.2 ist kein Ersatz. |
| Cayenne 5.0-M3 | [Apache Downloads](https://cayenne.apache.org/download/), [Releasekatalog](https://release-catalog.apache.org/cayenne/index.html). Veröffentlicht, als Alpha/Milestone gekennzeichnet; nicht als GA ausgeben. |
| Cayenne M3 APIs | [UPGRADE.md am Tag5.0-M3](https://github.com/apache/cayenne/blob/5.0-M3/UPGRADE.md), [CayenneRuntime](https://github.com/apache/cayenne/blob/5.0-M3/cayenne/src/main/java/org/apache/cayenne/runtime/CayenneRuntime.java). Runtime/DataNodes/Tx/Sqllogger konkret prüfen. |

Keine dynamischen Versionen. Nach offiziellem Versionscheck genau pinnen; spätere Updates wieder kontrolliert testen. Cayenne ist der vom Nutzer gewünschte Milestone, die Bootvorgabe ist GA.

## 2. Bestehende Repos

- [Dev-Stack README](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/be32c293a5af0d3138395b64e2a73d40ec0f6542/README.md)
- [Compose](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/be32c293a5af0d3138395b64e2a73d40ec0f6542/compose.yaml)
- [APISIX-Routen](https://github.com/sogis/dateninfrastruktur-dev-stack/blob/be32c293a5af0d3138395b64e2a73d40ec0f6542/services/apisix/apisix.yaml)
- [Sodata Build](https://github.com/sogis/dateninfrastruktur-sodata/blob/7eff0b138c23524ac522231ce312d4c6659635dc/build.gradle)
- [Sodata Architektur](https://github.com/sogis/dateninfrastruktur-sodata/blob/7eff0b138c23524ac522231ce312d4c6659635dc/docs/architecture.md)
- [CatalogService](https://github.com/sogis/dateninfrastruktur-sodata/blob/7eff0b138c23524ac522231ce312d4c6659635dc/src/main/java/ch/so/agi/datenportal/catalog/service/CatalogService.java)
- [Themenrepo](https://github.com/sogis/dateninfrastruktur-themenrepo/tree/7d99ceec0e392a5f12b602c0840c4762c7213fba)

Diese Dateien zeigen die vorhandene Grundlage, nicht die neue Managementimplementierung. Admin ist als neues bzw. vom Nutzer inzwischen angelegtes lokales Repo zu behandeln. Vorhandene lokale Dateien bewahren.

## 3. INTERLIS, ili2pg und Audit

Bestehende fachliche Ausgangsmodelle (keine Pflicht, ihre Hierarchie beizubehalten):
- [Base](https://geo.so.ch/models/AGI/SO_AGI_DataCatalog_Base_20260529.ili)
- [Datasheet](https://geo.so.ch/models/AGI/SO_AGI_DataCatalog_Datasheet_20260523.ili)
- [PublishedCatalog](https://geo.so.ch/models/AGI/SO_AGI_DataCatalog_PublishedCatalog_20260602.ili)
- [Versionierter Modellbestand](https://github.com/sogis/sogis-interlis-repository/tree/c7594041083931f143d5cdcf3edd453f4d27e459/models/AGI)

Technik:
- [ili2db Dokumentation](https://github.com/claeis/ili2db/blob/ed9e7c20c9148b02d42e1846e2c5c555341aa257/docs/ili2db.rst): createMetaInfo, createStdCols, Mapping und CLIoptionen.
- [ili2pg Extensionstrategie](https://github.com/claeis/ili2db/blob/ed9e7c20c9148b02d42e1846e2c5c555341aa257/ili2pg/src/ch/ehi/ili2pg/PgCustomStrategy.java): setupPgExt nennt postgis und uuid-ossp.
- [PostgreSQL16 Trigger](https://www.postgresql.org/docs/16/plpgsql-trigger.html): OLD/NEW, AFTER-Audit, Rückgabeverhalten.
- [PostgreSQL16 Konfigurationsfunktionen](https://www.postgresql.org/docs/16/functions-admin.html): current_setting/set_config.
- [PostgreSQL16 CREATE FUNCTION](https://www.postgresql.org/docs/16/sql-createfunction.html): sichere SECURITY-DEFINER-Funktionen/search_path.
- [PostgreSQL Audit Trigger – Grenzen](https://wiki.postgresql.org/wiki/Audit_trigger): kein Schutz gegen privilegierten DBadministrator, keine SELECT-/DDL-Historie durch DML-Trigger.

Die vom Nutzer gelieferte `stdcols.sql` belegt das vorhandene Muster Defaults + BEFORE-UPDATE-Trigger mit session_user. Der neue Auftrag ergänzt vollständige Actor-/Änderungshistorie, er erklärt die bestehende Datei nicht zum bereits vollständigen Audit.

`di.audit`/`di.audit.redact` sind **neue Projektkonventionen**, keine dokumentierten ili2db-Features. Der externe Installer ist zu entwickeln; die Metaattribute allein erzeugen keine Trigger.

## 4. Gateway, Identität und Dateitransport

- [APISIX forward-auth Dokumentation](https://apisix.apache.org/docs/apisix/plugins/forward-auth/)
- [forward-auth Implementierung3.19.0](https://github.com/apache/apisix/blob/3.19.0/apisix/plugins/forward-auth.lua): ursprüngliche URI/Methode, Header, Status, Fail-Closed und Entfernen nicht gelieferter Upstreamheader.
- [openid-connect Implementierung3.19.0](https://github.com/apache/apisix/blob/3.19.0/apisix/plugins/openid-connect.lua): konkrete Optionen gegen eingebautes Schema prüfen.
- [Spring Security OAuth2 Resource Server JWT](https://docs.spring.io/spring-security/reference/servlet/oauth2/resource-server/jwt.html)
- [Spring Security CSRF](https://docs.spring.io/spring-security/reference/servlet/exploits/csrf.html)
- [Keycloak Hostname](https://www.keycloak.org/server/hostname): Browser-/Backchanneladressen nicht verwechseln.
- [rclone serve http](https://rclone.org/commands/rclone_serve_http/): interner technischer Origin, keine fachliche Autorisierungsinstanz.

Versionsunterschiede zwischen einer aktuell ausgelieferten Dokumentationsseite und der gepinnten3.19-Implementierung sind in MA-0/MA-E aufzulösen. Header-/Phasenverhalten stets mit dem realen Gateway testen.

## 5. Agentenworkflow

- [OpenCode2 CLI](https://opencode.ai/v2/docs/cli/commands/)
- [OpenCode2 Agenten](https://opencode.ai/v2/docs/agents/)
- [OpenCode2 Permissions](https://opencode.ai/v2/docs/permissions/)
- [DeepSeek 1017 Ankündigung](https://api-docs.deepseek.com/news/news261017/)

Die tatsächlich installierte2.x-Version und vorhandene Provider-/Modellliste sind massgeblich für Aufrufsyntax und Modellkennung. Kein erfundener `...-1017`-IDstring und kein stiller Aliaswechsel. Modellbindung im Runner belegen.

Die vom Nutzer beigefügten erfolgreichen Compilerprompts dienen als **methodische Referenz**: exakte Revisionen, isolierter Reviewer, eigene Gegenprobe, gezielte Nacharbeit. Compileraufgaben, Pythonentfernung und dortige Testmatrizen werden nicht übernommen.
