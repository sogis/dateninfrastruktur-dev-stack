# Abgeschlossene einmalige G1-Umstellung: nur Regressionfixtures

Der lokale Cutover ist durchgeführt und verifiziert. Die produktiven Host-/Tool-
Einstiege und der Docker-COPY sind entfernt. Diese beiden Kopien dienen allein
isolierten Tests mit synthetischen Quellen; sie werden vorübergehend in deren
private Runtime kopiert und gehören weder zum normalen Image noch zur Operator-API.
Der letzte unabhängige Cutover-Kandidat bleibt in Git und den G1-Handoffs erhalten.
Keine Umstellung oder Purge beim normalen Start; keine erneute lokale Ausführung.
