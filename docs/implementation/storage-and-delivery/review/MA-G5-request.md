# Reviewrequest MA-G5 – vollständiger Fachpfad und endgültige Ablösung

Abgenommene Basis: [MA-G4](MA-G4-accepted.md) mit diesen sechs Quell-SHAs:

- STACK `4858ceddd19cbc700c1242abc5c45357f15a8be4`
- ADMIN `deb68c22cf4914a265d16d555592152047cdbfb5`
- PUBLIC `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS `4f02a22bfd26ce2f67b93b38033104d5a6b18fcc`
- PLUGIN `cd1be45d43cc319aba12ad757ec7a29fef95975b`
- TOPICS `57933e7916744b38262024c0f7c2e3af94c0cc5a`

Der erste unabhängige Lauf `20261105T232632Z` endete mit `NACHARBEIT`.
Die neue Serien-Testfixture publizierte vor ihrer ersten Ausgabe. Die
Korrektur legt Ausgaben zuerst an, publiziert danach Reihe und Ausgaben und
setzt den aktuellen Zeiger. Kein Produktvertrag wurde gelockert. Die
isolierte Gegenprüfung von Sodata hat historische/aktuelle Ausgaben und
Pagination bestätigt. Die Betriebsanleitung trennt die Java-Versionen.
Der einmalige Jenkins-Archivschritt akzeptiert zusätzlich nur den exakten
belegten SHA-256 der Altimage-Vorlage; ein geändertes Exemplar wird abgewiesen.
Der ursprüngliche G5-Lauf ist nach einer G50-Teilbeobachtung mit Exit 1
abgebrochen. Es gibt keine erfolgreich ausgeführten Pflichtchecks zum
Übernehmen. Keine frühere abgenommene Phasensuite wiederholen.

Alle G50–G59 frisch und unabhängig prüfen. Ein eigener erfolgreicher
End-to-End-Lauf aus dem isolierten STACK:

```sh
python3 scripts/test_ingestion_end_to_end_g5.py
```

Den Exit-Code des eigentlichen Prozesses erfassen; Belegpfade im Report
absolut oder relativ zum Reviewverzeichnis angeben. Alle sechs Trees,
Handoff und Spec-Hashes prüfen, tatsächliche Codeprüfung und mindestens
eine eigene ausgeführte Gegenprobe. Produkt- und Testdateien nicht ändern.

Der Harness baut Admin, Portal, Jenkins samt HPI/Bundle, PG, Tooling und
Superset und startet genau die kanonischen zehn Dienste. Nach leerem Setup
erzeugt der ausdrückliche Testfixture-Einstieg nur synthetische Metadaten.
Eine echte Admin-Browseranmeldung erteilt das Lieferrecht. Echte OIDC-
Lieferanten laden CSV ein; der fest eingebaute GRETL-Runner erzeugt die
neuen Snapshots und privaten Dateien. Für Widerruf und Parallelität hält
eine vorübergehende isolierte SQL-Testpolicy echte Workerrequests vor
dem ersten Autorisierungslock an. Sie ist ausschliesslich Testcode und
wird entfernt. Es gibt weder einen Probeprozessor im Image noch eine
Abkürzung zur Fachpublikation. Recreate, Teilausfälle, alte Pfade und
Abbau werden im selben Lauf geprüft.

Die tatsächliche lokale Umstellung findet erst nach erfolgreicher
unabhängiger Abnahme statt. `local_cutover_g5.py` ist deshalb im Review
ausschliesslich zu lesen und anhand künstlicher Gegenproben zu beurteilen:
niemals gegen den Nutzerstack ausführen. Der bereits ausgeführte G1-Purge
wird nie wiederholt. `LOCAL_CUTOVER.md` muss vor der Umstellung ehrlich
ausstehend lauten. Review und lokaler Lauf werden getrennt belegt.
