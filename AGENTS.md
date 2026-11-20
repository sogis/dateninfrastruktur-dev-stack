# dateninfrastruktur-dev-stack

Bei repoübergreifender Arbeit auch die Workspace-AGENTS lesen und die
Gitgrenzen prüfen. Bestehende Arbeit schützen. Build, Start, Status, Logs,
Stopp und Down direkt mit Docker Compose ausführen. Compose verwaltet
Netzwerke und projektbezogene Named Volumes. Python-Skripte bleiben mit
3.9 kompatibel.
Obsolete Pfade löschen. Explizites Setup und Admin-Development direkt
halten und bestehende Werkzeuge nutzen. Keine allgemeine Betriebsengine,
generischen Manager, Lifecycle-State-Machine oder neue Reviewinfrastruktur.

Der Stack besitzt Betrieb, Gateway, Setup und produktübergreifende Tests.
Setup explizit ausführen. Der Normalstart nutzt bestehende Daten und führt
keine Migration aus. Tests brauchen eigene Projektnamen, Ports, Volumes,
schreibbare Hostpfade und synthetische Zugangsdaten. Volumes nur beim
bewussten Reset oder bei der Bereinigung des eigens erzeugten Testprojekts
löschen. Fremde Ressourcen schützen.

Der gemeinsame PostgreSQL/PostGIS-Server bedient getrennte logische Datenbanken.
APISIX ruft die Admin-Authorization-API über `forward-auth` auf. Aktive
Gateway-Deny-Regeln, internen Origin und privaten Garage-Bucket erhalten.

Die CSV-Anlieferung startet den festen GRETL-6-Job aus dem Jenkins-Image.
Die Integration mit der veröffentlichten Maven-Distribution und einer
eigenen Compose-Instanz prüfen.

Vor grösseren Änderungen `.agents/skills/simplify-change/SKILL.md` anwenden.
Vor PR-Abschluss unabhängig mit `.agents/skills/review-change/SKILL.md`
prüfen. Bestehende Integrationstests anhand der betroffenen Verträge auswählen.
