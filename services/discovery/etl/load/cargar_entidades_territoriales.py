#!/usr/bin/env python3
"""
load/cargar_entidades_territoriales.py — consolida la jerarquía territorial recursiva.

Une en una sola tabla auto-referente `sipi.entidades_territoriales` (adjacency list,
parent_id) los dos árboles ya cargados desde OpenDataManager por los pasos previos:

    administrativo:  CCAA → Provincias → Municipios (INE)  → Entidades Locales Menores (Geonames)
    eclesiastico:    Provincias Eclesiásticas → Diócesis → Parroquias (CEE)

Es el paso de CONSOLIDACIÓN del workflow (debe ir tras L1, L3, L4, L5, L6). No descarga
de ODMGR: parte de lo ya materializado por esos loaders. El padre se resuelve por
(origen_tabla, origen_id), así que un huérfano entra con parent NULL.

Idempotente: cada INSERT es set-based con NOT EXISTS por (origen_tabla, origen_id).
created_by_id = ETL_USER_ID.

Nota: en la Fase 2 (cutover) los loaders de origen escribirán directamente aquí desde
ODMGR y se retirará esta consolidación junto con las 7 tablas tipadas.

Uso:
    python load/cargar_entidades_territoriales.py
    python load/cargar_entidades_territoriales.py --dry-run
"""
import argparse
import asyncio
import logging
import os
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from load.utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def get_dsn() -> str:
    return os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")


# (paso, SQL). $1 = ETL_USER_ID. Orden: padres antes que hijos.
_PASOS = [
    ("comunidades_autonomas", """
        INSERT INTO sipi.entidades_territoriales
          (id, dominio, tipo, nombre, parent_id, origen_tabla, origen_id, activo, created_at, created_by_id)
        SELECT gen_random_uuid()::text, 'administrativo', 'comunidad_autonoma', ca.nombre,
               NULL, 'comunidades_autonomas', ca.id, true, now()::timestamp, $1
        FROM sipi.comunidades_autonomas ca
        WHERE NOT EXISTS (SELECT 1 FROM sipi.entidades_territoriales et
                          WHERE et.origen_tabla='comunidades_autonomas' AND et.origen_id=ca.id)
    """),
    ("provincias", """
        INSERT INTO sipi.entidades_territoriales
          (id, dominio, tipo, nombre, parent_id, origen_tabla, origen_id, activo, created_at, created_by_id)
        SELECT gen_random_uuid()::text, 'administrativo', 'provincia', p.nombre,
               etca.id, 'provincias', p.id, true, now()::timestamp, $1
        FROM sipi.provincias p
        LEFT JOIN sipi.entidades_territoriales etca
          ON etca.origen_tabla='comunidades_autonomas' AND etca.origen_id=p.comunidad_autonoma_id
        WHERE NOT EXISTS (SELECT 1 FROM sipi.entidades_territoriales et
                          WHERE et.origen_tabla='provincias' AND et.origen_id=p.id)
    """),
    ("municipios", """
        INSERT INTO sipi.entidades_territoriales
          (id, dominio, tipo, nombre, parent_id, origen_tabla, origen_id, activo, created_at, created_by_id)
        SELECT gen_random_uuid()::text, 'administrativo', 'municipio', m.nombre,
               etp.id, 'municipios', m.id, true, now()::timestamp, $1
        FROM sipi.municipios m
        LEFT JOIN sipi.entidades_territoriales etp
          ON etp.origen_tabla='provincias' AND etp.origen_id=m.provincia_id
        WHERE NOT EXISTS (SELECT 1 FROM sipi.entidades_territoriales et
                          WHERE et.origen_tabla='municipios' AND et.origen_id=m.id)
    """),
    ("entidades_locales_menores", """
        INSERT INTO sipi.entidades_territoriales
          (id, dominio, tipo, nombre, parent_id, origen_tabla, origen_id, latitud, longitud, activo, created_at, created_by_id)
        SELECT gen_random_uuid()::text, 'administrativo', 'entidad_local_menor', elm.nombre,
               etm.id, 'entidades_locales_menores', elm.id, elm.latitud, elm.longitud, true, now()::timestamp, $1
        FROM sipi.entidades_locales_menores elm
        LEFT JOIN sipi.entidades_territoriales etm
          ON etm.origen_tabla='municipios' AND etm.origen_id=elm.municipio_id
        WHERE NOT EXISTS (SELECT 1 FROM sipi.entidades_territoriales et
                          WHERE et.origen_tabla='entidades_locales_menores' AND et.origen_id=elm.id)
    """),
    ("provincias_eclesiasticas", """
        INSERT INTO sipi.entidades_territoriales
          (id, dominio, tipo, nombre, parent_id, origen_tabla, origen_id, activo, created_at, created_by_id)
        SELECT gen_random_uuid()::text, 'eclesiastico', 'provincia_eclesiastica', pe.nombre,
               NULL, 'provincias_eclesiasticas', pe.id, true, now()::timestamp, $1
        FROM sipi.provincias_eclesiasticas pe
        WHERE NOT EXISTS (SELECT 1 FROM sipi.entidades_territoriales et
                          WHERE et.origen_tabla='provincias_eclesiasticas' AND et.origen_id=pe.id)
    """),
    ("diocesis", """
        INSERT INTO sipi.entidades_territoriales
          (id, dominio, tipo, nombre, parent_id, origen_tabla, origen_id, activo, created_at, created_by_id)
        SELECT gen_random_uuid()::text, 'eclesiastico', 'diocesis', d.nombre,
               etpe.id, 'diocesis', d.id, true, now()::timestamp, $1
        FROM sipi.diocesis d
        LEFT JOIN sipi.entidades_territoriales etpe
          ON etpe.origen_tabla='provincias_eclesiasticas' AND etpe.origen_id=d.provincia_eclesiastica_id
        WHERE NOT EXISTS (SELECT 1 FROM sipi.entidades_territoriales et
                          WHERE et.origen_tabla='diocesis' AND et.origen_id=d.id)
    """),
    ("parroquias", """
        INSERT INTO sipi.entidades_territoriales
          (id, dominio, tipo, nombre, parent_id, origen_tabla, origen_id, activo, created_at, created_by_id)
        SELECT gen_random_uuid()::text, 'eclesiastico', 'parroquia', pa.nombre,
               etd.id, 'parroquias', pa.id, true, now()::timestamp, $1
        FROM sipi.parroquias pa
        LEFT JOIN sipi.entidades_territoriales etd
          ON etd.origen_tabla='diocesis' AND etd.origen_id=pa.diocesis_id
        WHERE NOT EXISTS (SELECT 1 FROM sipi.entidades_territoriales et
                          WHERE et.origen_tabla='parroquias' AND et.origen_id=pa.id)
    """),
]


async def main(dry_run: bool) -> None:
    conn = await asyncpg.connect(get_dsn())
    try:
        await verificar_etluser(conn)
        total = 0
        for nombre, sql in _PASOS:
            if dry_run:
                log.info(f"[dry-run] {nombre}")
                continue
            status = await conn.execute(sql, ETL_USER_ID)
            n = int(status.split()[-1]) if status else 0
            total += n
            log.info(f"  {nombre}: +{n}")
        log.info(f"Consolidación territorial: {total} entidades nuevas.")
    finally:
        await conn.close()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Consolida la jerarquía territorial recursiva")
    ap.add_argument("--dry-run", action="store_true")
    asyncio.run(main(ap.parse_args().dry_run))
