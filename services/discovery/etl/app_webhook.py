# -*- coding: utf-8 -*-
"""Receptor de webhooks de ODM (vía incremental del ETL de SIPI).

ODM, al publicar un dataset, hace POST firmado (HMAC-SHA256 en X-ODM-Signature)
a este endpoint. Verificamos la firma y poblamos sipi-core con el recurso
recién publicado (reusa el mismo pipeline que el backfill).

Arranque (modo por defecto de la imagen):
    uvicorn app_webhook:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import json
import logging

from fastapi import FastAPI, Header, HTTPException, Request

from src.odm import ODMClient
from src.odm import config as odm_config
from src.odm.pipeline import poblar_recurso

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("sipi.etl.webhook")

app = FastAPI(title="SIPI ETL — receptor ODM")


def _session_factory():
    from sipi_core.db.sessions import AsyncDatabaseManager
    return AsyncDatabaseManager().session


@app.get("/health")
def health():
    return {"status": "healthy", "service": "sipi-etl-odm-consumer"}


@app.post("/odm/webhook")
async def odm_webhook(request: Request, x_odm_signature: str = Header(default="")):
    raw = await request.body()
    if not ODMClient.verify_signature(raw, x_odm_signature):
        raise HTTPException(status_code=401, detail="Firma X-ODM-Signature inválida")

    payload = json.loads(raw)
    if payload.get("event") != "dataset.published":
        return {"ignored": payload.get("event")}

    resource_name = (payload.get("dataset") or {}).get("resource_name")
    if not resource_name:
        raise HTTPException(status_code=400, detail="Payload sin dataset.resource_name")
    if resource_name not in odm_config.RESOURCE_MAP:
        log.info("Recurso no mapeado, ignorado: %s", resource_name)
        return {"ignored_unmapped": resource_name}

    client = ODMClient()
    # poblar_recurso resuelve el último dataset del recurso (= el recién publicado)
    stats = await poblar_recurso(_session_factory(), client, resource_name)
    log.info("Webhook %s -> %s", resource_name, dict(stats))
    return {"resource": resource_name, "stats": dict(stats)}
