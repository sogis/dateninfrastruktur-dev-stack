#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

if [[ ! -f .env ]]; then
  echo "Zuerst ./scripts/init.sh und ./scripts/up.sh ausführen." >&2
  exit 1
fi

set -a
# shellcheck disable=SC1091
source .env
set +a

GATEWAY_PORT="${GATEWAY_PORT:-18081}"
GARAGE_S3_PORT="${GARAGE_S3_PORT:-13900}"
PUBLIC_URL="http://localhost:${GATEWAY_PORT}/ch.so.daten"
JENKINS_URL="http://localhost:${GATEWAY_PORT}/jenkins"
SODATA_URL="http://localhost:${GATEWAY_PORT}"
SMOKE_KEY="_foundation-smoke/$$-$(date +%s).txt"
ROOT_SMOKE_KEY="_foundation-smoke-$$-$(date +%s).txt"
DENIED_KEY="_foundation-smoke/denied-$$-$(date +%s).txt"
SMOKE_TEXT="Dateninfrastruktur Foundation smoke test $$"
SMOKE_FILE="$(mktemp "${TMPDIR:-/tmp}/foundation-smoke.XXXXXX")"

: "${GARAGE_BROWSER_ACCESS_KEY:?./scripts/init.sh ausführen}"
: "${GARAGE_BROWSER_SECRET_KEY:?./scripts/init.sh ausführen}"
: "${JENKINS_ADMIN_PASSWORD:?./scripts/init.sh ausführen}"

browser_aws() {
  docker compose --profile tools run \
    --rm \
    --no-deps \
    -e AWS_ACCESS_KEY_ID="${GARAGE_BROWSER_ACCESS_KEY}" \
    -e AWS_SECRET_ACCESS_KEY="${GARAGE_BROWSER_SECRET_KEY}" \
    aws "$@"
}

cleanup() {
  docker compose --profile tools run --rm --no-deps aws \
    s3api delete-object --bucket ch.so.daten --key "${SMOKE_KEY}" >/dev/null 2>&1 || true
  docker compose --profile tools run --rm --no-deps aws \
    s3api delete-object --bucket ch.so.daten --key "${ROOT_SMOKE_KEY}" >/dev/null 2>&1 || true
  docker compose --profile tools run --rm --no-deps aws \
    s3api delete-object --bucket ch.so.daten --key "${DENIED_KEY}" >/dev/null 2>&1 || true
  rm -f "${SMOKE_FILE}"
}
trap cleanup EXIT

printf '%s\n' "${SMOKE_TEXT}" > "${SMOKE_FILE}"

echo "Prüfe Bucket und authentifizierten S3-Upload ..."
docker compose --profile tools run --rm --no-deps aws \
  s3api head-bucket --bucket ch.so.daten >/dev/null
docker compose --profile tools run --rm --no-deps \
  -v "${SMOKE_FILE}:/tmp/smoke-object:ro" \
  aws s3 cp /tmp/smoke-object "s3://ch.so.daten/${SMOKE_KEY}" >/dev/null
docker compose --profile tools run --rm --no-deps \
  -v "${SMOKE_FILE}:/tmp/smoke-object:ro" \
  aws s3 cp /tmp/smoke-object "s3://ch.so.daten/${ROOT_SMOKE_KEY}" >/dev/null

echo "Prüfe öffentlichen Leseschlüssel (Lesen erlaubt, Schreiben verboten) ..."
browser_downloaded="$(browser_aws s3 cp "s3://ch.so.daten/${SMOKE_KEY}" -)"
[[ "${browser_downloaded}" == "${SMOKE_TEXT}" ]]
if docker compose --profile tools run --rm --no-deps \
  -e AWS_ACCESS_KEY_ID="${GARAGE_BROWSER_ACCESS_KEY}" \
  -e AWS_SECRET_ACCESS_KEY="${GARAGE_BROWSER_SECRET_KEY}" \
  -v "${SMOKE_FILE}:/tmp/browser-write:ro" \
  aws s3 cp /tmp/browser-write "s3://ch.so.daten/${DENIED_KEY}" >/dev/null 2>&1; then
  echo "Der öffentliche Browser-Schlüssel konnte schreiben." >&2
  exit 1
fi

echo "Prüfe anonymen öffentlichen Download, Range und CORS ..."
downloaded="$(curl --fail --silent --show-error "${PUBLIC_URL}/${SMOKE_KEY}")"
[[ "${downloaded}" == "${SMOKE_TEXT}" ]]
range_status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
  -H 'Range: bytes=0-3' "${PUBLIC_URL}/${SMOKE_KEY}")"
[[ "${range_status}" == "206" ]]
python3 - "${PUBLIC_URL}/${SMOKE_KEY}" <<'PYTHON'
import sys
import urllib.request
request = urllib.request.Request(
    sys.argv[1], headers={"Range": "bytes=0-3", "Origin": "https://daten.so.ch"})
with urllib.request.urlopen(request, timeout=15) as response:
    assert response.read() == b"Date"
    assert response.headers["Content-Range"].startswith("bytes 0-3/")
    assert response.headers["Access-Control-Allow-Origin"] == "*"
PYTHON

echo "Prüfe öffentliche Verzeichnisliste ..."
root_listing="$(curl --fail --silent --show-error "${PUBLIC_URL}/")"
grep -Fq "${ROOT_SMOKE_KEY}" <<<"${root_listing}"
listing="$(curl --fail --silent --show-error "${PUBLIC_URL}/_foundation-smoke/")"
grep -Fq "${SMOKE_KEY##*/}" <<<"${listing}"

echo "Prüfe administrative Gateway-Sperren ..."
python3 - "$SODATA_URL" <<'PYTHON'
import sys
import urllib.error
import urllib.request

