# Reviewrequest MA-G1 – privater Einbucketbetrieb und bekannte Bestandsübernahme

- STACK base: `aa39924ef68084e379dc7c8311835a207fe91e8c`
- ADMIN base: `92e1fddb4b3af166a89ab065c4a282d49b9a6895`
- PUBLIC base: `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS base: `f32e40253cdd03a9327b66582aa2050557301239`
- PLUGIN base: `5535624776f3c1958192f45782f8724c08b31dd7`
- TOPICS base: `7c83135d69ada644e6e9a0352c3eb1308f798861`

## Abschlussdelta nach tatsächlichem lokalem Storagecutover

Vollständige unabhängige Erstabnahme: `20261105T160802Z`, Report-SHA256
`4d71d770e172fd5e82930d0f85070dfca33f27abbcb6b09755477a2e4e1ec62c`.
Die optionale key-lokale Foundationkorrektur wurde danach separat unabhängig
akzeptiert: `20261105T162915Z`, Report-SHA256
`169cbf830d11a7f72be6eeb29c1833ad0fcf29868d414f07f65eec4d2eeb5900`.

Nach den beiden Abnahmen wurde der ausdrücklich beauftragte **tatsächliche**
lokale Storagecutover ausgeführt und verifiziert. Bereinigter Bericht:
`LOCAL_STORAGE_CUTOVER.md`. Original-ENV/Dateien/Tokens bleiben privat und sind
nicht Teil des Handoffs. Ein eigener Test-Compose ist nicht dieser lokale Nachweis.

Änderung: Einmaligen Hostoperator löschen, Engine/Tooloperator ausschliesslich als
eng benannte synthetische Regressionfixtures unter `tests/ingestion/retired/`
behalten. Docker-COPY entfernen; normales Toolimage enthält die Engine nicht mehr.
Testtreiber kopieren benötigte Fixturemodule nur in eigene private Test-Runtimes.
Lesende Browserprobe als Testhilfe ohne mutierende Lifecycle-API extrahieren.
README, Retirementmatrix und Status spiegeln den abgeschlossenen lokalen Schritt.

G14/G19 frisch prüfen:

```sh
python3 scripts/test_ingestion_foundation_g1.py
```

Prüft normales tatsächliches Toolimage ohne Cutovermodul sowie dieselbe reale
key-lokale Foundation-/GET-Hash-/Unknownobjekt-/Globalnamenkontroll-/Retire-/
Aliasneuzuordnungsprobe über die testweise kopierte unveränderte Engine.
Zusätzlich statisch keine aktive Host-/Compose-/Operatorreferenz auf die
entfernten Einstiege; keine vorhandene Legacyimport-Testreferenz reaktivieren.
Eigene Gegenprobe ausführen, z.B. frühzeitige Verweigerung eines entfernten
Operator-/Normalstart-Migrationspfads oder wirksame Nichtverfügbarkeit im Image.

G10–G13/G15–G18 werden einzeln aus der vollständigen **ersten** Abnahme gebunden
übernommen: dort sind diese Checks tatsächlich EXECUTED, kein blosses Weiterreichen
eines CARRIED-Urteils. Normales Garage-Provisioning, allgemeine Copy-/Purge-/
Resumezustände, INTERLIS/SQL/ORM/Fingerprint, Browser-/Grant-/Downloadkette sowie
Container-Recreate/Credentials sind unverändert. Zwischenzeitliche Änderungen
betreffen nur den separat bereits akzeptierten optionalen Fixtureschritt,
Testablage/aktive Retirementgrenzen und Dokumentation. Reviewer muss diese
Nichtbetroffenheit an beiden Diffs selbst bestätigen. Keine pauschale Wiederholung
aller Browser-/Schema-/Cutoversuiten für das Entfernen eines abgeschlossenen Tools.

Die nächste Phase bleibt bis zur aktuellen unabhängigen Abschlussabnahme gesperrt.
