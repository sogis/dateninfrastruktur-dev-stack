#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${GARAGE_BROWSER_ACCESS_KEY:?./scripts/init.sh ausführen}"
: "${GARAGE_BROWSER_SECRET_KEY:?./scripts/init.sh ausführen}"
: "${PRIVATE_TEST_OBJECT_ID:?./scripts/init.sh ausführen}"
GATEWAY_PORT="${GATEWAY_PORT:-18081}"
PRIVATE_BUCKET="ch.so.dateninfrastruktur.private"
PRIVATE_KEY="private-foundation-smoke.txt"
EXPECTED="private-object-id=${PRIVATE_TEST_OBJECT_ID}"

echo "Prüfe berechtigten Zugriff auf das private Testobjekt ..."
private_content="$(docker compose --profile tools run --rm --no-deps aws \
  s3 cp "s3://${PRIVATE_BUCKET}/${PRIVATE_KEY}" - 2>/dev/null)"
[[ "${private_content}" == "${EXPECTED}" ]] || {
  echo "Berechtigter Abruf des privaten Testobjekts stimmt nicht." >&2
  exit 1
}

echo "Prüfe anonymen S3-Zugriff auf den privaten Bucket ..."
if docker compose --profile tools run --rm --no-deps aws \
  s3api head-object --bucket "${PRIVATE_BUCKET}" --key "${PRIVATE_KEY}" \
  --no-sign-request >/dev/null 2>&1; then
  echo "Anonymer S3-Zugriff auf den privaten Bucket war erlaubt." >&2
  exit 1
fi

echo "Prüfe öffentlichen Leseschlüssel auf dem privaten Bucket ..."
if docker compose --profile tools run --rm --no-deps \
  -e AWS_ACCESS_KEY_ID="${GARAGE_BROWSER_ACCESS_KEY}" \
  -e AWS_SECRET_ACCESS_KEY="${GARAGE_BROWSER_SECRET_KEY}" \
  aws s3api head-object --bucket "${PRIVATE_BUCKET}" --key "${PRIVATE_KEY}" >/dev/null 2>&1; then
  echo "Der öffentliche Leseschlüssel konnte das private Objekt lesen." >&2
  exit 1
fi
if docker compose --profile tools run --rm --no-deps \
  -e AWS_ACCESS_KEY_ID="${GARAGE_BROWSER_ACCESS_KEY}" \
  -e AWS_SECRET_ACCESS_KEY="${GARAGE_BROWSER_SECRET_KEY}" \
  aws s3api list-objects-v2 --bucket "${PRIVATE_BUCKET}" >/dev/null 2>&1; then
  echo "Der öffentliche Leseschlüssel konnte den privaten Bucket listen." >&2
  exit 1
fi

echo "Prüfe öffentlichen Gateway-Pfad auf das private Objekt ..."
body_file="$(mktemp "${TMPDIR:-/tmp}/private-gateway.XXXXXX")"
status="$(curl --silent --show-error --output "${body_file}" --write-out '%{http_code}' \
  "http://localhost:${GATEWAY_PORT}/${PRIVATE_BUCKET}/${PRIVATE_KEY}")"
if [[ "${status}" == "200" ]] || grep -Fq "${EXPECTED}" "${body_file}"; then
  echo "Gateway lieferte den privaten Objektinhalt (HTTP ${status})." >&2
  rm -f "${body_file}"
  exit 1
fi
rm -f "${body_file}"

echo "Prüfe, dass öffentliche Publikationsartefakte das private Testobjekt nicht enthalten ..."
scan_dir="$(mktemp -d "${TMPDIR:-/tmp}/public-scan.XXXXXX")"
cleanup_scan() {
  rm -rf "${scan_dir}"
}
trap cleanup_scan EXIT
docker compose --profile tools run --rm --no-deps \
  -v "${scan_dir}:/scan" \
  aws s3 sync s3://ch.so.daten /scan >/dev/null
if grep -rIlF "${EXPECTED}" "${scan_dir}" >/dev/null 2>&1; then
  echo "Ein öffentliches Publikationsartefakt enthält den privaten Testinhalt." >&2
  exit 1
fi

echo "Privater Speicher ist geprüft: berechtigt lesbar, über alle öffentlichen Wege gesperrt."
