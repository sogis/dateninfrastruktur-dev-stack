FROM postgres:16.10-bookworm@sha256:38471f330eb885e04de130b768d6db4e10469e2311879c7e5c699f6d2d8a1c74
ARG TARGETARCH
# Keep the existing PostGIS ABI/version and avoid a PG16.10 -> 16.9 downgrade.
# PGDG archive package SHA256 values come from its architecture-specific index.
RUN set -eu; \
    case "$TARGETARCH" in \
      arm64) runtime_sha=ed269049725434b915fb3723e07b575767690ff1fc2c653de2e8a236517c2f8b ;; \
      amd64) runtime_sha=24ef2e0be6118a4b5eb0f6ed023513a63037612cb1356bd2a1e7627cda003485 ;; \
      *) exit 2 ;; \
    esac; \
    apt-mark hold postgresql-16 postgresql-client-16; \
    apt-get update; apt-get install -y --no-install-recommends ca-certificates curl; \
    base=https://apt-archive.postgresql.org/pub/repos/apt/pool/main/p/postgis; \
    curl --fail --location --retry 3 "$base/postgresql-16-postgis-3_3.5.2+dfsg-1.pgdg120+1_${TARGETARCH}.deb" -o /tmp/postgis.deb; \
    curl --fail --location --retry 3 "$base/postgresql-16-postgis-3-scripts_3.5.2+dfsg-1.pgdg120+1_all.deb" -o /tmp/postgis-scripts.deb; \
    printf '%s  /tmp/postgis.deb\n' "$runtime_sha" | sha256sum -c -; \
    printf '%s  /tmp/postgis-scripts.deb\n' 69193c85be98675c82f10f56d8ddd16f3166dbed64679c01a576ac38365c04b0 | sha256sum -c -; \
    apt-get install -y --no-install-recommends /tmp/postgis.deb /tmp/postgis-scripts.deb; \
    test "$(postgres --version)" = 'postgres (PostgreSQL) 16.10 (Debian 16.10-1.pgdg12+1)'; \
    rm -f /tmp/postgis.deb /tmp/postgis-scripts.deb; rm -rf /var/lib/apt/lists/*
# No automatic CREATE EXTENSION in template1 or application databases.
