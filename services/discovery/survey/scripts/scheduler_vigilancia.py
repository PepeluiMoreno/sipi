#!/usr/bin/env python3
"""Scheduler de vigilancia: ejecuta cada ProcesoVigilancia activo en su frecuencia_cron.

Worker ligero (stdlib + croniter) que cada `SCHED_INTERVAL` segundos:
  1. pregunta a la API GraphQL por los procesos activos (id, frecuenciaCron, ultimaEjecucion),
  2. para cada uno cuyo cron esté vencido respecto a su última ejecución, llama a
     `ejecutarProcesoVigilancia` (que descarga las fuentes, crea Hallazgo y actualiza
     ultima_ejecucion).

Env:  SIPI_API_URL (def http://api:8040/graphql/) · SCHED_INTERVAL (def 60)
"""
import json
import logging
import os
import time
import urllib.request
from datetime import datetime, timedelta

try:
    from croniter import croniter
except ImportError:  # se instala en el contenedor; mensaje claro si falta
    raise SystemExit("Falta 'croniter' (pip install croniter).")

API = os.getenv("SIPI_API_URL", "http://api:8040/graphql/")
INTERVAL = int(os.getenv("SCHED_INTERVAL", "60"))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s scheduler: %(message)s")
log = logging.getLogger("vigilancia.scheduler")

_LISTAR = """
query($f: [FilterInput!]) {
  procesosVigilancia(limit: 500, filters: $f) {
    items { id nombre frecuenciaCron ultimaEjecucion }
  }
}
"""
_EJECUTAR = "mutation($id: ID!){ ejecutarProcesoVigilancia(procesoId: $id){ ok creados mensaje } }"


def gql(query, variables=None):
    body = {"query": query}
    if variables:
        body["variables"] = variables
    req = urllib.request.Request(API, data=json.dumps(body).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.loads(r.read().decode("utf-8"))
    if data.get("errors"):
        raise RuntimeError(data["errors"])
    return data["data"]


def _parse(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00")).replace(tzinfo=None)
    except Exception:
        return None


def due(cron, ultima, now):
    if not cron:
        return False
    base = _parse(ultima) or (now - timedelta(days=3650))  # nunca ejecutado → vencido
    try:
        return croniter(cron, base).get_next(datetime) <= now
    except Exception as e:
        log.warning("cron inválido %r: %s", cron, e)
        return False


def tick():
    now = datetime.utcnow()
    try:
        procs = gql(_LISTAR, {"f": [{"field": "activo", "operator": "EQ", "value": "true"}]})
        items = procs["procesosVigilancia"]["items"]
    except Exception as e:
        log.error("No se pudo listar procesos: %s", e)
        return
    for p in items:
        if due(p.get("frecuenciaCron"), p.get("ultimaEjecucion"), now):
            try:
                r = gql(_EJECUTAR, {"id": p["id"]})["ejecutarProcesoVigilancia"]
                log.info("Ejecutado «%s»: %s hallazgos. %s",
                         p.get("nombre"), r.get("creados"), (r.get("mensaje") or "").replace("\n", " | "))
            except Exception as e:
                log.error("Fallo ejecutando «%s»: %s", p.get("nombre"), e)


def main():
    log.info("Scheduler de vigilancia en marcha (API=%s, intervalo=%ss).", API, INTERVAL)
    while True:
        tick()
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
