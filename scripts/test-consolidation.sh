#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $# != 2 || "$1" != --phase ]]; then printf 'Usage: %s --phase MA-F0\n' "$0" >&2; exit 2; fi
case "$2" in
  MA-F0) exec python3 "$stack/scripts/test_consolidation_f0.py" ;;
  *) printf 'Phase not implemented: %s\n' "$2" >&2; exit 2 ;;
esac
