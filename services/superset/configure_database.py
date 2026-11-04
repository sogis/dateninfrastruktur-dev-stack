import os
from urllib.parse import quote_plus

from superset.app import create_app


def main():
    user = quote_plus(os.environ["CLICKHOUSE_SUPERSET_USER"])
    password = quote_plus(os.environ["CLICKHOUSE_SUPERSET_PASSWORD"])
    uri = (
        f"clickhousedb+connect://{user}:{password}"
        f"@{os.environ['CLICKHOUSE_HOST']}:{os.environ['CLICKHOUSE_HTTP_PORT']}"
        f"/{os.environ['CLICKHOUSE_DB']}?secure=false"
    )
    app = create_app()
    with app.app_context():
        # Import only after the app initialized the encrypted field factory.
        from superset import db
        from superset.models.core import Database

        database = (
            db.session.query(Database)
            .filter_by(database_name="clickhouse_foundation")
            .one_or_none()
        )
        if database is not None:
            print("Bestehende Superset-Verbindung bleibt unverändert.")
            return
        database = Database(database_name="clickhouse_foundation")
        db.session.add(database)
        database.sqlalchemy_uri = uri
        database.expose_in_sqllab = True
        database.allow_ctas = False
        database.allow_cvas = False
        database.allow_dml = False
        database.allow_run_async = False
        db.session.commit()
        print("Superset-Datenbankverbindung clickhouse_foundation ist gespeichert.")


if __name__ == "__main__":
    main()
