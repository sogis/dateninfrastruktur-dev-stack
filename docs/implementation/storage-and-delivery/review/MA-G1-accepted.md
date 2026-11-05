# MA-G1 – unabhängig ABGENOMMEN und lokal verifiziert

Aktueller Abschlusslauf: `20261105T165335Z`, OpenCode `v2.2.5`,
`deepseek/deepseek-flash`, echter Runnerabschluss0, Produktintegrität unverändert.

| Bestandteil | SHA256 |
|---|---|
| Handoff | `3abb21dd1a64e3f197da1f1527189d13d437cd7585bb6a6c620466b8903d18b3` |
| Reviewreport | `ffa71e817d166949a96a20d02624e6e568d7bb2a4d5f1c2ad64e88d2892b5e2b` |
| Runner | `6545eb659b640712b30703268a77c12103180dab4ef28ba82e8aa52994d413ea` |

Akzeptierter Quell-SHA-Satz vor Beginn G2:

- STACK `3fce2fb1360a675a2e966824ec53404f25e0213a`
- ADMIN `e338727dcff18f2d1d3a803fc29e31417f99ac08`
- PUBLIC `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS `f32e40253cdd03a9327b66582aa2050557301239`
- PLUGIN `5535624776f3c1958192f45782f8724c08b31dd7`
- TOPICS `7c83135d69ada644e6e9a0352c3eb1308f798861`

Vollständiger erster Reviewlauf `20261105T160802Z`: G10–G19 selbst EXECUTED,
Modelle, nichtleerer Upgrade/Frischaufbau, wirklicher Garage-Rechte-/Bytevergleich,
Kopierunterbrechung und verlorenem Delete-Ack, Browser-PKCE/same-token revoke,
HEAD/Range/ETag, wiederholtes Setup und echte Neuerstellung. Eigene Gegenprobe:
Website-/Fremdkeydrift wird geschlossen behandelt, gebundene Keys bleiben gleich.

Aliasdelta `20261105T162915Z`: G14/G19 frisch, die acht unveränderten Checks
gebunden übernommen; key-lokaler Foundationnachweis mit realen GET-Hashes und
Alias-Identitätskonflikten. Anschliessend tatsächlicher lokaler Cutover;
[bereinigter lokaler Bericht](../LOCAL_STORAGE_CUTOVER.md).

Abschlussdelta: aktive einmalige Host-/Tool/API-/Imagepfade entfernt; nur
synthetische Regressionfixtures behalten. G14/G19 erneut frisch, andere acht
Checks einzeln an den wirklich ausgeführten Erstbelegen gebunden übernommen.
Eigene Gegenprobe: zusätzliche lokale/globale Aliase verhindern Retirement,
Bytes bleiben erhalten; fremder gleichnamiger Key-/Bucket bleibt unberührt.
Keine Findings. Der erste verwaiste Legacyimport-Test ist entfernt.

Lauf `20261105T164352Z` hatte zwar einen positiven Fachbericht, aber einen
protokollierten Provider-ECONNRESET und Prozesscode1: **kein Gate**, nichts
umgedeutet. Frische Sitzung am identischen Kandidaten bis zum gültigen obigen
Abschluss begleitet. Keine Provider-/Accountkonfiguration geändert.

Originalberichte/Handoffs/Events/Evidence unverändert privat unter
`STACK/.runtime/ingestion-review/MA-G1/`. Die lokale Übernahme wurde zusätzlich
am echten Nutzerzustand verifiziert, nicht aus synthetischen Tests abgeleitet.
G2 darf erst nach dem oben akzeptierten SHA-Satz beginnen; G2–G5 sind noch offen.
