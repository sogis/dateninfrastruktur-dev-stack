import os
from urllib.parse import quote_plus

SECRET_KEY = os.environ["SUPERSET_SECRET_KEY"]

SQLALCHEMY_DATABASE_URI = (
    "postgresql+psycopg2://"
    f"{quote_plus(os.environ['SUPERSET_DB_USER'])}:"
    f"{quote_plus(os.environ['SUPERSET_DB_PASSWORD'])}@"
    f"{os.environ['SUPERSET_DB_HOST']}:{os.environ['SUPERSET_DB_PORT']}/"
    f"{os.environ['SUPERSET_DB_NAME']}"
)
SQLALCHEMY_TRACK_MODIFICATIONS = False

WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"

ENABLE_PROXY_FIX = False
PUBLIC_ROLE_LIKE = "Gamma"
AUTH_ROLE_PUBLIC = "Public"

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": False,
    "DASHBOARD_RBAC": False,
}
