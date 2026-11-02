#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

skip_build=false
build_only=false
infrastructure_only=false

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --skip-build)
      skip_build=true
      ;;
    --build-only)
      build_only=true
      ;;
    --infrastructure-only|--no-bootstrap)
      infrastructure_only=true
      ;;
    --local-editor|--local-docs|--local-jenkins|--local-sodata)
      # Compatibility switches: the standard path always builds local components.
      ;;
    --registry-only)
      echo "--registry-only ist für diese Grundinstallation deaktiviert." >&2
      echo "Der unterstützte Weg baut ausschliesslich lokale Images aus den neuen Geschwisterrepos." >&2
      exit 2
      ;;
    --help|-h)
      cat <<'EOF'
Usage: ./scripts/up.sh [--skip-build] [--build-only] [--infrastructure-only]

  --skip-build           use already built local images
  --build-only           build Jenkins, Sodata and Superset images, do not start
  --infrastructure-only  start services without seed/publication bootstrap

The standard path builds dateninfrastruktur-jenkins:local,
dateninfrastruktur-sodata:local and dateninfrastruktur-superset:local from the
five sibling repositories, then starts the local stack and runs the idempotent
seed/publication bootstrap.
EOF
      exit 0
      ;;
    *)
      echo "Unbekannte Option: $1" >&2
      exit 2
      ;;
  esac
  shift
done

./scripts/init.sh
set -a
# shellcheck disable=SC1091
source .env
set +a

export COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dateninfrastruktur-dev-stack}"
export RUNTIME_DIR="${RUNTIME_DIR:-.runtime/${COMPOSE_PROJECT_NAME}}"
export GATEWAY_PORT="${GATEWAY_PORT:-18081}"
export GARAGE_S3_PORT="${GARAGE_S3_PORT:-13900}"
export KEYCLOAK_PORT="${KEYCLOAK_PORT:-18080}"
export SUPERSET_PORT="${SUPERSET_PORT:-18088}"
export CLICKHOUSE_HTTP_PORT="${CLICKHOUSE_HTTP_PORT:-18123}"
export CLICKHOUSE_NATIVE_PORT="${CLICKHOUSE_NATIVE_PORT:-19000}"
export JENKINS_IMAGE="${JENKINS_IMAGE:-dateninfrastruktur-jenkins:local}"
export SODATA_IMAGE="${SODATA_IMAGE:-dateninfrastruktur-sodata:local}"
export SUPERSET_IMAGE="${SUPERSET_IMAGE:-dateninfrastruktur-superset:local}"
export SODATA_REPO_DIR="${SODATA_REPO_DIR:-${REPO_DIR}/../dateninfrastruktur-sodata}"

if [[ "${GATEWAY_PORT}" == "8080" ]]; then
  echo "GATEWAY_PORT=8080 kollidiert mit Jenkins im gemeinsamen APISIX-Netzwerkraum." >&2
  exit 1
fi

