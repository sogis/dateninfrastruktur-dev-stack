# Festgeschriebene Reviewkandidaten

Je tatsächlicher Übergabe einen neuen Unterordner anlegen, beispielsweise `c001/`. Dort liegen `candidate-manifest.json` und bei Bedarf Datei-/Diff-Manifeste unter `snapshots/`.

Das [Beispielmanifest](../candidate-manifest.example.json) ist keine erfüllte Abnahme. Beobachtete Commits, Modelle, Versionen und Hashes erst für einen realen Kandidaten eintragen. Relative Pfade werden vom gemeinsamen Workspace aus aufgelöst.

Den Produktstand zuerst festschreiben, danach das Manifest erzeugen. Ab Reviewbeginn unverändert lassen. Nach dem abgeschlossenen Review können diese Unterlagen separat versioniert werden; nicht nachträglich den Manifestbezug auf diesen Nachweiscommit ändern. Die genauen Regeln stehen in [Abschnitt 8 des Auftrags](../AUFTRAG_GRUNDINSTALLATION.md#8-handoff-und-unabhängiges-review).

Diese README ist reguläre Produktdokumentation. Nur die tatsächlich erzeugten Kandidatenunterordner werden bei der Abgrenzung der Nachweise aus dem Produktdateisnapshot ausgenommen.
