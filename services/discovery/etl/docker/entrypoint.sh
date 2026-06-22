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
    # El historial alembic de sipi-core es inconsistente (mezcla esquemas app y
    # sipi → falla en BD limpia). Para staging (BD nueva, sin datos) inicializamos
    # el esquema directamente desde los modelos: CREATE SCHEMA + metadata.create_all.
    # Idempotente (create_all no recrea lo existente).
    echo "[entrypoint] modo MIGRATE: init de esquema (create_all de sipi-core)"
    exec python - <<'PY'
import os, re
from sqlalchemy import create_engine, text
dsn = re.sub(r"\+\w+", "", os.environ.get("DATABASE_URL", ""))  # postgresql+asyncpg -> postgresql
schemas = (os.environ.get("DEFINED_SCHEMAS") or os.environ.get("APP_SCHEMA") or "app").split(",")
engine = create_engine(dsn)
with engine.begin() as conn:
    for s in (x.strip() for x in schemas):
        if s:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{s}"'))
import sipi_core.models  # registra todos los modelos en la metadata
from sipi_core.db.metadata import get_combined_metadata
md = get_combined_metadata()
md.create_all(engine)
print(f"[entrypoint] esquema inicializado: {len(md.tables)} tablas en {schemas}")
PY
elif [ "$MODE" = "poblar" ]; then
    echo "[entrypoint] modo POBLAR (one-shot): scripts/poblar_desde_odm.py ${POBLAR_ARGS:---todo}"
    exec python scripts/poblar_desde_odm.py ${POBLAR_ARGS:---todo}
else
    echo "[entrypoint] modo WEBHOOK: receptor de notificaciones ODM (uvicorn :8000)"
    exec uvicorn app_webhook:app --host 0.0.0.0 --port 8000
fi
