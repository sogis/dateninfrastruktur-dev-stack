#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${CLICKHOUSE_TEST_READER_PASSWORD:?./scripts/init.sh ausführen}"
CLICKHOUSE_HTTP_PORT="${CLICKHOUSE_HTTP_PORT:-18123}"
DRIVER_VERSION="0.9.0"
DRIVER_JAR_NAME="clickhouse-jdbc-${DRIVER_VERSION}-all.jar"
DRIVER_URL="https://repo1.maven.org/maven2/com/clickhouse/clickhouse-jdbc/${DRIVER_VERSION}/${DRIVER_JAR_NAME}"
SLF4J_VERSION="2.0.17"
SLF4J_API_URL="https://repo1.maven.org/maven2/org/slf4j/slf4j-api/${SLF4J_VERSION}/slf4j-api-${SLF4J_VERSION}.jar"
SLF4J_SIMPLE_URL="https://repo1.maven.org/maven2/org/slf4j/slf4j-simple/${SLF4J_VERSION}/slf4j-simple-${SLF4J_VERSION}.jar"
RUNTIME_DIR="${RUNTIME_DIR:-.runtime/${COMPOSE_PROJECT_NAME:-dateninfrastruktur-dev-stack}}"
JDBC_DIR="${RUNTIME_DIR}/jdbc"
DRIVER_JAR="${JDBC_DIR}/${DRIVER_JAR_NAME}"
SLF4J_API_JAR="${JDBC_DIR}/slf4j-api-${SLF4J_VERSION}.jar"
SLF4J_SIMPLE_JAR="${JDBC_DIR}/slf4j-simple-${SLF4J_VERSION}.jar"
CLASSES_DIR="${JDBC_DIR}/classes"

mkdir -p "${JDBC_DIR}" "${CLASSES_DIR}"
download_if_missing() {
  local target="$1"
  local url="$2"
  if [[ ! -f "${target}" ]]; then
    curl --fail --silent --show-error --location --output "${target}.tmp" "${url}"
    mv "${target}.tmp" "${target}"
  fi
}
echo "Lade ClickHouse-JDBC-Treiber ${DRIVER_VERSION} ..."
download_if_missing "${DRIVER_JAR}" "${DRIVER_URL}"
download_if_missing "${SLF4J_API_JAR}" "${SLF4J_API_URL}"
download_if_missing "${SLF4J_SIMPLE_JAR}" "${SLF4J_SIMPLE_URL}"

driver_sha256="$(shasum -a 256 "${DRIVER_JAR}" | awk '{print $1}')"
echo "JDBC-Treiber: com.clickhouse:clickhouse-jdbc:${DRIVER_VERSION}:all"
echo "JDBC-Treiber-SHA256: ${driver_sha256}"

javac -cp "${DRIVER_JAR}" -d "${CLASSES_DIR}" scripts/testing/JdbcSmoke.java

java -cp "${DRIVER_JAR}:${SLF4J_API_JAR}:${SLF4J_SIMPLE_JAR}:${CLASSES_DIR}" JdbcSmoke \
  "jdbc:clickhouse://127.0.0.1:${CLICKHOUSE_HTTP_PORT}/foundation" \
  ch_test_reader \
  "${CLICKHOUSE_TEST_READER_PASSWORD}"

echo "JDBC-Zugang über den veröffentlichten Hostport ist geprüft."
