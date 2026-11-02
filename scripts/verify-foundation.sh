#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

./scripts/test-isolation-config.sh
./scripts/smoke-test.sh
./scripts/test-postgres.sh
./scripts/test-keycloak.sh
./scripts/test-clickhouse.sh
./scripts/test-jdbc.sh
./scripts/test-superset.sh
./scripts/test-private-storage.sh

echo "Alle Foundation-Prüfungen sind erfolgreich abgeschlossen."
