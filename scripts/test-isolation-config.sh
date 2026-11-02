#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

COMPOSE_PROJECT_NAME="${COMPOSE_PROJECT_NAME:-dateninfrastruktur-dev-stack}"
RUNTIME_DIR="${RUNTIME_DIR:-.runtime/${COMPOSE_PROJECT_NAME}}"

python3 - "${COMPOSE_PROJECT_NAME}" "${RUNTIME_DIR}" <<'PYTHON'
import json
import os
import subprocess
import sys

project, runtime_dir = sys.argv[1:3]
assert project != "datenportal-dev-stack"
assert project.startswith("dateninfrastruktur-")
assert project in runtime_dir, (project, runtime_dir)

output = subprocess.check_output(
    ["docker", "compose", "ps", "--format", "json"], text=True).strip()
try:
    parsed = json.loads(output)
    services = parsed if isinstance(parsed, list) else [parsed]
except json.JSONDecodeError:
    services = [json.loads(line) for line in output.splitlines() if line.strip()]
assert services, "keine laufenden Compose-Dienste gefunden"

published = []
for service in services:
    name = service.get("Service") or service.get("Name")
    for publisher in service.get("Publishers") or []:
        if publisher.get("PublishedPort"):
            published.append((name, publisher.get("URL"), publisher.get("PublishedPort")))
assert published, "keine veröffentlichten Ports gefunden"
for name, url, port in published:
    assert url in ("127.0.0.1", "::1"), (name, url, port)

assert not any(name == "postgres" for name, _, _ in published), "PostgreSQL hat einen Hostport"

images = subprocess.check_output(
    ["docker", "compose", "images", "--format", "json"], text=True).strip()
try:
    parsed_images = json.loads(images)
    image_rows = parsed_images if isinstance(parsed_images, list) else [parsed_images]
except json.JSONDecodeError:
    image_rows = [json.loads(line) for line in images.splitlines() if line.strip()]
for image in image_rows:
    repository = image.get("Repository", "")
    assert not repository.startswith("sogis/datenportal-"), repository
print("Compose-Isolation: Projekt, Loopback-Ports, PostgreSQL und lokale Images sind geprüft.")
PYTHON

volume_count="$(docker volume ls -q --filter "label=com.docker.compose.project=${COMPOSE_PROJECT_NAME}" | wc -l | tr -d ' ')"
[[ "${volume_count}" -ge 1 ]] || { echo "Keine projektspezifischen Volumes gefunden." >&2; exit 1; }

echo "Instanzspezifische Projektgrenze und Volumes sind geprüft."
