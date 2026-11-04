#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/../.." && pwd)"
exec python3 "$(dirname "$stack")/dateninfrastruktur-admin/scripts/setup.py" "$@"
