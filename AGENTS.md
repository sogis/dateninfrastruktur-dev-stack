# dateninfrastruktur-dev-stack

Im gemeinsamen Dateninfrastruktur-Workspace vor repoübergreifender Arbeit
`../AGENTS.md` ausdrücklich lesen und die Repo-Grenzen verifizieren. Bei einem
Einzelclone gelten die lokalen Regeln und Bedienhinweise im README. Für
repoübergreifende Aufträge zuerst den verifizierten Workspace bereitstellen.

Dieses Repo besitzt Composebetrieb, Gateway, Setup und produktübergreifende
Integrationstests. Die aktuellen Kommandos stehen in README.md und
docs/operations.md. Lokaler Betrieb und Tests nutzen den bestehenden
ComposeContext. Neue Testinstanzen brauchen eigene Namen, Ports, Volumes,
schreibbare Hostpfade und synthetische Zugangsdaten.

APISIX ruft die Java-Authorization-API über `forward-auth` auf. Interner Origin,
privater Garage-Bucket und die freigegebenen Dienste behalten ihre Grenzen.
Der gemeinsame PostgreSQL/PostGIS-Server bedient getrennte logische Datenbanken.
Explizites Setup und normales Up bleiben getrennt. Aktive Gateway-Deny-Regeln
schützen interne und stillgelegte Endpunkte.

Auftragsreviews laufen über den Workspace-Einstieg `workspace review` mit
gebundenem externem Auftrag und getrennten Testressourcen.
