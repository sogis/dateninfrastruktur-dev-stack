#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/.." && pwd)"
if [[ $# != 2 || "$1" != --phase ]]; then printf 'Usage: %s --phase MA-F0|MA-F1|MA-F2|MA-F3|MA-F4\n' "$0" >&2; exit 2; fi
case "$2" in
  MA-F0) exec python3 "$stack/scripts/test_consolidation_f0.py" ;;
  MA-F1) exec python3 "$stack/scripts/test_consolidation_f1.py" ;;
  MA-F2) exec python3 "$stack/scripts/test_consolidation_f2.py" ;;
  MA-F3) exec python3 "$stack/scripts/test_consolidation_f3.py" ;;
  MA-F4) exec python3 "$stack/scripts/test_consolidation_f4.py" ;;
  *) printf 'Phase not implemented: %s\n' "$2" >&2; exit 2 ;;
esac
