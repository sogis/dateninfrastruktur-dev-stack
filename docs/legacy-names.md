# Technische Namen und Kompatibilitätsverträge

Die aktiven Repo-, Image-, Umgebungs- und Build-Namen wurden auf den
`dateninfrastruktur`-Namespace umgestellt. Eine kleine Zahl technischer
Schnittstellen bleibt bewusst erhalten, weil eine Umbenennung Jenkins-Verträge,
fachliche Identitäten oder Containerpfade brechen würde.

## Neue technische Identität

| Name | Fundort | Zweck | Begründung |
|---|---|---|---|
| `jenkins-gretl-dateninfrastruktur-plugin` | Plugin-`pom.xml`, HPI/JPI, Jenkins-Plugin-ID, Image-Pluginpfad | Aktive technische Plugin-Identität | Maven-Artefakt, Jenkins-ID, HPI/JPI und Assetpfade wurden gemeinsam umgestellt. |
| `DATENINFRASTRUKTUR_*` | Compose, Sodata, Jenkins-Dev, Themenrepo | Aktive Umgebungsvariablen | Ersetzt die früheren `DATENPORTAL_*`-Variablen vollständig. |
| `dateninfrastruktur.*` | Sodata-`application*.yml`, Tests, Gradle-Buildproperties | Aktive Konfigurationsschlüssel | Ersetzt die früheren `datenportal.*`-Schlüssel in den aktiven Pfaden. |
| `dateninfrastruktur-sodata` | Gradle-`settings.gradle`, Dockerfile-COPY, Footer, App-Name | Sodata-Artefakt- und App-Name | Gradle-Build, Dockerfile und Laufzeitname wurden gemeinsam umgestellt. |

## Beibehaltene technische Namen

| Name | Fundort | Zweck | Begründung |
|---|---|---|---|
| `ch.so.agi.datenportal` | Java-Paket, Klassen, Jelly-Ressourcen | Java-/Jelly-Zuordnung | Package- und Ressourcenpfade sind Teil des Jenkins-/Spring-Klassenpfads; eine Umbenennung bringt keinen funktionalen Nutzen. |
| `ch.so.agi.jenkins.gretldatenportal` | Java-Paket, Jelly-Ressourcen, Jenkins-Deskriptoren | Java-/Jelly-Zuordnung | Package- und Ressourcenpfade sind Teil des Jenkins-Klassenpfads und der UI-Ressourcen. |
| `gretlDatenportalJobs` | JCasC in `services/jenkins/jenkins-stack.yaml`, `casc/*.yaml` | JCasC-Symbol des Plugins | Das Symbol ist der stabile Konfigurationsschlüssel des Plugins. |
| `prepareDatenportalWorkspace` | `shared/Jenkinsfile`, Plugin-Schritt | Pipeline-Schritt | Der Themenrepo-Vertrag ruft den Schritt unter diesem Namen auf. |
| `gretl-datenportal-seed` | JCasC, Bootstrap, Jenkins-Jobs | Seedjob und Bootstrap-Erwartung | Bootstrap und Dokumentation adressieren den Job unter diesem Namen. |
| `datenportal-topic-repository` | JCasC, `shared/Jenkinsfile` | Gemeinsamer Pipeline-Lock | Der Lock-Name verhindert parallele Publikationen; er ist kein Umgebungsziel. |
| `gretl-datenportal-job.yaml`, `gretl-datenportal-defaults.yaml`, `gretl-datenportal-teams.yaml` | Themenrepo, Plugin-Scanner | Scannervertrag | Das Plugin findet Organisationen, Defaults und Teams über diese Dateinamen. |
| `gretl-datenportal.css`, `gretl-datenportal.js` | Plugin-Webapp, Jelly-Ressourcen, Plugin-Tests | Statische Assetnamen | Die Dateinamen sind an Jelly-Referenzen und das veröffentlichte HPI gebunden; eine Umbenennung bringt keinen funktionalen Nutzen. |
| `/opt/datenportal` | Jenkins-Image, Sodata-Image, Compose-Mounts | Containerinterne Arbeits- und Bundlepfade | Image-Aufbau, Offline-Bundle, DuckDB-Extension-Pfad und JCasC-Mount hängen daran. |
| `/var/jenkins_home/gretl-datenportal/topic-repo` | Jenkins-Plugin, Bootstrap | Containerinterner Themenrepo-Pfad | Der Plugin-Checkout und der Bootstrap-Publication-Lauf verwenden diesen Pfad. |
| `datenportal.explore.*` | Sodata-Frontend (`autoSaveId`) | Browserlokale Layout- und Editorzustände | Die Schlüssel liegen nur im Browser; eine Umbenennung würde gespeicherte Benutzerlayouts ohne Servergewinn zurücksetzen. |
| `SO_AGI_DataCatalog_*` | INTERLIS-Modelle, Publikations-SQL, Manifest | Fachliche Modellnamen | Fachliche Verträge und Referenzen des Themenrepos. |
| `ch.so.*`-Datensatz-IDs | Themenrepo, XTF, Katalog | Fachliche Metadaten-IDs | Fachliche Identitäten dürfen nicht umbenannt werden. |
| `datenportal-dev-stack` in Quellenangaben | `docs/provenance.md`, Manifest | Herkunftsnachweis | Die Quell-URLs bleiben als Provenienz erhalten; sie sind keine aktiven Laufzeitziele. |

## Nicht beibehaltene aktive Ziele

Folgende frühere aktive Ziele wurden bewusst entfernt oder ersetzt:

- `jenkins-gretl-datenportal-plugin` als Maven-Artefakt, Jenkins-Plugin-ID,
  HPI/JPI-Dateiname und Assetpfad; die alte Maven-Snapshot-Koordinate wurde
  entfernt und darf nicht weiterverwendet werden.
- `DATENPORTAL_*` als aktive Umgebungsvariablen; ersetzt durch
  `DATENINFRASTRUKTUR_*`.
- `datenportal.*` als aktive Sodata-/Gradle-Konfigurationsschlüssel; ersetzt
  durch `dateninfrastruktur.*`.
- `datenportal-sodata` als aktiver Gradle-/App-Artefaktname; ersetzt durch
  `dateninfrastruktur-sodata`.
- alte Anwendungsimages `sogis/datenportal-jenkins`, `sogis/datenportal-sodata`,
  `sogis/datenportal-datenblatt-editor`, `sogis/datenportal-dokumentation`,
- der Registry-/HPI-Fallback auf `jars.interlis.guru`,
- der frühere Editor- und Dokumentationswebsite-Startpfad,
- feste Hostports `8081`, `3900`, `8080`, `8082` des alten Stacks,
- die alten Compose-Projektnamen und gemeinsamen Hostpfade.
