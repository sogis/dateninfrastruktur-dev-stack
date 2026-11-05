#!/bin/sh
set -eu
umask 077
dir=$(mktemp -d)
trap 'rm -f "$dir/default.xml" "$dir/loader.xml" "$dir/projector.xml" "$dir/reader.xml" "$dir/users.sql"; rmdir "$dir"' EXIT
write_config() {
    case "$3" in (*[!a-zA-Z0-9._~-]*|'') echo 'Unsupported private ClickHouse setup credential' >&2; exit 1;; esac
    printf '<clickhouse><host>clickhouse</host><user>%s</user><password>%s</password></clickhouse>\n' "$2" "$3" > "$dir/$1.xml"
}
write_config default default "${CLICKHOUSE_DEFAULT_PASSWORD:?}"
write_config loader di_csv_loader "${DI_CH_LOADER_PASSWORD:?}"
write_config projector di_csv_projector "${DI_CH_PROJECTOR_PASSWORD:?}"
write_config reader di_csv_view_reader "${DI_CH_READER_PASSWORD:?}"
client() { clickhouse-client --config-file "$dir/$1.xml" --multiquery; }
cat > "$dir/users.sql" <<SQL
CREATE DATABASE IF NOT EXISTS di_data ENGINE=Atomic;
CREATE DATABASE IF NOT EXISTS di_public_sql ENGINE=Atomic;
CREATE USER IF NOT EXISTS di_csv_loader IDENTIFIED WITH sha256_password BY '${DI_CH_LOADER_PASSWORD}';
CREATE USER IF NOT EXISTS di_csv_projector IDENTIFIED WITH sha256_password BY '${DI_CH_PROJECTOR_PASSWORD}';
CREATE USER IF NOT EXISTS di_csv_view_reader IDENTIFIED WITH sha256_password BY '${DI_CH_READER_PASSWORD}';
SQL
client default < "$dir/users.sql" >/dev/null 2>&1 || { echo 'ClickHouse CSV account preparation failed' >&2; exit 1; }
# Never apply grants to an existing same-named account with unverified credentials.
for account in loader projector reader; do
    printf 'SELECT 1\n' | client "$account" >/dev/null 2>&1 || { echo 'ClickHouse CSV account binding differs' >&2; exit 1; }
done
client default <<'SQL'
GRANT CREATE TABLE, INSERT, SELECT ON di_data.v_* TO di_csv_loader;
GRANT SELECT ON di_data.v_* TO di_csv_projector;
GRANT CREATE VIEW, DROP VIEW, SELECT ON di_public_sql.ds_* TO di_csv_projector;
-- The pinned Atomic engine uses a transient replacement relation for CREATE OR REPLACE VIEW.
GRANT SELECT, DROP TABLE ON di_public_sql._tmp_replace_* TO di_csv_projector;
GRANT CREATE TABLE, INSERT ON di_public_sql.ds_* TO di_csv_projector;
GRANT SELECT ON di_public_sql.ds_* TO di_csv_view_reader;
SQL
echo 'ClickHouse CSV loader, projector and technical view reader ready; Foundation grants retained'
