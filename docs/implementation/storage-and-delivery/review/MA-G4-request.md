# Reviewrequest MA-G4 – echter GRETL-CSV-Ablauf und SQL-Projektion

- STACK base: `cc8091e74bd83aab9f3848631ce85587c7a241ae`
- ADMIN base: `a19d6d0940ffc01728b9be3c5058279f5c3c3b39`
- PUBLIC base: `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS base: `e78bbe34356d4a46e128f209df0dc0ab1fed4729`
- PLUGIN base: `a23841d58d37eb3098480c34b7864922519436f3`
- TOPICS base: `fe25f56585dc6d3fb4cc432a42584a5350acc45c`

Alle G40–G49 frisch am exakten Kandidaten selbst prüfen und mindestens eine
eigene Gegenprobe ausführen. Keine Produkt-, Anforderungs-, Prompt- oder
Testdateien verändern. Die frühere MA-G3-Abnahme ist gebunden und
`MA-G3-accepted.md` nennt ihren nicht blockierenden ZIP-Hinweis. Der G4-
Kandidat härtet die Vorprüfung vor der Aktivierung des echten Prozessors.

Der erste unabhängige Lauf `20261105T221949Z` endete mit `NACHARBEIT`.
Er bestätigte intakte gespeicherte Objekte separat, aber der integrierte
Lauf brach beim Historiennachweis ab. Der G45-Negativtest änderte durch
eine flache Kopie den Dateischlüssel des späteren G41-Nachweises. Jetzt
ändert er nur den manipulierten HTTP-Request; der Speicherlesetest meldet
eine fehlende Datei ausdrücklich. Der Queue-Unit-Test entfernt seine
Testaufträge noch unter dem Queue-Lock, damit sein Jenkins-Testverzeichnis
nicht mit einem anlaufenden Build kollidiert. Seit dem ersten Review hat
sich kein Produktcode geändert. Die Teilbeobachtungen des abgebrochenen
Laufs sind keine übernehmbaren PASS-Nachweise. Den G4-Harness deshalb bis
zum Ende neu ausführen; keine abgeschlossenen MA-G0–G3-Suiten wiederholen.

Ausführbare Nachweise im isolierten STACK:

```sh
python3 scripts/test_ingestion_processing_g4.py
```

Der erste Harness baut das tatsächliche HPI, das vollständige Runnerbundle
und die kanonischen Testimages. Er startet nur die für diesen Ablauf
benötigten Dienste mit privaten Testcredentials, installiert technische
ClickHouse-Rechte ausdrücklich und verwendet das reale Keycloak-/Jenkins-
Browserfrontend. Er prüft zwei echte Modellverträge und eine separate
Typfixture, Replace/Append, Historie und private Distributionen; er
unterbricht eigene ClickHouse-, Garage- und Admin-Abhängigkeiten, prüft die
verlorene Annahmeantwort mit einem echten wiederholten HTTP-Request und
validiert den nachfolgenden aktuellen SQL-Stand. Er kontrolliert die laufenden
CPS-Dateien auch auf die neu hinzugekommenen S3-/CH-Credentials.
Nach Archivierung bleibt die Historie erhalten. Der gezielte unabhängige
G4-Lauf prüft die tatsächlich betroffenen Rechte-, Fence-, Transaktions- und
Annahmeverträge mit echten Artefakten. Der separaten Entwicklerregression
`test_ingestion_backend_g2.py` dienen synthetische Attestierungen; diese
sind kein End-to-End-Verarbeitungsnachweis.

Die vollständigen Laufzeitbelege liegen nur unter dem eigenen
`.runtime/mag-g4-*`. Keine Originalinstanz, keine Nutzerdumps, keine echten
Credentials. Der Nutzerstack bleibt bis zum abgenommenen Endcutover auf
dem früheren geprüften Stand. `MA-G4_PROCESSING.md` beschreibt das
Daten-, Betriebs- und Vertrauensmodell. Insbesondere sind PG-Annahme
und SQL-Projektion getrennte, überprüfte Schritte. Keine neue Plattform,
keine personenbezogenen ClickHouse-Rechte und kein aktiver Probeprozessor.
