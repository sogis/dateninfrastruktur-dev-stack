#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/../.." && pwd)"
exec "$stack/scripts/test-consolidation.sh" "$@"
