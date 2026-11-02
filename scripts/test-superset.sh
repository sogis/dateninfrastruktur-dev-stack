#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
cd "${REPO_DIR}"

set -a
# shellcheck disable=SC1091
source .env
set +a

: "${SUPERSET_ADMIN_PASSWORD:?./scripts/init.sh ausführen}"
: "${SUPERSET_DB_PASSWORD:?./scripts/init.sh ausführen}"
SUPERSET_PORT="${SUPERSET_PORT:-18088}"

echo "Prüfe Superset-Metadatenbank in PostgreSQL ..."
metadata_user_count="$(docker compose exec -T -e PGPASSWORD="${SUPERSET_DB_PASSWORD}" postgres \
  psql -U superset -d superset -tAc 'SELECT count(*) FROM ab_user')"
[[ "${metadata_user_count}" -ge 1 ]] || { echo "Superset-Metadaten enthalten keinen Benutzer." >&2; exit 1; }
connection_count="$(docker compose exec -T -e PGPASSWORD="${SUPERSET_DB_PASSWORD}" postgres \
  psql -U superset -d superset -tAc "SELECT count(*) FROM dbs WHERE database_name = 'clickhouse_foundation'")"
[[ "${connection_count}" == "1" ]] || { echo "Superset-Verbindung fehlt in PostgreSQL." >&2; exit 1; }

echo "Prüfe Superset-Treiberabfrage über die gespeicherte Verbindung ..."
docker compose exec -T superset python - <<'PYTHON'
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from superset.app import create_app

app = create_app()
with app.app_context():
    from superset import db
    from superset.models.core import Database

    database = (
        db.session.query(Database)
        .filter_by(database_name="clickhouse_foundation")
        .one()
    )
    with database.get_sqla_engine(schema=None) as engine:
        with engine.connect() as connection:
            count = connection.execute(
                text("SELECT count() FROM foundation.smoke_metrics")).scalar()
            assert count is not None and int(count) >= 3, count
            print("Superset-Treiber erlaubte Abfrage: smoke_metrics=" + str(count))
            try:
                connection.execute(text("SELECT count() FROM foundation.restricted_metrics")).scalar()
                raise AssertionError("Superset-Treiber erlaubte restricted_metrics")
            except SQLAlchemyError:
                print("Superset-Treiber verweigerte restricted_metrics.")
PYTHON

echo "Prüfe Superset-Login über den veröffentlichten Port ..."
python3 - "${SUPERSET_PORT}" "${SUPERSET_ADMIN_PASSWORD}" <<'PYTHON'
import http.cookiejar
import re
import sys
import urllib.parse
import urllib.request

port, password = sys.argv[1:3]
base = f"http://localhost:{port}"
jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
with opener.open(base + "/login/", timeout=30) as response:
    html = response.read().decode("utf-8", "replace")
match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
assert match, "Superset-Loginseite enthält kein CSRF-Token"
payload = urllib.parse.urlencode({
    "username": "admin",
    "password": password,
    "csrf_token": match.group(1),
}).encode()
request = urllib.request.Request(base + "/login/", data=payload, method="POST")
with opener.open(request, timeout=30) as response:
    final_url = response.geturl()
    body = response.read().decode("utf-8", "replace")
assert "/superset/welcome" in final_url or "Superset" in body, final_url
with opener.open(base + "/superset/welcome/", timeout=30) as response:
    assert response.status == 200
print("Superset-Login und authentifizierte Startseite sind geprüft.")
PYTHON

echo "Superset-Metadaten, Treiberabfrage und Login sind geprüft."
