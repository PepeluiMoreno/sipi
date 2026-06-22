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
    # sipi → falla en BD limpia). Para staging (BD nueva) inicializamos el esquema
    # desde los modelos (create_all) + RBAC + usuarios (superadmin y visitante).
    # Todo idempotente.
    echo "[entrypoint] modo MIGRATE: init de staging (esquema + RBAC + usuarios)"
    exec python scripts/init_staging.py
elif [ "$MODE" = "poblar" ]; then
    echo "[entrypoint] modo POBLAR (one-shot): scripts/poblar_desde_odm.py ${POBLAR_ARGS:---todo}"
    exec python scripts/poblar_desde_odm.py ${POBLAR_ARGS:---todo}
else
    echo "[entrypoint] modo WEBHOOK: receptor de notificaciones ODM (uvicorn :8000)"
    exec uvicorn app_webhook:app --host 0.0.0.0 --port 8000
fi
