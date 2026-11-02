# Beibehaltene technische Namen

Eine globale Ersetzung `datenportal` → `dateninfrastruktur` wurde nicht
durchgeführt. Die folgenden Namen sind aktive Kompatibilitätsverträge. Sie
bleiben erhalten, weil eine Umbenennung keinen funktionalen Nutzen hätte und
bestehende Bilder, Plugins, Jelly-/JS-Pfade, Gradle-Verträge oder fachliche
Referenzen brechen würde.

| Name | Fundort | Zweck | Begründung |
|---|---|---|---|
| `jenkins-gretl-datenportal-plugin` | Plugin-`pom.xml`, HPI/JPI, Jenkins-Plugin-ID, Image-Pluginpfad | Technische Plugin-Identität | Jenkins erkennt das Plugin und seine Erweiterungen über diese ID; HPI/JPI- und Assetpfade hängen daran. |
| `ch.so.agi.jenkins.gretldatenportal` | Java-Paket, Jelly-Ressourcen, Jenkins-Deskriptoren | Java-/Jelly-Zuordnung | Package- und Ressourcenpfade sind Teil des Jenkins-Klassenpfads und der UI-Ressourcen. |
| `gretlDatenportalJobs` | JCasC in `services/jenkins/jenkins-stack.yaml`, `casc/*.yaml` | JCasC-Symbol des Plugins | Das Symbol ist der stabile Konfigurationsschlüssel des Plugins. |
| `prepareDatenportalWorkspace` | `shared/Jenkinsfile`, Plugin-Schritt | Pipeline-Schritt | Der Themenrepo-Vertrag ruft den Schritt unter diesem Namen auf. |
| `gretl-datenportal-seed` | JCasC, Bootstrap, Jenkins-Jobs | Seedjob und Bootstrap-Erwartung | Bootstrap und Dokumentation adressieren den Job unter diesem Namen. |
| `datenportal-topic-repository` | JCasC, `shared/Jenkinsfile` | Gemeinsamer Pipeline-Lock | Der Lock-Name verhindert parallele Publikationen; er ist kein Umgebungsziel. |
| `gretl-datenportal-job.yaml`, `gretl-datenportal-defaults.yaml`, `gretl-datenportal-teams.yaml` | Themenrepo, Plugin-Scanner | Scannervertrag | Das Plugin findet Organisationen, Defaults und Teams über diese Dateinamen. |
| `/opt/datenportal` | Jenkins-Image, Sodata-Image, Compose-Mounts | Containerinterne Arbeits- und Bundlepfade | Image-Aufbau, Offline-Bundle, DuckDB-Extension-Pfad und JCasC-Mount hängen daran. |
| `/var/jenkins_home/gretl-datenportal/topic-repo` | Jenkins-Plugin, Bootstrap | Containerinterner Themenrepo-Pfad | Der Plugin-Checkout und der Bootstrap-Publication-Lauf verwenden diesen Pfad. |
| `DATENPORTAL_*` | Compose, Sodata-Konfiguration, Skripte | Bestehende Konfigurationsschnittstellen | Die Anwendung und ihre Tests lesen diese Variablen; eine Umbenennung wäre eine unnötige Schnittstellenänderung. |
| `datenportal.*` | Sodata-`application.yml`, Tests | Bestehende Konfigurationsschlüssel | Spring-Boot-Konfiguration und Tests sind auf diese Präfixe abgestimmt. |
| `datenportal-sodata` | Gradle-`settings.gradle`, Dockerfile-COPY, Footer | Sodata-Artefaktname | Dockerfile und Gradle-Build müssen zusammenpassen; der Name ist ein technischer Vertrag. |
| `SO_AGI_DataCatalog_*` | INTERLIS-Modelle, Publikations-SQL, Manifest | Fachliche Modellnamen | Fachliche Verträge und Referenzen des Themenrepos. |
| `ch.so.*`-Datensatz-IDs | Themenrepo, XTF, Katalog | Fachliche Metadaten-IDs | Fachliche Identitäten dürfen nicht umbenannt werden. |
| `datenportal-dev-stack` in Quellenangaben | `docs/provenance.md`, Manifest | Herkunftsnachweis | Die Quell-URLs bleiben als Provenienz erhalten; sie sind keine aktiven Laufzeitziele. |

## Nicht beibehaltene aktive Ziele

Folgende frühere aktive Ziele wurden bewusst entfernt oder ersetzt:

- alte Anwendungsimages `sogis/datenportal-jenkins`, `sogis/datenportal-sodata`,
  `sogis/datenportal-datenblatt-editor`, `sogis/datenportal-dokumentation`,
- der Registry-/HPI-Fallback auf `jars.interlis.guru`,
- der frühere Editor- und Dokumentationswebsite-Startpfad,
- feste Hostports `8081`, `3900`, `8080`, `8082` des alten Stacks,
- die alten Compose-Projektnamen und gemeinsamen Hostpfade.
