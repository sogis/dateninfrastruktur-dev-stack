#!/usr/bin/env bash
set -euo pipefail
stack="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
: "${IMAGE_NAME:?Expliziten lokalen Kandidatentag als IMAGE_NAME setzen}"
[[ $# -eq 1 ]] || { printf 'Verwendung: IMAGE_NAME=<lokaler Tag> %s <neues Kontextverzeichnis>\n' "$0" >&2; exit 2; }
exec "$stack/../dateninfrastruktur-jenkins-dev/bin/build-image.sh" "$1"
