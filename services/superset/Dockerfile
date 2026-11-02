ARG SUPERSET_VERSION=6.1.0
FROM apache/superset:${SUPERSET_VERSION}

ARG CLICKHOUSE_CONNECT_VERSION=1.11.0
ARG PSYCOPG2_VERSION=2.9.13

USER root
RUN uv pip install --no-cache --python /app/.venv/bin/python \
        "clickhouse-connect==${CLICKHOUSE_CONNECT_VERSION}" \
        "psycopg2-binary==${PSYCOPG2_VERSION}"
COPY superset_config.py /app/pythonpath/superset_config.py
COPY initialize-superset.sh /usr/local/bin/initialize-superset.sh
COPY configure_database.py /usr/local/bin/configure_database.py
RUN chmod 0755 /usr/local/bin/initialize-superset.sh /usr/local/bin/configure_database.py
USER superset
ENV SUPERSET_CONFIG_PATH=/app/pythonpath/superset_config.py
ENTRYPOINT ["/usr/local/bin/initialize-superset.sh"]
