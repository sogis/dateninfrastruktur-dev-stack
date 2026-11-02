#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

JENKINS_DEV_DIR="${JENKINS_DEV_DIR:-${REPO_DIR}/../dateninfrastruktur-jenkins-dev}"
PLUGIN_REPO="${PLUGIN_REPO:-${REPO_DIR}/../dateninfrastruktur-jenkins-gretl-plugin}"
THEMEN_REPO_DIR="${THEMEN_REPO_DIR:-${REPO_DIR}/../dateninfrastruktur-themenrepo}"
PLUGIN_SOURCE="${PLUGIN_SOURCE:-local}"
IMAGE_NAME="${IMAGE_NAME:-dateninfrastruktur-jenkins:local}"
IMAGE_VERSION="${IMAGE_VERSION:-local}"

if [[ ! -x "${JENKINS_DEV_DIR}/bin/build-image.sh" ]]; then
  echo "Jenkins-Dev-Buildscript nicht gefunden: ${JENKINS_DEV_DIR}/bin/build-image.sh" >&2
  exit 1
fi
if [[ ! -d "${PLUGIN_REPO}" ]]; then
  echo "Lokales Plugin-Repository nicht gefunden: ${PLUGIN_REPO}" >&2
  echo "PLUGIN_SOURCE=local bricht ohne lokale Pluginquelle bewusst ab." >&2
  exit 1
fi
if [[ ! -d "${THEMEN_REPO_DIR}" ]]; then
  echo "Themenrepo nicht gefunden: ${THEMEN_REPO_DIR}" >&2
  exit 1
fi
if ! git -C "${THEMEN_REPO_DIR}" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "Themenrepo ist keine Git-Arbeitskopie: ${THEMEN_REPO_DIR}" >&2
  exit 1
fi

export THEMEN_REPO_DIR
export PLUGIN_REPO
export PLUGIN_SOURCE
export IMAGE_NAME
export IMAGE_VERSION

# Build the plugin with a supported Jenkins build JDK when SDKMAN is present.
if [[ -z "${JAVA_HOME:-}" && -d "${HOME}/.sdkman/candidates/java/21.0.10-tem" ]]; then
  export JAVA_HOME="${HOME}/.sdkman/candidates/java/21.0.10-tem"
  export PATH="${JAVA_HOME}/bin:${PATH}"
fi

if [[ -n "${PLUGIN_HPI_SOURCE:-}" ]]; then
  export PLUGIN_HPI_SOURCE
fi
if [[ -n "${MAVEN_REPO_LOCAL:-}" ]]; then
  export MAVEN_REPO_LOCAL
fi

echo "Baue lokales Jenkins-Image: ${IMAGE_NAME}"
echo "Jenkins-Dev-Repository: ${JENKINS_DEV_DIR}"
echo "Themenrepo: ${THEMEN_REPO_DIR}"
echo "Plugin-Quelle: ${PLUGIN_SOURCE}"

exec "${JENKINS_DEV_DIR}/bin/build-image.sh"
