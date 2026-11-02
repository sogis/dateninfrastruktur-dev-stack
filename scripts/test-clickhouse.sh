#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

ADMIN_USER="${CLICKHOUSE_ADMIN_USER:-ch_admin}"
: "${CLICKHOUSE_ADMIN_PASSWORD:?./scripts/init.sh ausführen}"
: "${CLICKHOUSE_TEST_READER_PASSWORD:?./scripts/init.sh ausführen}"
: "${CLICKHOUSE_SUPERSET_READER_PASSWORD:?./scripts/init.sh ausführen}"
CLICKHOUSE_HTTP_PORT="${CLICKHOUSE_HTTP_PORT:-18123}"

ch() {
  local user="$1"
  local password="$2"
  shift 2
  docker compose exec -T clickhouse clickhouse-client \
    --host 127.0.0.1 --user "${user}" --password "${password}" "$@"
}

expect_denied() {
  local label="$1"
  shift
  local output
  if output="$("$@" 2>&1)"; then
    echo "${label}: Zugriff wurde unerwartet erlaubt." >&2
    exit 1
  fi
  if ! grep -Eiq 'access denied|not enough privileges|necessary to have grant|readonly|authentication failed|invalid password' <<<"${output}"; then
    echo "${label}: Fehler ist kein Berechtigungs-/Authentifizierungsfehler." >&2
    printf '%s\n' "${output}" | tail -5 >&2
    exit 1
  fi
}

echo "Prüfe deterministische ClickHouse-Testzeilen ..."
smoke_count="$(ch "${ADMIN_USER}" "${CLICKHOUSE_ADMIN_PASSWORD}" --query 'SELECT count() FROM foundation.smoke_metrics')"
restricted_count="$(ch "${ADMIN_USER}" "${CLICKHOUSE_ADMIN_PASSWORD}" --query 'SELECT count() FROM foundation.restricted_metrics')"
[[ "${smoke_count}" -ge 3 ]] || { echo "smoke_metrics enthält nur ${smoke_count} Zeilen." >&2; exit 1; }
[[ "${restricted_count}" -ge 1 ]] || { echo "restricted_metrics fehlt." >&2; exit 1; }

for reader in "ch_test_reader:${CLICKHOUSE_TEST_READER_PASSWORD}" "superset_reader:${CLICKHOUSE_SUPERSET_READER_PASSWORD}"; do
  user="${reader%%:*}"
  password="${reader#*:}"
  echo "Prüfe technischen Leser ${user} ..."
  allowed="$(ch "${user}" "${password}" --query 'SELECT count() FROM foundation.smoke_metrics')"
  [[ "${allowed}" -ge 3 ]] || { echo "${user} kann smoke_metrics nicht lesen." >&2; exit 1; }

  expect_denied "${user}: restricted_metrics" \
    ch "${user}" "${password}" --query 'SELECT count() FROM foundation.restricted_metrics'
  expect_denied "${user}: INSERT" \
    ch "${user}" "${password}" --query "INSERT INTO foundation.smoke_metrics VALUES (99, 'denied', 0, today())"
  expect_denied "${user}: DDL" \
    ch "${user}" "${password}" --query 'CREATE TABLE foundation.denied_table (id UInt8) ENGINE = Memory'
  expect_denied "${user}: GRANT" \
    ch "${user}" "${password}" --query 'GRANT SELECT ON foundation.restricted_metrics TO ch_test_reader'
done

echo "Prüfe anonymen und falschen ClickHouse-Zugang ..."
status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  "http://localhost:${CLICKHOUSE_HTTP_PORT}/?query=SELECT%201")"
[[ "${status}" == "401" || "${status}" == "403" ]] || { echo "Anonymer HTTP-Zugang lieferte ${status}." >&2; exit 1; }
expect_denied "falsches Passwort" \
  ch ch_test_reader "definitely-wrong-password" --query 'SELECT 1'

echo "ClickHouse-Rechte und Testdaten sind geprüft."
