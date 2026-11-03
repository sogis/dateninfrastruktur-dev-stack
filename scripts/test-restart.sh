#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${CLICKHOUSE_ADMIN_PASSWORD:?./scripts/init.sh ausführen}"
GATEWAY_PORT="${GATEWAY_PORT:-18081}"
RUNTIME_DIR="${RUNTIME_DIR:-.runtime/${COMPOSE_PROJECT_NAME:-dateninfrastruktur-dev-stack}}"
STATE_FILE="${RUNTIME_DIR}/restart-state.json"
mkdir -p "${RUNTIME_DIR}"

ch_admin() {
  docker compose exec -T clickhouse clickhouse-client \
    --host 127.0.0.1 --user "${CLICKHOUSE_ADMIN_USER:-ch_admin}" \
    --password "${CLICKHOUSE_ADMIN_PASSWORD}" "$@"
}

capture_state() {
  local marker="$1"
  local release_id job_count seed_build
  release_id="$(curl --fail --silent --show-error "http://localhost:${GATEWAY_PORT}/ch.so.daten/current.json" | python3 -c 'import json,sys; print(json.load(sys.stdin)["releaseId"])')"
  job_count="$(curl --globoff --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
    "http://localhost:${GATEWAY_PORT}/jenkins/api/json?tree=jobs[name]" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["jobs"]))')"
  seed_build="$(curl --globoff --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
    "http://localhost:${GATEWAY_PORT}/jenkins/job/gretl-datenportal-seed/api/json?tree=lastBuild[number]" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("lastBuild",{}).get("number",0))')"
  python3 - "${STATE_FILE}" "${marker}" "${release_id}" "${job_count}" "${seed_build}" <<'PY'
import hashlib
import json
import os
import sys

state_file, marker, release_id, job_count, seed_build = sys.argv[1:6]
keys = [
    "GARAGE_DEFAULT_ACCESS_KEY", "GARAGE_DEFAULT_SECRET_KEY",
    "GARAGE_BROWSER_ACCESS_KEY", "GARAGE_BROWSER_SECRET_KEY",
    "DATENINFRASTRUKTUR_PORTAL_RELOAD_TOKEN", "POSTGRES_ADMIN_PASSWORD",
    "KEYCLOAK_DB_PASSWORD", "KEYCLOAK_ADMIN_PASSWORD", "KEYCLOAK_DEMO_PASSWORD",
    "SUPERSET_DB_PASSWORD", "SUPERSET_ADMIN_PASSWORD", "SUPERSET_SECRET_KEY",
    "CLICKHOUSE_ADMIN_PASSWORD", "CLICKHOUSE_TEST_READER_PASSWORD",
    "CLICKHOUSE_SUPERSET_READER_PASSWORD", "JENKINS_ADMIN_PASSWORD",
]
state = {
    "marker": marker,
    "release_id": release_id,
    "job_count": int(job_count),
    "seed_build": int(seed_build),
    "secret_digests": {
        key: hashlib.sha256(os.environ.get(key, "").encode()).hexdigest()
        for key in keys
    },
}
with open(state_file, "w", encoding="utf-8") as output:
    json.dump(state, output, indent=2)
    output.write("\n")
os.chmod(state_file, 0o600)
PY
  chmod 600 "${STATE_FILE}"
}

verify_state() {
  local state_file="$1"
  python3 - "${state_file}" "${GATEWAY_PORT}" <<'PY'
import hashlib
import json
import os
import subprocess
import sys
import urllib.request

state_file, gateway_port = sys.argv[1:3]
with open(state_file, encoding="utf-8") as source:
    state = json.load(source)
keys = list(state["secret_digests"])
for key in keys:
    digest = hashlib.sha256(os.environ.get(key, "").encode()).hexdigest()
    assert digest == state["secret_digests"][key], f"Secret geändert: {key}"
with urllib.request.urlopen(
        f"http://localhost:{gateway_port}/ch.so.daten/current.json", timeout=15) as response:
    release_id = json.load(response)["releaseId"]
assert release_id == state["release_id"], (release_id, state["release_id"])
print("Persistenz: Secrets und Release-ID sind unverändert.")
PY

  local job_count seed_build
  job_count="$(curl --globoff --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
    "http://localhost:${GATEWAY_PORT}/jenkins/api/json?tree=jobs[name]" | python3 -c 'import json,sys; print(len(json.load(sys.stdin)["jobs"]))')"
  seed_build="$(curl --globoff --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
    "http://localhost:${GATEWAY_PORT}/jenkins/job/gretl-datenportal-seed/api/json?tree=lastBuild[number]" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("lastBuild",{}).get("number",0))')"
  python3 - "${state_file}" "${job_count}" "${seed_build}" <<'PY'
import json
import sys

state_file, job_count, seed_build = sys.argv[1:4]
with open(state_file, encoding="utf-8") as source:
    state = json.load(source)
assert int(job_count) == state["job_count"], (job_count, state["job_count"])
assert int(seed_build) == state["seed_build"], (seed_build, state["seed_build"])
print("Persistenz: keine neuen Jenkins-Jobs und kein zusätzlicher Seedlauf.")
PY

  local marker
  marker="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["marker"])' "${state_file}")"
  ch_admin --query "SELECT count() FROM foundation.smoke_metrics WHERE metric = '${marker}'" | grep -qx '1'
  ch_admin --query "SELECT count() FROM foundation.smoke_metrics WHERE id IN (1,2,3)" | grep -qx '3'
  ch_admin --query "SELECT count() FROM foundation.restricted_metrics" | grep -qx '1'

  docker compose exec -T -e PGPASSWORD="${SUPERSET_DB_PASSWORD}" postgres \
    psql -U superset -d superset -tAc "SELECT count(*) FROM dbs WHERE database_name = 'clickhouse_foundation'" | grep -qx '1'

  cp "${RUNTIME_DIR}/keycloak-identities.json" "${RUNTIME_DIR}/keycloak-identities.before.json"
  ./scripts/test-keycloak.sh >/dev/null
  cmp -s "${RUNTIME_DIR}/keycloak-identities.before.json" "${RUNTIME_DIR}/keycloak-identities.json"
  rm -f "${RUNTIME_DIR}/keycloak-identities.before.json"
  echo "Persistenz: Keycloak-Benutzer-IDs, Superset-Verbindung und ClickHouse-Testzeile sind erhalten."
}

marker="persistence-$(date +%s)-$$"
ch_admin --query "INSERT INTO foundation.smoke_metrics VALUES (42, '${marker}', 4.2, today())"
capture_state "${marker}"
./scripts/test-keycloak.sh >/dev/null

echo "Stoppe den Stack ohne Volume-Löschung und starte ihn erneut ..."
./scripts/down.sh
./scripts/up.sh --skip-build --no-bootstrap

verify_state "${STATE_FILE}"
echo "Wiederanlauf mit denselben Volumes ist erfolgreich geprüft."
