#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/.." && pwd)"
exec python3 "$stack/scripts/compose_operations.py" dev "$@"
