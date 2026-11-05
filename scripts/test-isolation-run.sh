#!/usr/bin/env bash
set -euo pipefail
printf '%s\n' 'Dieser Grundinstallationspfad ist historisch. Verwende scripts/test-consolidation.sh --phase MA-F1/MA-F2/MA-F3/MA-F4 für isolierte Tests oder scripts/smoke-test.sh für den aktiven Compose-Kontext. Keine Legacyinstanz wurde gestartet oder verändert.' >&2
exit 2
