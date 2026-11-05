# Reviewrequest MA-G1 – privater Einbucketbetrieb und bekannte Bestandsübernahme

- STACK base: `aa39924ef68084e379dc7c8311835a207fe91e8c`
- ADMIN base: `92e1fddb4b3af166a89ab065c4a282d49b9a6895`
- PUBLIC base: `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS base: `f32e40253cdd03a9327b66582aa2050557301239`
- PLUGIN base: `5535624776f3c1958192f45782f8724c08b31dd7`
- TOPICS base: `7c83135d69ada644e6e9a0352c3eb1308f798861`

## Delta nach unabhängigem ABGENOMMEN

Vorheriger akzeptierter Lauf: `20261105T160802Z`.
Report-SHA256: `4d71d770e172fd5e82930d0f85070dfca33f27abbcb6b09755477a2e4e1ec62c`.

Nach der Codeabnahme hat die **lesende** lokale Planvorbereitung korrekt vor
jeder Mutation gestoppt: Der eindeutig bekannte Foundation-Smoke-Bucket hat
keinen globalen Alias. Er wurde durch den ursprünglichen S3-CreateBucket als
key-lokaler Alias erzeugt. Es gab keine Löschung, kein Schema-Upgrade und kein
Stoppen eines Nutzerdienstes. Der Download-Vorhervergleich ist erfolgreich.

Änderung ausschliesslich am optionalen, einmaligen Foundation-Fixtureschritt:
Key-lokalen Alias über exakt den inventarisierten Defaultkey auflösen, dann
vollständige Bucket-ID und exklusive Aliaszuordnung binden. Keine globale
Namensfallbacksuche. Read-back-SHA/Grösse und genau ein bekanntes Objekt bleiben
Pflicht. Beim Retire ausschliesslich die gebundene ID; unbekannte Objekte und
Alias-Neuzuordnung verursachen Fehler ohne Löschung. Nach verlorener Delete-
Bestätigung ist eine fehlende alte ID nur lesend prüfbar.

Frisch auszuführen: **G14, G19** mit

```sh
python3 scripts/test_ingestion_foundation_g1.py
```

Der echte Garage-Test prüft key-lokale Auflösung, tatsächliche Objektbytes,
einen separaten gleichnamigen globalen Bucket als unberührte Kontrolle,
unbekanntes Objekt vor Retirement, erfolgreichen und wiederholten Abschluss,
sowie eine Aliasneuzuordnung mit weiterhin erhaltenen neuen Bytes.
Mindestens eine eigene relevante Gegenprobe wirklich ausführen.

G10–G13/G15–G18 aus dem gebundenen akzeptierten Bericht einzeln übernehmen,
sofern der Reviewer die Nichtbetroffenheit bestätigt: Provisioner, Normalsetup,
allgemeine private Copy-/Purge-/Resumezustände, INTERLIS/SQL/ORM/Fingerprint,
Browser-/Grant-/Downloadkette, Container-Recreate und Credentials sind unverändert.
Der bestehende allgemeine Operator-Test ohne Foundationquelle ist unverändert;
keine erneute komplette Browser-/Schema-/Cutoversuite allein für den lokalen Alias.

Zusätzlich nur README-Korrektur zum aktiven Auftrag/entfernten Legacyimport und
Entfernung des vom Reviewer benannten verwaisten Tests `test_operator_contract.py`.
Dieser hatte keine aktive Harness-/Gradle-Referenz und prüfte ausschliesslich das
bereits entfernte Importkommando. Ersatz ist in der Retirementmatrix genannt.

Der tatsächliche lokale Cutover bleibt bis zur Annahme dieses Deltas geschlossen.
Der eingefrorene vorherige G1-Stand und alle ursprünglichen Belege bleiben erhalten.