base = sys.argv[1]

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None

opener = urllib.request.build_opener(NoRedirect)
for path in ["/admin", "/admin/catalog/status", "/admin/catalog/reload",
             "/actuator", "/actuator/health", "/apisix/admin/routes"]:
    for method in ["GET", "POST"]:
        for headers in [{}, {"X-Reload-Token": "invalid-smoke-token"}]:
            request = urllib.request.Request(base + path, method=method, headers=headers)
            try:
                response = opener.open(request, timeout=10)
            except urllib.error.HTTPError as error:
                response = error
            assert response.code == 403, (path, method, response.code)
PYTHON

docker compose exec -T jenkins bash -s -- "${SODATA_URL}" <<'SH'
set -euo pipefail
: "${ORG_GRADLE_PROJECT_portalReloadToken:?reload token missing}"
for endpoint in status reload; do
  method=GET
  [[ "$endpoint" != reload ]] || method=POST
  code=$(printf 'X-Reload-Token: %s\n' "$ORG_GRADLE_PROJECT_portalReloadToken" |
    curl --silent --show-error --output /dev/null --write-out '%{http_code}' \
      --header @- --request "$method" "$1/admin/catalog/$endpoint")
  [[ "$code" == "403" ]] || { echo "Öffentlicher $endpoint mit gültigem Token lieferte $code" >&2; exit 1; }
done
SH

echo "Prüfe Jenkins-Anmeldung, Plugin und Seedjob ..."
curl --fail --silent --show-error "${JENKINS_URL}/login" -o /dev/null
curl --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
  "${JENKINS_URL}/api/json" >/dev/null
plugins="$(curl --globoff --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
  "${JENKINS_URL}/pluginManager/api/json?depth=1&tree=plugins[shortName,version,active]")"
python3 - "${plugins}" <<'PYTHON'
import json
import sys

data = json.loads(sys.argv[1])
matches = [p for p in data["plugins"] if p["shortName"] == "jenkins-gretl-dateninfrastruktur-plugin"]
assert matches, "lokal gebautes GRETL-Plugin ist nicht installiert"
assert matches[0]["active"] is True, "GRETL-Plugin ist nicht aktiv"
PYTHON
seed="$(curl --globoff --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
  "${JENKINS_URL}/job/gretl-datenportal-seed/api/json?tree=name,lastBuild[result]")"
python3 - "${seed}" <<'PYTHON'
import json
import sys

data = json.loads(sys.argv[1])
assert data["name"] == "gretl-datenportal-seed"
assert data.get("lastBuild", {}).get("result") == "SUCCESS", "Seedjob war nicht erfolgreich"
PYTHON

echo "Prüfe Startformular und seine statischen Ressourcen ..."
form_html="$(curl --fail --silent --show-error --user "admin:${JENKINS_ADMIN_PASSWORD}" \
  "${JENKINS_URL}/gretl-datenportal/")"
python3 - "$form_html" "$JENKINS_URL" "$JENKINS_ADMIN_PASSWORD" <<'PYTHON'
import base64
import re
import sys
import urllib.parse
import urllib.request

html, base, password = sys.argv[1:4]
assets = re.findall(r'(?:src|href)="([^"]+\.(?:css|js))"', html)
assert assets, "Startformular enthält keine CSS-/JS-Ressourcen"
authorization = "Basic " + base64.b64encode(("admin:" + password).encode()).decode()
for asset in sorted(set(assets)):
    url = urllib.parse.urljoin(base + "/", asset)
    request = urllib.request.Request(url, headers={"Authorization": authorization})
    with urllib.request.urlopen(request, timeout=15) as response:
        assert response.status == 200, (url, response.status)
PYTHON

echo "Prüfe Portal-Manifest, DuckDB und Readiness ..."
if ! curl --fail --silent --show-error --max-time 5 "${PUBLIC_URL}/current.json" >/dev/null; then
  echo "current.json fehlt; Erstpublikation prüfen." >&2
  exit 1
fi
docker compose exec -T jenkins curl --fail --silent --show-error http://sodata:8080/actuator/health -o /dev/null
curl --fail --silent --show-error "${SODATA_URL}/" -o /dev/null
python3 - "${PUBLIC_URL}" "${SODATA_URL}" <<'PYTHON'
import hashlib
import json
import sys
import urllib.request

sys.path.insert(0, "scripts/testing")
from importlib import import_module

validate = import_module("check-publication-manifest").validate
public, portal = sys.argv[1:3]
with urllib.request.urlopen(public + "/current.json", timeout=15) as response:
    manifest = validate(json.load(response))
with urllib.request.urlopen(public + "/" + manifest["duckdb"], timeout=30) as response:
    published = response.read()
with urllib.request.urlopen(portal + "/catalog/catalog.duckdb", timeout=30) as response:
    active = response.read()
assert published == active, "Portal-DuckDB entspricht nicht dem veröffentlichten Stand"
assert active[8:12] == b"DUCK"
with urllib.request.urlopen(
        portal + "/catalog/catalog.duckdb?v=" + hashlib.sha256(active).hexdigest(),
        timeout=30) as response:
    assert response.read() == active
PYTHON

echo "Prüfe entfernte Editor-/Dokumentationspfade ..."
for path in /datenblatt-editor/ /dokumentation/ /metadaten-editor/; do
  status="$(curl --silent --show-error --output /dev/null --write-out '%{http_code}' "${SODATA_URL}${path}")"
  [[ "${status}" != "200" ]] || { echo "${path} ist noch öffentlich erreichbar." >&2; exit 1; }
done

echo "Smoke-Test erfolgreich: Gateway, S3, Jenkins, Seed, Formular und Portal sind geprüft."
