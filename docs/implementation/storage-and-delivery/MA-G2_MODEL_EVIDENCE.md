# MA-G2 Modell-/Mappingbeleg (Codex, keine unabhängige Abnahme)

Vollständige Stockgenerierung und anschliessende echte Wiederholung an der
isolierten ili2pg-Referenz: 17 Auto-Klassen und DataMap bytegleich, keine
ignorierten Reverse-Relationship-Migrationsfehler. Die Ausgangsreferenz besitzt
54 Modell-/Assoziationsabbildungen und 266 rohe ili2pg-Spalten; 17 Fachtabellen
haben die kontrollierten Audit-/row_version-Ergänzungen.

| Artefakt | SHA256 |
|---|---|
| dateninfrastruktur-admin/models/SO_AGI_DataInfrastructure_Catalog_20261105.ili | `a4f2462ea94bfd347d32712a2b27217d82357f001b093a6d80f77ba03cf40aa4` |
| dateninfrastruktur-admin/models/SO_AGI_DataInfrastructure_Access_20261105.ili | `ff9833c33250544676c5f9d9af1376b70d5c4afe024802cce34c3e313ce47aa7` |
| dateninfrastruktur-admin/db/model-mapping.json | `f9d6a602ea63e316d60592e0a20e90633905de62c3f4dcd65277ec31857e1827` |
| dateninfrastruktur-admin/db/reference-ma-g2-metadata.json | `ca9044384e58e5f8694bec1ce899e48d2922b03f9bd2462348d8c5ee8b67e074` |
| dateninfrastruktur-admin/db/mapping-profile.json | `bd2aa6cfb4effb0f6c4e0bed5cf961448c730596ed533db7cb0a674c7a0c705d` |
| dateninfrastruktur-admin/src/main/resources/cayenne/management.map.xml | `627382da01d8ac150ff4dc34dbfac2092286c1a9a3258e964acd1baab339564f` |
| dateninfrastruktur-admin/db/persistence-contract.properties | `a7beb105097f00a64b8351cd0a8aa8b75a44eceb735767e0aa457a39e7f1e3f4` |
| dateninfrastruktur-themenrepo/contracts/population-v1.json | `60902b5af84464dea348bae2263e08435790c0a34476da926dfb426e4f0f286f` |
| dateninfrastruktur-themenrepo/contracts/compiled/population-v1.imd | `762a1328abadc226b36af5aa2a467e84272014a0e64b233ac3ca78b084643b80` |
| dateninfrastruktur-themenrepo/models/SO_Bevoelkerung_Altersstruktur_20261015.ili | `09438e64baae5701e3ecf0a4ca2b19419207c2223968d6416864f1fd61130a48` |

Privater Rohbeleg `.runtime/mag-g2-reference-2d05289e08/g2-byte-identical-generation.log`, SHA256
`58a2c08e59e90ab76fd601d2c721c7ca3a2b8e0c64d980facf9a048bb0c25529`.

Privater Rohbeleg `.runtime/mag-g2-reference-2d05289e08/g2-byte-identical-generation.json`, SHA256
`1c37fbff3ef17d7db1876744420b25b8f9218370ff98672308236083e8db8c9f`.

Kein Nachweis wurde aus der lokalen Nutzerdatenbank abgeleitet. Modellpaket,
Cayenne-Generierung und Rohreferenz verwenden eigene synthetische Ressourcen.
Das genehmigte TOPICS-Pilotmodell wurde mit dem echten festgelegten ili2c
erneut kompiliert; die vollständige IMD-Datei war bytegleich.
