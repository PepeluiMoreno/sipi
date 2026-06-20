#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Puebla la base de datos de SIPI (sipi-core) desde los recursos de ODM.

Sustituye a populate_master_data.py: ya no se derivan agentes del censo CSV;
se consumen los recursos producidos por OpenDataManager.

Requisitos en tiempo de ejecución (no van en el repo):
  - DATABASE_URL        DSN de la BD de SIPI (postgresql+asyncpg://...)
  - ODM_BASE_URL        URL base del ODM desplegado (con datasets publicados)
  - ODM_APP_TOKEN       (opcional) token M2M si ODM exige auth

Uso:
  python scripts/poblar_desde_odm.py --todo
  python scripts/poblar_desde_odm.py --recurso "Registro de Entidades Religiosas (RER)"
  python scripts/poblar_desde_odm.py --listar
"""
import argparse
import asyncio
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv()  # carga .env ANTES de importar sipi-core

from src.odm import ODMClient, poblar_recurso, poblar_todo  # noqa: E402
from src.odm import config as odm_config  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
log = logging.getLogger("poblar")


def _session_factory():
    """Devuelve un callable -> async context manager de AsyncSession (sipi-core)."""
    from sipi_core.db.sessions import AsyncDatabaseManager
    mgr = AsyncDatabaseManager()
    return mgr.session


async def main_async(args):
    if args.listar:
        print("Recursos ODM mapeados (RESOURCE_MAP):")
        for name, (dominio, fuente) in sorted(odm_config.RESOURCE_MAP.items()):
            print(f"  [{dominio:18s} / {fuente:14s}] {name}")
        return 0

    odm_config.require_connection()
    if not os.getenv("DATABASE_URL"):
        log.error("Falta DATABASE_URL (DSN de la BD de SIPI).")
        return 2

    client = ODMClient()
    session_factory = _session_factory()

    if args.todo:
        stats = await poblar_todo(session_factory, client)
    elif args.recurso:
        stats = await poblar_recurso(session_factory, client, args.recurso)
    else:
        log.error("Indica --todo, --recurso NOMBRE o --listar.")
        return 2

    log.info("RESUMEN: %s", dict(stats))
    return 0


def main():
    p = argparse.ArgumentParser(description="Poblar SIPI desde recursos de ODM")
    p.add_argument("--todo", action="store_true", help="Poblar todos los recursos mapeados")
    p.add_argument("--recurso", help="Poblar un único recurso por nombre exacto")
    p.add_argument("--listar", action="store_true", help="Listar recursos mapeados y salir")
    args = p.parse_args()
    sys.exit(asyncio.run(main_async(args)))


if __name__ == "__main__":
    main()
