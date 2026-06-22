#!/bin/bash
set -e

# Espera a PostgreSQL parseando host/puerto de DATABASE_URL (si es parseable)
python - <<'PY' || true
import os, re, time, socket
url = os.environ.get("DATABASE_URL", "")
m = re.search(r"@([^:/]+)(?::(\d+))?/", url)
if m:
    host, port = m.group(1), int(m.group(2) or 5432)
    for _ in range(60):
        try:
            socket.create_connection((host, port), timeout=2).close()
            print(f"[entrypoint] PostgreSQL {host}:{port} listo."); break
        except OSError:
            print(f"[entrypoint] esperando PostgreSQL {host}:{port}..."); time.sleep(2)
PY

MODE="${SIPI_ETL_MODE:-webhook}"
if [ "$MODE" = "migrate" ]; then
    echo "[entrypoint] modo MIGRATE: alembic upgrade head (sipi-core)"
    # Las migraciones asumen que los esquemas (DEFINED_SCHEMAS, p.ej. app,gis) ya
    # existen — ninguna hace CREATE SCHEMA. Los creamos aquí, idempotente.
    python - <<'PY'
import os, re, psycopg2
dsn = re.sub(r"\+\w+", "", os.environ.get("DATABASE_URL", ""))  # postgresql+asyncpg -> postgresql
schemas = (os.environ.get("DEFINED_SCHEMAS") or os.environ.get("APP_SCHEMA") or "app").split(",")
conn = psycopg2.connect(dsn); conn.autocommit = True
cur = conn.cursor()
for s in (x.strip() for x in schemas):
    if s:
        cur.execute(f'CREATE SCHEMA IF NOT EXISTS "{s}"')
cur.close(); conn.close()
print("[entrypoint] esquemas asegurados:", schemas)
PY
    cd /app/packages/sipi-core/src/sipi_core
    exec python -m alembic upgrade head
elif [ "$MODE" = "poblar" ]; then
    echo "[entrypoint] modo POBLAR (one-shot): scripts/poblar_desde_odm.py ${POBLAR_ARGS:---todo}"
    exec python scripts/poblar_desde_odm.py ${POBLAR_ARGS:---todo}
else
    echo "[entrypoint] modo WEBHOOK: receptor de notificaciones ODM (uvicorn :8000)"
    exec uvicorn app_webhook:app --host 0.0.0.0 --port 8000
fi
