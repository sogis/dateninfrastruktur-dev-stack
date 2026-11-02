#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${POSTGRES_ADMIN_PASSWORD:?./scripts/init.sh ausführen}"
: "${KEYCLOAK_DB_PASSWORD:?./scripts/init.sh ausführen}"
: "${SUPERSET_DB_PASSWORD:?./scripts/init.sh ausführen}"

admin_psql() {
  docker compose exec -T -e PGPASSWORD="${POSTGRES_ADMIN_PASSWORD}" postgres \
    psql -U postgres -v ON_ERROR_STOP=1 "$@"
}

echo "Prüfe getrennte PostgreSQL-Rollen ohne Superuser-Rechte ..."
attributes="$(admin_psql -tAc "SELECT rolname || ':' || rolsuper || ':' || rolcreatedb || ':' || rolcreaterole FROM pg_roles WHERE rolname IN ('keycloak','superset') ORDER BY rolname")"
[[ "${attributes}" == $'keycloak:false:false:false\nsuperset:false:false:false' ]] || {
  echo "Unerwartete Rollenattribute: ${attributes}" >&2
  exit 1
}

echo "Prüfe vorhandene fremde Testtabellen ..."
admin_psql -d keycloak -tAc "SELECT count(*) FROM public.foreign_probe" | grep -qx '1'
admin_psql -d superset -tAc "SELECT count(*) FROM public.foreign_probe" | grep -qx '1'

echo "Prüfe verweigerte Fremdzugriffe auf Datenbank- und Tabellenebene ..."
if docker compose exec -T -e PGPASSWORD="${SUPERSET_DB_PASSWORD}" postgres \
  psql -U superset -d keycloak -c 'SELECT 1' >/dev/null 2>&1; then
  echo "Superset-Rolle konnte sich mit der Keycloak-Datenbank verbinden." >&2
  exit 1
fi
if docker compose exec -T -e PGPASSWORD="${KEYCLOAK_DB_PASSWORD}" postgres \
  psql -U keycloak -d superset -c 'SELECT 1' >/dev/null 2>&1; then
  echo "Keycloak-Rolle konnte sich mit der Superset-Datenbank verbinden." >&2
  exit 1
fi
if docker compose exec -T -e PGPASSWORD="${SUPERSET_DB_PASSWORD}" postgres \
  psql -U superset -d superset -c 'SELECT * FROM public.foreign_probe' >/dev/null 2>&1; then
  echo "Superset-Rolle konnte die fremde Testtabelle lesen." >&2
  exit 1
fi
if docker compose exec -T -e PGPASSWORD="${KEYCLOAK_DB_PASSWORD}" postgres \
  psql -U keycloak -d keycloak -c 'SELECT * FROM public.foreign_probe' >/dev/null 2>&1; then
  echo "Keycloak-Rolle konnte die fremde Testtabelle lesen." >&2
  exit 1
fi

echo "PostgreSQL-Rollentrennung und Negativzugriffe sind geprüft."
