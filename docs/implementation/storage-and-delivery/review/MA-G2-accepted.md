# MA-G2 – ABGENOMMEN

Unabhängige Sitzung `20261105T192845Z`, OpenCode `v2.2.5`,
`deepseek/deepseek-flash` (angeforderter DeepSeek Flash 1017 über bestehenden
Zugang). Prozess Exit 0; tatsächlicher Provider verifiziert; Quell- und
Kandidatenbäume unverändert. Alle G20–G29 wurden frisch ausgeführt.

| Repository | Abgenommener Commit |
|---|---|
| STACK | `4de934b9a82ac4b0aa3f6e92f8db44b3a31e4194` |
| ADMIN | `cb4074d7c76d8a9b93e0d6a614369c4fb9ed85ad` |
| PUBLIC | `d066314ad81750d3c2a16a1ade9f626aa4732521` |
| JENKINS | `f32e40253cdd03a9327b66582aa2050557301239` |
| PLUGIN | `5535624776f3c1958192f45782f8724c08b31dd7` |
| TOPICS | `5e696006754cc7389ef002a7b24d6b90df3de80a` |

Handoff SHA256 `ccf723ebe8a06a995881de5db0937d1fd85e90c98aeb24fd898b979714398bcd`.
Report SHA256 `a0a604bdf4a29bbdb41d06788f1a9d2a56befd511bdd46058c0b7d986cec751a`.
Runner SHA256 `0887fdca60ac05f822c39983d9d567f8c362cda65630948f33f874d33ff8d8e3`.
Rohbelege privat in `.runtime/ingestion-review/MA-G2/20261105T192845Z/`.

Nachgewiesen: echtes INTERLIS/ili2pg-Schema, befüllter G1→G2-Upgrade und
Roundtrip bei unveränderten Altwerten, privaten Referenzen und Auditzeilen;
frische DB ohne Fachseed; Scope/Delegation, signierte Benutzer-/Service-HTTP-
Profile, geordnete Aufträge und Claims, Widerrufskonkurrenz, Rollback und
bereinigter Pool. Die eigene Gegenprobe führte 13 tatsächliche verweigerte
SQL-Änderungs-/Zugriffsversuche mit positiven Kontrollabfragen aus. Keine
Fachannahme via manuellen Altoperator. G2 verwendet synthetische
Runnerattestierungen; echte CSV-/Storage-/CH-Verarbeitung bleibt G4.

Nicht blockierende Hinweise: historische ADMIN-Downloaddoku nennt noch den
entfernten Operator; bei deaktivierter Autopublikation soll die Bedienung den
pausierten Lieferpfad ausdrücklich erklären. Kein offener Pflichtcheck.

Die lokale Nutzerinstanz ist weiterhin auf dem abgenommenen G1-Laufzeitstand.
Diese Abnahme öffnet MA-G3, nicht MA-G4/MA-G5.
