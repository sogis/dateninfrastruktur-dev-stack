#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/../.." && pwd)"
admin="$(dirname "$stack")/dateninfrastruktur-admin"
export DI_MANAGEMENT_RUNTIME_DIR="${DI_MANAGEMENT_RUNTIME_DIR:-$admin/.runtime/managed/database}"
if [[ $# != 3 ]]; then printf 'Usage: %s <dataset-uuid> <expected-version> <distribution-uuid>\n' "$0" >&2; exit 2; fi
exec python3 - "$admin" "$@" <<'PYTHON'
import sys
sys.path.insert(0,sys.argv[1]+'/scripts')
from managed_runtime import activate
activate(sys.argv[2],int(sys.argv[3]),sys.argv[4])
PYTHON
