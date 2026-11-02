#!/usr/bin/env bash
set -euo pipefail

cd /app

for attempt in $(seq 1 60); do
  if superset db upgrade; then
    break
  fi
  if [ "$attempt" -eq 60 ]; then
    echo "Superset-Metadatenbank ist nach 60 Versuchen nicht migrierbar." >&2
    exit 1
  fi
  echo "Warte auf Superset-Metadatenbank (Versuch ${attempt}/60) ..."
  sleep 2
done

superset init

python - <<'PY'
import os

from flask_appbuilder.security.sqla.models import User
from superset import db
from superset.app import create_app

app = create_app()
with app.app_context():
    sm = app.appbuilder.sm
    username = os.environ["SUPERSET_ADMIN_USERNAME"]
    user = db.session.query(User).filter_by(username=username).one_or_none()
    if user is None:
        role = sm.find_role(sm.auth_role_admin)
        if role is None:
            role = sm.add_role(sm.auth_role_admin)
        sm.add_user(
            username=username,
            first_name="Local",
            last_name="Administrator",
            email=os.environ["SUPERSET_ADMIN_EMAIL"],
            role=role,
            password=os.environ["SUPERSET_ADMIN_PASSWORD"],
        )
        print("Lokaler Superset-Administrator erzeugt.")
    else:
        print("Lokaler Superset-Administrator vorhanden; Passwort bleibt unverändert.")
PY

python /usr/local/bin/configure_database.py

exec gunicorn \
  --bind 0.0.0.0:8088 \
  --workers 2 \
  --worker-class gthread \
  --threads 4 \
  --timeout 120 \
  "superset.app:create_app()"
