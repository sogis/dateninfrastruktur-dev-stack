# MA-F2 – kontrollierte Datenübernahme

Die Übernahme verwendet die kanonischen Compose-Toolprofile und drei vollständige
logische PostgreSQL-Archive. Die beiden Quellcluster bleiben unverändert erhalten.
Eigene Datenbankrollen, Membershipoptionen, Passwortverifier, DB-/Rollenparameter,
Owners, effektive ACLs, Sequenzen, Trigger und alle Tabelleninhalte werden erhalten.
Quelle und Ziel werden vor jedem Schritt an konkrete Container, Mounts, private
Konfiguration und geprüfte ausführbare Dateien gebunden. Ein bestehendes unbekanntes
Ziel wird niemals gelöscht oder überschrieben.

Ein eng gebundener Kompatibilitätsschritt übernimmt die hashgeprüfte zusätzliche
`_st_concavehull(geometry)`-Extensionsfunktion des alten BAO-PostGIS3.5.2-Images;
kein pauschales Ignorieren von Restorefehlern. Das Ziel bleibt PG16.10/PostGIS3.5.2.

Die aktuelle gestoppte H2-Schreibschicht wird vollständig gesichert und mit exakt
dem Quellimage aus einer Kopie exportiert. Die Foundation-Keycloak-DB bleibt Basis.
MA-only-Personen/Clients und nachgewiesene Profiländerungen werden übernommen;
gleiche UUIDs werden geprüft, gleiche Namen/E-Mails allein reichen nicht.
Foundation-Passwörter haben bei belegter gleicher Person Vorrang. Realm-/Clientrollen
und Gruppenmitgliedschaften werden für belegte Personen/Gruppen ergänzt, ohne
bestehende Foundationzuordnungen zu entfernen. Abweichende gleichnamige Rollen-
definitionen blockieren vor Mutation; neue Rollen werden anhand ihrer überprüften
Definition in ihrem Realm-/Clientkontext zugeordnet. Gruppen-/Client-UUIDs bleiben
erhalten, auch über Replay. Der MA-Masterrealm
bleibt im Vollbackup, wird wegen abweichender administrativer Berechtigungen nicht
mit dem Foundation-Masterrealm vereinigt. Unerwartete weitere MA-Realms blockieren.

Die neue bekannte technische Migration V009 erlaubt ausschliesslich `di_migrator`
eine transaktionale, an Operations-ID und Zielissuer gebundene Principaländerung.
Fachmodell, Cayenne-DataMap und alle bisherigen SQL-Migrationen bleiben unverändert.
Interne Principal-IDs, Grants, Decisions und historische Auditzeilen bleiben gleich;
zusätzliche Migrationsauditereignisse werden separat nachgewiesen. Gefälschte
Writer-Kontextwerte reichen nicht zur Identitätsänderung. Kein öffentlicher Merge.

S3 übernimmt alle privaten Objekte einschliesslich Metadaten durch Copy, nie Delete.
Identische Objekte werden übersprungen; abweichende Bytes oder Metadaten blockieren
vor einem Überschreiben. Der Origin bleibt read-only. Der alte öffentliche
Foundation-Schlüssel behält Legacyzugriff, erhält keinen privaten Bucketzugriff.
Superset-Metadatenbank und SECRET_KEY sowie vorhandene Volumes werden übernommen.

Buildservices sind von ausführenden Toolservices getrennt: ein Runtimejob kann
keinen zusätzlichen PostgreSQL-Build auslösen. Private dotenv-Dateien werden durch
Compose selbst gelesen; Quotes, Dollars, Backslashes und Zeilenumbrüche bleiben
auch in übernommenen Secrets erhalten. Es erfolgt keine Shellauswertung.

Die Migrationsprobe erstellt eigene nichtleere Foundation-/MA-Quellen, darunter
das akzeptierte frühere Schema und das tatsächliche ältere PG/PostGIS-Image.
Sie prüft vollständigen Restore, aktuelle H2-Identitäten, alle historischen
Dateihashes, Konflikte, Replay, alten Auditbestand, privilegienbegrenzte Migration,
verschlüsselte Supersetverbindung und Rückfallgrenzen. Kein Nutzerbackup geht an
den Reviewer. Die tatsächliche lokale Übernahme und Retire folgen erst nach F3.

Livezustand bleibt LOCAL_CUTOVER_PENDING.

## Gezielte Nachprüfung

| Änderung | Gefährdeter Vertrag | Neue Prüfung |
|---|---|---|
| Runtimejobs von Builddiensten getrennt | unbeabsichtigtes PG-Recreate/JDBC/OIDC | vollständige F2-Datenkette, PG-Container-/Image-ID bleibt gleich |
| Compose-native dotenv-Verarbeitung | übernommene Credentials | Quotes/Dollars/Backslashes/Newlines plus sieben reale App-Logins |
| Globale Rollencheckpoints | Änderungen nach Backup, Rollenrestore | F09/F12/F13 einschliesslich veränderter Rollenparameter |
| Ergänzung MA-Rollen/Gruppen | aktuelle Identitätsrechte/Replay/Konflikt | gezielte echte Keycloakprobe plus Rollen/Gruppen in aktueller H2-Quellfixture |

F0 und unveränderte F1-Browser-/Routingverträge werden nicht als Vollsuite
wiederholt. Die unabhängige F2-Prüfung testet den endgültigen Kandidaten selbst.
