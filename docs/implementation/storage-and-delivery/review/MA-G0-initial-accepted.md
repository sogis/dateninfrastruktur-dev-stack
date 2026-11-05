# MA-G0 – unabhängige Erstabnahme

ABGENOMMEN durch OpenCode 2.2.5 / deepseek/deepseek-flash im isolierten Kandidaten
20261105T140634Z. G00–G04 alle frisch EXECUTED/PASS. Eigene Gegenprobe: echte
INTERLIS-UNIQUE-Verletzung wurde durch den CsvValidator abgewiesen.

STACK `c4164cb4f1364d963ee76719fef0f0d33d7acaf3`, ADMIN
`b4a8c2726da16373ee9e0fd02ecb715fba482612`; die weiteren vier SHAs stehen im
gebundenen Handoff. Keine BLOCKER/MAJOR, Quellen und Nutzerinstanz unverändert.

Report-SHA256: `b4cd33815e43f6f4e271bce84907d4e3d9468d4d543bdd9b7ca427c36833b576`.
Runner-SHA256: `f51573a203ecfbc1c0b18cb3c70da9e65f31b44aadebc3a5d90bbe20f7e7ec43`.
Handoff-SHA256: `b75a97bae25381b2a7c70ecd75e673179db52524391e8aff8308e9ab63d54465`.
Rohbelege: `.runtime/ingestion-review/MA-G0/20261105T140634Z/`.

Der anschliessende Dokumentationsdelta korrigiert eine rclone-Zählung:
Verzeichniseinträge sind keine S3-Objekte und deren Size=-1 keine Dateibytes.
G01/G02/G03 haben unveränderten Code/Binär-/Modellvertrag; der Delta-Request bindet
sie einzeln mit Report-/Handoff-/Runner-/Beleghash. G00/G04 werden neu geprüft.
Erst der neue aktuelle Kandidat erhält die endgültige MA-G0-Freigabe.
