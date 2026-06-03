#!/usr/bin/env python
"""
Seed unificado e idempotente de SIPI: acceso (RBAC) + configuración + comunicación.

Uso:
    export DATABASE_URL=postgresql://sipi:<pwd>@localhost:5433/sipi
    export APP_SCHEMA=sipi GIS_SCHEMA=sipi DEFAULT_SCHEMA=sipi DEFINED_SCHEMAS=sipi
    python -m sipi_core.scripts.seed_all

Re-ejecutable sin duplicar. Pensado para arranque/provisión.
"""
from __future__ import annotations
import os
import sys

import sqlalchemy as sa
from sqlalchemy.orm import Session

import sipi_core.models  # noqa: F401  (carga la fachada y registra los modelos)
from sipi_core.modules.acceso.services.seed import seed as seed_acceso
from sipi_core.modules.configuracion.services.seed import seed as seed_config
from sipi_core.modules.comunicacion.services.seed import seed as seed_comu


def _sync_url() -> str:
    url = os.getenv("DATABASE_URL")
    if not url:
        user = os.getenv("POSTGRES_USER", "sipi")
        pwd = os.getenv("POSTGRES_PASSWORD", "sipi")
        host = os.getenv("POSTGRES_SERVICE_NAME", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "sipi")
        url = f"postgresql://{user}:{pwd}@{host}:{port}/{db}"
    # driver síncrono
    return (url.replace("postgresql+asyncpg://", "postgresql://")
               .replace("postgresql+psycopg2://", "postgresql://"))


def run() -> dict:
    engine = sa.create_engine(_sync_url())
    with Session(engine) as s:
        out = {
            "acceso": seed_acceso(s),
            "configuracion": seed_config(s),
            "comunicacion": seed_comu(s),
        }
    return out


if __name__ == "__main__":
    resultado = run()
    print("Seed completado:")
    for modulo, detalle in resultado.items():
        print(f"  - {modulo}: {detalle}")
    sys.exit(0)
