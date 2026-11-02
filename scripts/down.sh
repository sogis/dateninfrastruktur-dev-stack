#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

if [[ ! -f .env ]]; then
  echo "Keine lokale .env vorhanden; es gibt nichts zu stoppen." >&2
  exit 1
fi

# A regular stop preserves all named volumes.
docker compose down
