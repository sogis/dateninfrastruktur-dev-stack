#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/../.." && pwd)"
admin="$(dirname "$stack")/dateninfrastruktur-admin"
export DI_MANAGEMENT_RUNTIME_DIR="${DI_MANAGEMENT_RUNTIME_DIR:-$admin/.runtime/managed/database}"
exec python3 "$admin/scripts/managed_runtime.py" stop
