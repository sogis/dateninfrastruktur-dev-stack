#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${KEYCLOAK_ADMIN_PASSWORD:?./scripts/init.sh ausführen}"
KEYCLOAK_PORT="${KEYCLOAK_PORT:-18080}"
RUNTIME_DIR="${RUNTIME_DIR:-.runtime/${COMPOSE_PROJECT_NAME:-dateninfrastruktur-dev-stack}}"
mkdir -p "${RUNTIME_DIR}"

python3 - "${KEYCLOAK_PORT}" "${KEYCLOAK_ADMIN_PASSWORD}" "${RUNTIME_DIR}/keycloak-identities.json" <<'PYTHON'
import json
import sys
import urllib.parse
import urllib.request

port, admin_password, output_path = sys.argv[1:4]
base = f"http://localhost:{port}"
realm = "dateninfrastruktur"

token_request = urllib.request.Request(
    base + "/realms/master/protocol/openid-connect/token",
    data=urllib.parse.urlencode({
        "grant_type": "password",
        "client_id": "admin-cli",
        "username": "admin",
        "password": admin_password,
    }).encode(),
    method="POST",
)
with urllib.request.urlopen(token_request, timeout=20) as response:
    token = json.load(response)["access_token"]

def get(path):
    request = urllib.request.Request(
        base + path, headers={"Authorization": "Bearer " + token})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.load(response)

realm_data = get("/admin/realms/" + realm)
assert realm_data["realm"] == realm
assert realm_data["enabled"] is True

users = get("/admin/realms/" + realm + "/users?briefRepresentation=false&max=100")
by_name = {user["username"]: user for user in users}
expected = {
    "anna": "0b7c9d5e-1f2a-4d3b-8c4e-5f6a7b8c9d01",
    "ben": "1c8d0e6f-2a3b-4c5d-9e6f-7a8b9c0d1e02",
    "claudia": "2d9e1f70-3b4c-5d6e-af70-8b9c0d1e2f03",
}
for username, expected_id in expected.items():
    assert username in by_name, f"Keycloak-Benutzer fehlt: {username}"
    assert by_name[username]["id"] == expected_id, (username, by_name[username]["id"])
    assert by_name[username]["enabled"] is True, username

with urllib.request.urlopen(
        base + "/realms/" + realm + "/.well-known/openid-configuration",
        timeout=20) as response:
    discovery = json.load(response)
expected_issuer = base + "/realms/" + realm
assert discovery["issuer"] == expected_issuer, discovery["issuer"]
assert discovery["jwks_uri"].endswith("/protocol/openid-connect/certs")
with urllib.request.urlopen(discovery["jwks_uri"], timeout=20) as response:
    jwks = json.load(response)
assert jwks.get("keys"), "JWKS enthält keine Schlüssel"

with open(output_path, "w", encoding="utf-8") as output:
    json.dump({name: by_name[name]["id"] for name in expected}, output, indent=2)
    output.write("\n")
print("Keycloak: Realm, drei stabile Benutzer-IDs, Discovery und JWKS sind gültig.")
PYTHON

chmod 600 "${RUNTIME_DIR}/keycloak-identities.json"
echo "Keycloak ist geprüft; Issuer: http://localhost:${KEYCLOAK_PORT}/realms/dateninfrastruktur"
