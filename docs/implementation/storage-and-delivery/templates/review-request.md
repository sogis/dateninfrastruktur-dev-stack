# Reviewrequest MA-Gx – <konkreter Umfang>

- STACK base: `<vollständiger bereits existierender SHA>`
- ADMIN base: `<SHA>`
- PUBLIC base: `<SHA>`
- PLUGIN base: `<SHA>`
- JENKINS base: `<SHA>`
- TOPICS base: `<SHA>`

## Änderung und Risiken

| Geänderte Verantwortung | Gefährdeter Vertrag | Frisch auszuführende Checks | Übertragbare Belege / konkrete Begründung |
|---|---|---|---|
| <Datei/Methode> | <Axx/Specabschnitt> | <Gxx> | <Quelle/SHA/Reporthash oder keine> |

## Ausführung

Konkrete tatsächlich existierende Commands mit CWD, Voraussetzungen und Isolation. Keine Nutzer-ENV/Secrets. Nicht ausgeführte Tests offen nennen. Frühere eigene Implementierertests sind Hinweise, keine Reviewerabnahme.

## Ziele

Benutzer-/Betriebswirkung, nicht bloss Klassenliste. Bei G3 ausdrücklich zwischen Testprobe und echter CSVpipeline unterscheiden. Bei G5 Codeabnahme und lokale Umstellung trennen.

## Bekannte Grenzen

Keine pauschalen Scopeänderungen. Neue Abweichung mit Grund und Auswirkung. Head-SHAs werden erst nach dem Commit in den ignorierten Handoff eingetragen; diesen Request nicht selbstreferenziell machen.
