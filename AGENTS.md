# dateninfrastruktur-dev-stack

Bei repoübergreifender Arbeit auch die Workspace-AGENTS lesen und die
Gitgrenzen prüfen. Bestehende Arbeit schützen. Docker Compose, den vorhandenen
ComposeContext und Python 3.9 verwenden. Obsolete Pfade löschen und auf
spekulative Abstraktionen, Kompatibilitätsschichten und eigene Orchestrierung
oder Reviewinfrastruktur verzichten.

Der Stack besitzt Betrieb, Gateway, Setup und produktübergreifende Tests.
Setup explizit ausführen. Der Normalstart nutzt bestehende Daten und führt
keine Migration aus. Tests brauchen eigene Projektnamen, Ports, Volumes,
schreibbare Hostpfade und synthetische Zugangsdaten. Fremde Ressourcen
dürfen weder verändert noch entfernt werden.

Der gemeinsame PostgreSQL/PostGIS-Server bedient getrennte logische Datenbanken.
APISIX ruft die Admin-Authorization-API über `forward-auth` auf. Aktive
Gateway-Deny-Regeln, internen Origin und privaten Garage-Bucket erhalten.

Vor grösseren Änderungen `.agents/skills/simplify-change/SKILL.md` anwenden.
Vor PR-Abschluss unabhängig mit `.agents/skills/review-change/SKILL.md`
prüfen. Bestehende Integrationstests anhand der betroffenen Verträge auswählen.
