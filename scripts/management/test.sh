#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/../.." && pwd)"
admin="$(dirname "$stack")/dateninfrastruktur-admin"
if [[ $# != 2 || "$1" != --phase ]]; then
  printf 'Usage: %s --phase MA-0|MA-A|MA-B\n' "$0" >&2
  exit 2
fi
case "$2" in
  MA-0) "$stack/scripts/management/preflight.sh"; python3 "$stack/scripts/management/test_review_gate.py"; python3 "$admin/scripts/compatibility.py" ;;
  MA-A) python3 "$admin/scripts/test_models.py" ;;
  MA-B) python3 "$admin/scripts/test_persistence_all.py"; python3 "$admin/scripts/compatibility.py" ;;
  *) printf 'Phase not implemented/accepted: %s\n' "$2" >&2; exit 2 ;;
esac