port_names=(GATEWAY_PORT GARAGE_S3_PORT KEYCLOAK_PORT SUPERSET_PORT CLICKHOUSE_HTTP_PORT CLICKHOUSE_NATIVE_PORT)
for ((left = 0; left < ${#port_names[@]}; left++)); do
  for ((right = left + 1; right < ${#port_names[@]}; right++)); do
    if [[ "${!port_names[left]}" == "${!port_names[right]}" ]]; then
      echo "${port_names[left]} und ${port_names[right]} verwenden beide Hostport ${!port_names[left]}." >&2
      exit 1
    fi
  done
done

if [[ "${skip_build}" == false ]]; then
  ./scripts/build-jenkins-local.sh
  ./scripts/build-sodata-local.sh
  docker compose build superset
fi

if [[ "${build_only}" == true ]]; then
  echo "Images gebaut; Stack wurde nicht gestartet."
  exit 0
fi

compose_up_wait() {
  docker compose up -d --wait --wait-timeout 300 "$@"
}

ensure_public_browser_key() {
  local key_id="${GARAGE_BROWSER_ACCESS_KEY}"
  local private_bucket="ch.so.dateninfrastruktur.private"
  local private_key="private-foundation-smoke.txt"

  echo "Konfiguriere dedizierten Read-only-Schlüssel für den öffentlichen S3-Browser ..."
  if ! docker compose exec -T garage /garage key info "${key_id}" >/dev/null 2>&1; then
    docker compose exec -T garage /garage key import \
      "${key_id}" \
      "${GARAGE_BROWSER_SECRET_KEY}" \
      -n "dateninfrastruktur public browser" \
      --yes >/dev/null
  fi

  docker compose exec -T garage /garage key deny "${key_id}" --create-bucket >/dev/null
  docker compose exec -T garage /garage bucket deny --write --owner ch.so.daten --key "${key_id}" >/dev/null
  docker compose exec -T garage /garage bucket allow --read ch.so.daten --key "${key_id}" >/dev/null
  docker compose exec -T garage /garage bucket deny --read --write --owner "${private_bucket}" --key "${key_id}" >/dev/null 2>&1 || true

  if ! docker compose --profile tools run --rm --no-deps \
    -e AWS_ACCESS_KEY_ID="${key_id}" \
    -e AWS_SECRET_ACCESS_KEY="${GARAGE_BROWSER_SECRET_KEY}" \
    aws s3api head-bucket --bucket ch.so.daten >/dev/null 2>&1; then
    echo "Der Browser-Schlüssel kann den öffentlichen Bucket nicht lesen." >&2
    exit 1
  fi
  if docker compose --profile tools run --rm --no-deps \
    -e AWS_ACCESS_KEY_ID="${key_id}" \
    -e AWS_SECRET_ACCESS_KEY="${GARAGE_BROWSER_SECRET_KEY}" \
    aws s3api head-object --bucket "${private_bucket}" --key "${private_key}" >/dev/null 2>&1; then
    echo "Der öffentliche Browser-Schlüssel kann das private Testobjekt lesen." >&2
    exit 1
  fi
}

sync_local_jenkins_plugin() {
  echo "Synchronisiere lokales GRETL-Plugin ins Jenkins-Volume ..."
  docker compose run \
    --rm \
    --no-deps \
    --no-TTY \
    --user root \
    --entrypoint /bin/sh \
    jenkins \
    -c '
      set -eu
      plugin_dir=/var/jenkins_home/plugins
      image_plugin=/usr/share/jenkins/ref/plugins/jenkins-gretl-datenportal-plugin.jpi
      installed_plugin="$plugin_dir/jenkins-gretl-datenportal-plugin.jpi"

      if [ ! -f "$image_plugin" ]; then
        echo "Plugin aus dem Jenkins-Image nicht gefunden: $image_plugin" >&2
        exit 1
      fi
      mkdir -p "$plugin_dir"
      cp "$image_plugin" "$installed_plugin"
      chown jenkins:jenkins "$plugin_dir" "$installed_plugin"
      rm -f "$plugin_dir/jenkins-gretl-datenportal-plugin.hpi"
      rm -rf "$plugin_dir/jenkins-gretl-datenportal-plugin"
    '
}

echo "Starte Garage und initialisiere Buckets ..."
compose_up_wait garage
docker compose run --rm --no-deps garage-init
ensure_public_browser_key

echo "Starte PostgreSQL und initialisiere getrennte Datenbanken ..."
compose_up_wait postgres
docker compose run --rm --no-deps postgres-init

echo "Starte ClickHouse und initialisiere Testtabellen und Konten ..."
compose_up_wait clickhouse
docker compose run --rm --no-deps clickhouse-init

echo "Starte Keycloak und Superset ..."
compose_up_wait --no-deps keycloak
compose_up_wait --no-deps superset

echo "Starte S3-Browser, Jenkins, APISIX und Portal ..."
compose_up_wait s3-browser
sync_local_jenkins_plugin
docker compose up -d --force-recreate --wait --wait-timeout 300 jenkins downloads

# Sodata requires an existing current.json at startup. The bootstrap starts it
# only after the initial publication was verified, exactly like the source stack.
if [[ "${infrastructure_only}" == false ]]; then
  ./scripts/bootstrap.sh
  compose_up_wait sodata
else
  echo "Infrastrukturmodus: Portalstart und Erstpublikation bleiben aus."
fi

echo
echo "Dateninfrastruktur-Grundinstallation ist gestartet."
echo "Portal/Gateway/Jenkins: http://localhost:${GATEWAY_PORT}/"
echo "Jenkins-Anlieferung:    http://localhost:${GATEWAY_PORT}/anlieferung"
echo "Jenkins-Administration: http://localhost:${GATEWAY_PORT}/jenkins/"
echo "Öffentlicher Bucket:    http://localhost:${GATEWAY_PORT}/ch.so.daten/"
echo "S3 API:                 http://localhost:${GARAGE_S3_PORT}"
echo "Keycloak:               http://localhost:${KEYCLOAK_PORT}"
echo "Superset:               http://localhost:${SUPERSET_PORT}"
echo "ClickHouse HTTP/JDBC:   http://localhost:${CLICKHOUSE_HTTP_PORT}"
if [[ "${infrastructure_only}" == true ]]; then
  echo "Hinweis: Seed, Erstpublikation und Portalbereitschaft wurden nicht ausgeführt."
fi
