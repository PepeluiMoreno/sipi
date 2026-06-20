# Imagen del ETL consumidor de ODM. Build context = raíz del monorepo.
FROM python:3.11-slim
RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client && rm -rf /var/lib/apt/lists/*
WORKDIR /app

# sipi-core: única fuente de verdad de modelos, instalada por ruta
COPY packages/sipi-core /app/packages/sipi-core
RUN pip install --no-cache-dir -e /app/packages/sipi-core

# dependencias del consumidor
COPY services/discovery/etl/requirements-odm.txt /app/requirements-odm.txt
RUN pip install --no-cache-dir -r /app/requirements-odm.txt

COPY services/discovery/etl /app/services/discovery/etl
RUN chmod +x /app/services/discovery/etl/docker/entrypoint.sh
ARG BUILD_SHA=dev
ENV APP_VERSION=${BUILD_SHA}
WORKDIR /app/services/discovery/etl
ENTRYPOINT ["/app/services/discovery/etl/docker/entrypoint.sh"]
