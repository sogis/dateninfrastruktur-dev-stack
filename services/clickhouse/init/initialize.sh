#!/bin/sh
set -eu

: "${CLICKHOUSE_DEFAULT_PASSWORD:?CLICKHOUSE_DEFAULT_PASSWORD is required}"
: "${CLICKHOUSE_ADMIN_USER:?CLICKHOUSE_ADMIN_USER is required}"
: "${CLICKHOUSE_ADMIN_PASSWORD:?CLICKHOUSE_ADMIN_PASSWORD is required}"
: "${CLICKHOUSE_TEST_READER_PASSWORD:?CLICKHOUSE_TEST_READER_PASSWORD is required}"
: "${CLICKHOUSE_SUPERSET_READER_PASSWORD:?CLICKHOUSE_SUPERSET_READER_PASSWORD is required}"

client() {
  CLICKHOUSE_USER=default CLICKHOUSE_PASSWORD="$CLICKHOUSE_DEFAULT_PASSWORD" \
    clickhouse-client --host "${CLICKHOUSE_HOST:-clickhouse}" "$@"
}

sql() {
  client --multiquery
}

sql <<'SQL'
CREATE DATABASE IF NOT EXISTS foundation;

CREATE TABLE IF NOT EXISTS foundation.smoke_metrics
(
    id UInt8,
    metric String,
    value Float64,
    observed_at Date
)
ENGINE = MergeTree
ORDER BY id;

CREATE TABLE IF NOT EXISTS foundation.restricted_metrics
(
    id UInt8,
    metric String,
    value Float64,
    observed_at Date
)
ENGINE = MergeTree
ORDER BY id;

CREATE ROLE IF NOT EXISTS foundation_reader;
GRANT SELECT ON foundation.smoke_metrics TO foundation_reader;
SQL

if [ "${DI_TEST_FIXTURE:-false}" = true ]; then
  sql <<'SQL'
INSERT INTO foundation.smoke_metrics
SELECT * FROM
(
    SELECT 1 AS id, 'alpha' AS metric, 1.5 AS value, toDate('2026-01-01') AS observed_at
    UNION ALL
    SELECT 2, 'beta', 2.5, toDate('2026-01-02')
    UNION ALL
    SELECT 3, 'gamma', 3.5, toDate('2026-01-03')
)
WHERE NOT EXISTS (SELECT 1 FROM foundation.smoke_metrics);

INSERT INTO foundation.restricted_metrics
SELECT * FROM
(
    SELECT 1 AS id, 'restricted' AS metric, 9.9 AS value, toDate('2026-01-01') AS observed_at
)
WHERE NOT EXISTS (SELECT 1 FROM foundation.restricted_metrics);
SQL
fi

# Passwords are written to a temporary SQL file and fed through stdin; they
# do not become command-line arguments in the container process list.
umask 077
cat > /tmp/clickhouse-init-users.sql <<SQL
CREATE USER IF NOT EXISTS ${CLICKHOUSE_ADMIN_USER} IDENTIFIED WITH sha256_password BY '${CLICKHOUSE_ADMIN_PASSWORD}';
CREATE USER IF NOT EXISTS ch_test_reader IDENTIFIED WITH sha256_password BY '${CLICKHOUSE_TEST_READER_PASSWORD}';
CREATE USER IF NOT EXISTS superset_reader IDENTIFIED WITH sha256_password BY '${CLICKHOUSE_SUPERSET_READER_PASSWORD}';
GRANT foundation_reader TO ch_test_reader, superset_reader;
GRANT ALL ON foundation.* TO ${CLICKHOUSE_ADMIN_USER} WITH GRANT OPTION;
GRANT ACCESS MANAGEMENT ON *.* TO ${CLICKHOUSE_ADMIN_USER};
ALTER USER ch_test_reader ADD PROFILES 'foundation_reader_profile';
ALTER USER superset_reader ADD PROFILES 'foundation_reader_profile';
CREATE QUOTA IF NOT EXISTS foundation_reader_quota FOR INTERVAL 1 hour MAX queries = 1000, errors = 100, result_rows = 1000000, read_rows = 100000000, execution_time = 3600 TO ch_test_reader, superset_reader;
SQL
if [ -n "${DI_CH_LOADER_PASSWORD:-}" ]; then
  cat >> /tmp/clickhouse-init-users.sql <<SQL
CREATE USER IF NOT EXISTS ch_delivery IDENTIFIED WITH sha256_password BY '${DI_CH_LOADER_PASSWORD}';
GRANT CREATE TABLE, INSERT, SELECT ON default.snapshot_* TO ch_delivery;
SQL
fi
client --multiquery < /tmp/clickhouse-init-users.sql
rm -f /tmp/clickhouse-init-users.sql

verify_login() {
  if ! CLICKHOUSE_USER="$1" CLICKHOUSE_PASSWORD="$2" \
    clickhouse-client --host "${CLICKHOUSE_HOST:-clickhouse}" --query 'SELECT 1' >/dev/null 2>&1; then
    echo "ClickHouse credentials for $1 do not match the configured user." >&2
    exit 1
  fi
}

verify_login "$CLICKHOUSE_ADMIN_USER" "$CLICKHOUSE_ADMIN_PASSWORD"
verify_login ch_test_reader "$CLICKHOUSE_TEST_READER_PASSWORD"
verify_login superset_reader "$CLICKHOUSE_SUPERSET_READER_PASSWORD"
if [ -n "${DI_CH_LOADER_PASSWORD:-}" ]; then
  verify_login ch_delivery "$DI_CH_LOADER_PASSWORD"
fi

client --query "SELECT 'smoke_metrics=' || toString(count()) FROM foundation.smoke_metrics"
client --query "SELECT 'restricted_metrics=' || toString(count()) FROM foundation.restricted_metrics"

echo "ClickHouse-Initialisierung abgeschlossen."
