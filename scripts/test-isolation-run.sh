#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

PROJECT="dateninfrastruktur-review-r001"
RUNTIME=".runtime/${PROJECT}"
ENV_FILE="${RUNTIME}/review.env"
REVIEW_GATEWAY_PORT=28081
REVIEW_KEYCLOAK_PORT=28080
REVIEW_SUPERSET_PORT=28088
REVIEW_CLICKHOUSE_HTTP_PORT=28123
REVIEW_CLICKHOUSE_NATIVE_PORT=29000
REVIEW_GARAGE_S3_PORT=23900
REVIEW_GATEWAY_PORT_2=28081

mkdir -p "${RUNTIME}"
chmod 700 "${RUNTIME}"
cp .env.example "${ENV_FILE}"
python3 - "${ENV_FILE}" "${PROJECT}" "${RUNTIME}" "${REVIEW_GATEWAY_PORT}" \
  "${REVIEW_KEYCLOAK_PORT}" "${REVIEW_SUPERSET_PORT}" \
  "${REVIEW_CLICKHOUSE_HTTP_PORT}" "${REVIEW_CLICKHOUSE_NATIVE_PORT}" \
  "${REVIEW_GARAGE_S3_PORT}" <<'PY'
import sys

path, project, runtime, gateway, keycloak, superset, clickhouse, native, garage = sys.argv[1:10]
replacements = {
    "COMPOSE_PROJECT_NAME": project,
    "RUNTIME_DIR": runtime,
    "GATEWAY_PORT": gateway,
    "KEYCLOAK_PORT": keycloak,
    "SUPERSET_PORT": superset,
    "CLICKHOUSE_HTTP_PORT": clickhouse,
    "CLICKHOUSE_NATIVE_PORT": native,
    "GARAGE_S3_PORT": garage,
}
lines = []
seen = set()
for line in open(path, encoding="utf-8"):
    key = line.split("=", 1)[0]
    if key in replacements:
        lines.append(f"{key}={replacements[key]}\n")
        seen.add(key)
    else:
        lines.append(line)
for key, value in replacements.items():
    if key not in seen:
        lines.append(f"{key}={value}\n")
open(path, "w", encoding="utf-8").writelines(lines)
PY
chmod 600 "${ENV_FILE}"

env -i PATH="${PATH}" HOME="${HOME}" TMPDIR="${TMPDIR:-/tmp}" \
  ENV_FILE="${REPO_DIR}/${ENV_FILE}" RUNTIME_DIR="${REPO_DIR}/${RUNTIME}" \
  ./scripts/init.sh

before_ids="$(shasum -a 256 .runtime/dateninfrastruktur-dev-stack/keycloak-identities.json 2>/dev/null | awk '{print $1}' || true)"
before_project="$(docker compose ps --format '{{.Service}} {{.State}}' | sort)"
if [[ -z "${before_ids}" ]]; then
  ./scripts/test-keycloak.sh >/dev/null
  before_ids="$(shasum -a 256 .runtime/dateninfrastruktur-dev-stack/keycloak-identities.json | awk '{print $1}')"
fi

review_compose() {
  env -i PATH="${PATH}" HOME="${HOME}" docker compose     --env-file "${REPO_DIR}/${ENV_FILE}" -p "${PROJECT}" "$@"
}

cleanup() {
  review_compose down -v --remove-orphans >/dev/null 2>&1 || true
}
trap cleanup EXIT

echo "Starte isolierten Reviewstack ${PROJECT} auf eigenen Ports ..."
review_compose up -d --wait --wait-timeout 300 \
  postgres clickhouse keycloak superset

python3 - "${REVIEW_KEYCLOAK_PORT}" "${REVIEW_SUPERSET_PORT}" <<'PY'
import json
import sys
import urllib.request

keycloak_port, superset_port = sys.argv[1:3]
with urllib.request.urlopen(
        f"http://localhost:{keycloak_port}/realms/dateninfrastruktur/.well-known/openid-configuration",
        timeout=30) as response:
    discovery = json.load(response)
    assert discovery["issuer"].endswith("/realms/dateninfrastruktur")
with urllib.request.urlopen(f"http://localhost:{superset_port}/health", timeout=30) as response:
    assert response.status == 200
print("Isolierter Reviewstack: Keycloak-Discovery und Superset-Health sind erreichbar.")
PY

after_ids="$(./scripts/test-keycloak.sh >/dev/null && shasum -a 256 .runtime/dateninfrastruktur-dev-stack/keycloak-identities.json | awk '{print $1}')"
after_project="$(docker compose ps --format '{{.Service}} {{.State}}' | sort)"
[[ "${before_ids}" == "${after_ids}" ]]
[[ "${before_project}" == "${after_project}" ]]
./scripts/smoke-test.sh >/dev/null
echo "Arbeitsinstanz blieb während des parallelen Reviewstacks unverändert und gesund."

cleanup
trap - EXIT

remaining_containers="$(docker ps -a --filter "label=com.docker.compose.project=${PROJECT}" -q | wc -l | tr -d ' ')"
remaining_volumes="$(docker volume ls -q --filter "label=com.docker.compose.project=${PROJECT}" | wc -l | tr -d ' ')"
[[ "${remaining_containers}" == "0" ]]
[[ "${remaining_volumes}" == "0" ]]
echo "Temporärer Reviewstack und seine ausschliesslich eigenen Volumes sind bereinigt."
