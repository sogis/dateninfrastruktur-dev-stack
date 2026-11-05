# Reviewrequest MA-G3 – Jenkins-OIDC und generische Anlieferung

- STACK base: `4de934b9a82ac4b0aa3f6e92f8db44b3a31e4194`
- ADMIN base: `cb4074d7c76d8a9b93e0d6a614369c4fb9ed85ad`
- PUBLIC base: `d066314ad81750d3c2a16a1ade9f626aa4732521`
- JENKINS base: `f32e40253cdd03a9327b66582aa2050557301239`
- PLUGIN base: `5535624776f3c1958192f45782f8724c08b31dd7`
- TOPICS base: `5e696006754cc7389ef002a7b24d6b90df3de80a`

Alle G30–G39 an diesem Kandidaten selbst ausführen und das Ziel gegen die
verbindlichen Spezifikationen prüfen. Eigene ausgeführte Gegenprobe vornehmen.
Produkt-, Test-, Prompt- und Vertragsdateien bleiben unverändert. G0–G2 sind
bereits unabhängig abgenommen. Der reale Nutzerstack bleibt auf G1; keine
Nutzer-Umgebung verwenden, verändern, auslesen oder starten.

`MA-G3_JENKINS.md` beschreibt den Umfang und die Betriebsgrenzen. Der neue
normale Kandidat enthält noch keinen CSV-Prozessor; G4 liefert die fachliche
Verarbeitung. Der isolierte Probeprozessor erzeugt kein Manifest, keinen
Fachcommit und keine Publikation.

Im isolierten STACK-Checkout:

```sh
python3 scripts/test_ingestion_jenkins_g3.py
python3 scripts/test_ingestion_backend_g2.py
```

Das erste Skript baut das HPI mit Maven inklusive JenkinsRule-Tests und das
Jenkins-Image aus dem exakten Kandidaten, startet nur die benötigten Dienste
mit frischen Laufzeitdaten und verifiziert echten Chromium-Codeflow, Subject-
und Formulargrenzen, Upload und die technische Pipeline. Es prüft vorher
das Offline-Retirement an einem eigens erzeugten gestoppten Jenkins-Volume;
der fremde Fixturejob bleibt erhalten. Der JUnit-Beleg für Audience-/Expiry-
Checks, Queue-API/Marker/Kollision und Spool-Symlink liegt im PLUGIN-Checkout
unter dem ignorierten `target/surefire-reports`. Für das G3-Review diesen
Test-Build tatsächlich ausführen und die Tests nachweisen.

Der Backendharness ist die kleinste sinnvolle Prozessregression für die
zusätzliche Runnerbindung und den Wiederanlauf: echte PG/Cayenne-Fences,
Beendigung exakt gebundener Runs, unveränderte Commit-/Ack-Semantik und
die vorhandenen Authentisierungs-/Autorisierungsgrenzen. Synthetische
Manifeste in diesem Backendharness sind kein CSV-Verarbeitungsnachweis.

Der G3-Harness verwendet eigene `.runtime/mag-g3-*`-Pfade und Docker-Ressourcen.
Prüfbelege nur bereinigt übernehmen. Das ursprüngliche G0-Image dient nur
als Quelle der im Build einzeln gehashten Tools und wird nicht gestartet.
