#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${ENV_FILE:-${REPO_DIR}/.env}"
ENV_EXAMPLE="${REPO_DIR}/.env.example"

if ! command -v openssl >/dev/null 2>&1; then
  echo "openssl wird für die lokalen Zufallswerte benötigt." >&2
  exit 1
fi

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${ENV_EXAMPLE}" "${ENV_FILE}"
  chmod 600 "${ENV_FILE}"
  echo "Lokale Env-Datei aus .env.example erzeugt."
fi

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dateninfrastruktur-dev-stack}"
RUNTIME_DIR="${RUNTIME_DIR:-.runtime/${COMPOSE_PROJECT_NAME}}"
case "${RUNTIME_DIR}" in
  /*) ;;
  *) RUNTIME_DIR="${REPO_DIR}/${RUNTIME_DIR}" ;;
esac

if ! grep -q '^COMPOSE_PROJECT_NAME=' "${ENV_FILE}"; then
  printf '\nCOMPOSE_PROJECT_NAME=%s\n' "${COMPOSE_PROJECT_NAME}" >> "${ENV_FILE}"
fi
if ! grep -q '^RUNTIME_DIR=' "${ENV_FILE}"; then
  # Store a repository-relative path so the same env file remains relocatable.
  relative_runtime="${RUNTIME_DIR#${REPO_DIR}/}"
  printf '\nRUNTIME_DIR=%s\n' "${relative_runtime}" >> "${ENV_FILE}"
fi

ensure_secret() {
  local name="$1"
  local bytes="${2:-24}"
  local current="${!name:-}"
  if [[ -n "${current}" ]]; then
    return 0
  fi

  local value
  value="$(openssl rand -hex "${bytes}")"
  if grep -q "^${name}=" "${ENV_FILE}"; then
    local tmp
    tmp="$(mktemp "${RUNTIME_DIR:-${TMPDIR:-/tmp}}/env.XXXXXX")"
    sed "s|^${name}=.*|${name}=${value}|" "${ENV_FILE}" > "${tmp}"
    chmod 600 "${tmp}"
    mv "${tmp}" "${ENV_FILE}"
  else
    printf '%s=%s\n' "${name}" "${value}" >> "${ENV_FILE}"
  fi
  export "${name}=${value}"
}

ensure_key() {
  local name="$1"
  local current="${!name:-}"
  if [[ -n "${current}" ]]; then
    return 0
  fi
  local value="GK$(openssl rand -hex 16)"
  if grep -q "^${name}=" "${ENV_FILE}"; then
    local tmp
    tmp="$(mktemp "${RUNTIME_DIR:-${TMPDIR:-/tmp}}/env.XXXXXX")"
    sed "s|^${name}=.*|${name}=${value}|" "${ENV_FILE}" > "${tmp}"
    chmod 600 "${tmp}"
    mv "${tmp}" "${ENV_FILE}"
  else
    printf '%s=%s\n' "${name}" "${value}" >> "${ENV_FILE}"
  fi
  export "${name}=${value}"
}

mkdir -p "${RUNTIME_DIR}"
chmod 700 "${RUNTIME_DIR}"

migrate_datenportal_env_keys() {
  local old_keys
  old_keys="$(grep -oE '^DATENPORTAL_[A-Z0-9_]+' "${ENV_FILE}" | sort -u || true)"
  [[ -n "${old_keys}" ]] || return 0

  local old_key new_key tmp
  while IFS= read -r old_key; do
    new_key="DATENINFRASTRUKTUR_${old_key#DATENPORTAL_}"
    tmp="$(mktemp "${RUNTIME_DIR}/env-migrate.XXXXXX")"
    if grep -q "^${new_key}=" "${ENV_FILE}"; then
      # The new key already exists. Keep it and drop the obsolete duplicate.
      sed "/^${old_key}=/d" "${ENV_FILE}" > "${tmp}"
    else
      sed "s|^${old_key}=|${new_key}=|" "${ENV_FILE}" > "${tmp}"
    fi
    chmod 600 "${tmp}"
    mv "${tmp}" "${ENV_FILE}"
  done <<< "${old_keys}"
  echo "Lokale DATENPORTAL_*-Variablen auf DATENINFRASTRUKTUR_* migriert."
}

migrate_datenportal_env_keys
set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a
chmod 600 "${ENV_FILE}"

ensure_key GARAGE_DEFAULT_ACCESS_KEY
ensure_secret GARAGE_DEFAULT_SECRET_KEY 32
ensure_key GARAGE_BROWSER_ACCESS_KEY
ensure_secret GARAGE_BROWSER_SECRET_KEY 32
ensure_secret PRIVATE_TEST_OBJECT_ID 16
ensure_secret DATENINFRASTRUKTUR_PORTAL_RELOAD_TOKEN 32
ensure_secret POSTGRES_ADMIN_PASSWORD 24
ensure_secret KEYCLOAK_DB_PASSWORD 24
ensure_secret KEYCLOAK_ADMIN_PASSWORD 24
ensure_secret KEYCLOAK_DEMO_PASSWORD 24
ensure_secret SUPERSET_DB_PASSWORD 24
ensure_secret SUPERSET_ADMIN_PASSWORD 24
ensure_secret SUPERSET_SECRET_KEY 32
ensure_secret CLICKHOUSE_ADMIN_PASSWORD 24
ensure_secret CLICKHOUSE_DEFAULT_PASSWORD 24
ensure_secret CLICKHOUSE_TEST_READER_PASSWORD 24
ensure_secret CLICKHOUSE_SUPERSET_READER_PASSWORD 24
ensure_secret JENKINS_ADMIN_PASSWORD 24

chmod 600 "${ENV_FILE}"

CONFIG_TEMPLATE="${REPO_DIR}/services/garage/garage.toml.template"
CONFIG_FILE="${RUNTIME_DIR}/garage.toml"
if [[ ! -f "${CONFIG_FILE}" ]]; then
  umask 077
  sed \
    -e "s/__RPC_SECRET__/$(openssl rand -hex 32)/" \
    -e "s/__ADMIN_TOKEN__/$(openssl rand -hex 32)/" \
    -e "s/__METRICS_TOKEN__/$(openssl rand -hex 32)/" \
    "${CONFIG_TEMPLATE}" > "${CONFIG_FILE}"
  chmod 600 "${CONFIG_FILE}"
  echo "Lokale Garage-Konfiguration erzeugt."
fi
chmod 600 "${CONFIG_FILE}"

REALM_TEMPLATE="${REPO_DIR}/services/keycloak/realm-template.json"
REALM_FILE="${RUNTIME_DIR}/keycloak-realm.json"
umask 077
python3 - "${REALM_TEMPLATE}" "${REALM_FILE}" "${KEYCLOAK_DEMO_PASSWORD}" <<'PY'
import json
import sys

template, target, password = sys.argv[1:4]
with open(template, encoding="utf-8") as source:
    realm = json.load(source)
for user in realm.get("users", []):
    for credential in user.get("credentials", []):
        if credential.get("value") == "__DEMO_PASSWORD__":
            credential["value"] = password
with open(target, "w", encoding="utf-8") as output:
    json.dump(realm, output, indent=2, ensure_ascii=False)
    output.write("\n")
PY
chmod 600 "${REALM_FILE}"

echo "Lokale Konfiguration bereit: ${ENV_FILE} (Werte nicht ausgegeben)."
