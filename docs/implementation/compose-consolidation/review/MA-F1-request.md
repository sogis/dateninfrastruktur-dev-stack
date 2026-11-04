# Reviewrequest MA-F1

- STACK base: `fc2ab199cd6aaea9141408f669aa5e2c27057ff8`
- ADMIN base: `6b6388b350f6de3d49abde076629a9c8d50a5ba0`
- PUBLIC base: `b1f20075be43eb4d0edf771ee1440ea0e30e1801`
- JENKINS base: `08931fa8254d096e2addcd3aee97bc1b753f087d`
- PLUGIN base: `579f3fd54432a977122afb186469fbb40d95322f`
- TOPICS base: `7d99ceec0e392a5f12b602c0840c4762c7213fba`

Umfang: kanonische Topologie, echte Admin-/Public-/Toolimages, explizite leere
DB-Einrichtung, private Origin-Credentials, vorhandener Fachvertrag,
DB-Katalog-/Jenkinsadapter, bestehende Supersetconnection erhalten.
Details und eigene Ergebnisse in F1_IMPLEMENTATION.md.

Selbst auszuführen aus STACK: `./scripts/test-consolidation.sh --phase MA-F1`.
Der Test baut und startet ausschliesslich die kanonische compose.yaml mit einem
frischen zufälligen Projekt, reservierten Ports, neuen Testcredentials/Volumes.
Er entfernt nur nach Prüfung seine eigenen Container/Volumes. Keine Nutzerdaten,
.env, alte Runtime, Inventurdatei oder Originalcontainer lesen/mutieren.
Das bereits lokal vorhandene unveränderte Jenkinsimage wird nur über Image-ID
referenziert, keine Nutzercredentials erforderlich. Java25/Testbrowser sind auf
diesem Rechner vorhanden; der Test setzt PLAYWRIGHT_SKIP_BROWSER_GC=1 und findet
SDKMAN Java25 selbst. Testfixtures sind ausdrücklich opt-in, nie Standardstart.

F04/F05/F06: zehn tatsächliche Defaultservices, ein PG16.10/PostGIS, drei DBs,
App-Konten positiv/eigener und negativ/fremder DBbereich, Audit-/Ownergrenzen,
frischer Build/Setup/Standardstart ohne Host-JAR oder Katalogbootstrap.
F07: realer OIDC-Token UND Browsercodeflow, privater S3 mit echter Verifikation,
Genehmigung und alle historischen Byteshashes; unberechtigter403/anonymer401.
F08: tatsächlicher Jenkinslogin/Anlieferungsredirect, bestehende verschlüsselte
Supersetconnection SELECT zu ClickHouse, echter Gradleadapter ohne Legacyreload.
Zusätzlich eine eigene sinnvolle Gegenprobe ausführen, z.B. geschütztes
bestehendes DBobjekt als anders berechtigter Appuser oder Ownershipmismatch vor
Mutationsaufruf; keine Produktdateien ändern.

Keine F0-PG-/Model-/MA-A–E-Vollsuiten erneut starten. F2 Migration, F3 öffentliche
Lifecyclewrapper/Retire und F4 endgültige Recreate-/Endkette folgen erst nach
Abnahme. Aktuell sind die früheren Wrapper noch historische Quellen; die neue
Topologie wird ausdrücklich via ComposeContext getestet. Das ist kein
abgeschlossener Nutzer-Cutover. Nur lokale Commits, kein Push in dieser Phase.
