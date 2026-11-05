# MA-F Arbeitsstand

| Phase | Status | Gate |
|---|---|---|
| MA-F0 | ABGENOMMEN (20261104T203347Z) | F01–F03; Bestand/Plan/native PG-/Reviewprobe |
| MA-F1 | ABGENOMMEN (20261104T210539Z) | F04–F08; frischer kanonischer Stack, echte Fachkette |
| MA-F2 | ABGENOMMEN (20261104T234324Z) | F09/F10/F12 gebundene unveränderte Eigenläufe; F11/F13 frisch im Delta, eigene Gegenprobe |
| MA-F3 | ABGENOMMEN (20261105T005356Z) | ein Lifecycle, Recreate, sicherer Retire/Rückfall; danach lokaler Cutover |
| MA-F4 | ABGENOMMEN (20261105T013710Z) | F17–F20 frisch, eigene Fail-Closed-/Cache-Gegenprobe; reales Ziel ebenfalls geprüft |

Livezustand: **LOCAL_CUTOVER_VERIFIED · RETIRED**. Ein Composeprojekt, zehn
gesunde Dauer-Services, ein nativer PG16.10/PostGIS3.5.2 mit drei Datenbanken.
20 verifizierte Altcontainer entfernt; alle zehn Originalvolumes erhalten;
zwölf fremde Container unverändert. Fachpfad, bestehende Dateien/Rechte,
Auditpräfix und tatsächlicher Recreate am übernommenen Ziel bestanden.
Details und private Backupreferenzen: [LOCAL_CUTOVER.md](LOCAL_CUTOVER.md).

Die funktionalen MA-0–E-Abnahmen bleiben historisch; sie beweisen keine MA-F-
Konsolidierung. Alte unversionierte Grundinstallationsbelege bleiben Nutzerarbeit.
