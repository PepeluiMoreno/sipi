#!/bin/bash
# entrypoint.sh
# Las migraciones se aplican manualmente antes del despliegue:
#   docker exec sipi-graphql bash -c "cd /code/sipi_core && alembic upgrade head"
set -e

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1 - $2"
}

log "INFO" "🚀 Iniciando SIPI GraphQL API"

cd /code

log "INFO" "🌐 Iniciando servidor GraphQL en puerto ${GRAPHQL_PORT:-8000}"
exec uvicorn app.graphql.app:application \
    --host 0.0.0.0 \
    --port "${GRAPHQL_PORT:-8000}" \
    --reload
