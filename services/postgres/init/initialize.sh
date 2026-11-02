#!/bin/sh
set -eu

: "${KEYCLOAK_DB_PASSWORD:?KEYCLOAK_DB_PASSWORD is required}"
: "${SUPERSET_DB_PASSWORD:?SUPERSET_DB_PASSWORD is required}"

admin() {
  psql -v ON_ERROR_STOP=1 "$@"
}

ensure_role() {
  role="$1"
  password="$2"
  if [ "$(admin -tAc "SELECT 1 FROM pg_roles WHERE rolname = '${role}'")" != "1" ]; then
    admin -c "CREATE ROLE \"${role}\" LOGIN PASSWORD '${password}' NOSUPERUSER NOCREATEDB NOCREATEROLE"
    echo "PostgreSQL-Rolle ${role} erzeugt."
  else
    echo "PostgreSQL-Rolle ${role} vorhanden; Passwort wird nicht verändert."
  fi
}

ensure_database() {
  database="$1"
  role="$2"
  if [ "$(admin -tAc "SELECT 1 FROM pg_database WHERE datname = '${database}'")" != "1" ]; then
    admin -c "CREATE DATABASE \"${database}\""
    echo "PostgreSQL-Datenbank ${database} erzeugt."
  else
    echo "PostgreSQL-Datenbank ${database} vorhanden."
  fi
  admin -d "${database}" -c "REVOKE ALL ON SCHEMA public FROM PUBLIC"
  admin -d "${database}" -c "GRANT USAGE, CREATE ON SCHEMA public TO \"${role}\""
  admin -d "${database}" -c "REVOKE ALL ON DATABASE \"${database}\" FROM PUBLIC"
  admin -d "${database}" -c "GRANT CONNECT, TEMPORARY ON DATABASE \"${database}\" TO \"${role}\""
  admin -d "${database}" -c "CREATE TABLE IF NOT EXISTS public.foreign_probe (id integer PRIMARY KEY, note text NOT NULL)"
  admin -d "${database}" -c "INSERT INTO public.foreign_probe (id, note) VALUES (1, 'cross-application probe') ON CONFLICT (id) DO NOTHING"
  admin -d "${database}" -c "REVOKE ALL ON TABLE public.foreign_probe FROM PUBLIC"
}

ensure_role keycloak "${KEYCLOAK_DB_PASSWORD}"
ensure_role superset "${SUPERSET_DB_PASSWORD}"
ensure_database keycloak keycloak
ensure_database superset superset

echo "PostgreSQL-Initialisierung abgeschlossen; getrennte Rollen und Datenbanken sind bereit."
