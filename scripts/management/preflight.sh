#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "$0")/../.." && pwd)"
printf 'Architecture: '; uname -m
docker compose version
exec "$stack/scripts/status.sh" "$@"
