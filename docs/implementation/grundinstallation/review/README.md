# Unabhängige Reviews

Jeder echte Reviewlauf schreibt in einen neuen Ordner: `<candidate-id>/<run-id>/REVIEW.md` mit Belegen unter `evidence/`. Verwende die [Reviewberichtvorlage](../templates/REVIEWBERICHT.template.md) und den [Reviewprompt](../START_REVIEW.md).

Der Reviewer repariert keinen Produktcode und verändert keine Auftrags-, AGENTS-, Test-, Phasenbericht- oder Manifestdateien. Er darf eigene isolierte Builds und Tests ausführen. Nicht ausgeführte Pflichtprüfungen sind kein PASS.

Nach Abschluss können die unveränderten, geheimnisfreien Reviewunterlagen durch den Implementierer oder Auftraggeber in einem separaten Nachweiscommit archiviert werden. Ein Nachweiscommit ersetzt nicht den geprüften Produktcommit. Frühere Läufe nicht überschreiben.

Diese README ist Produktdokumentation; die erzeugten Reviewlauf-Unterordner sind Nachweisartefakte. Details stehen in [Abschnitt 8 des Auftrags](../AUFTRAG_GRUNDINSTALLATION.md#8-handoff-und-unabhängiges-review).
