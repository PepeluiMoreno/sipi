#!/usr/bin/env python3
"""
load/cargar_geografia.py — L1: carga de geografía desde OpenDataManager (ODMGR)

Puebla en orden de dependencia FK:
    1. comunidades_autonomas  — desde ODMGR: geo_ccaa   (VALORES_VARIABLE/70)
    2. provincias             — desde ODMGR: geo_provincias (VALORES_VARIABLE/20)
    3. municipios             — desde ODMGR: geo_municipios (INE codmun.xlsx)

Fuentes ODMGR:
    espanaComunidadesAutonomasIne  → campos: Id, Codigo, Nombre
    espanaProvinciasIne            → campos: Id, Codigo, Nombre, FK_JerarquiaPadres
    espanaMunicipiosIne            → campos: codauto, cpro, cmun, nombre

Resolución FK:
    - CCAA: Codigo (2 dígitos INE)  ← clave de negocio
    - Provincia → CCAA: FK_JerarquiaPadres es lista de Ids internos INE.
      Se construye id_interno → sipi_uuid durante la carga de CCAA.
    - Municipio → Provincia: cpro (2 dígitos) → prov_map

Idempotente: INSERT … ON CONFLICT (codigo_ine/codigo) DO NOTHING.

Uso:
    python load/cargar_geografia.py
    python load/cargar_geografia.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_geografia.py --dry-run
"""

import argparse
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

from extract.clients.odmgr_client import ODMGRClient, resource_name_to_query
from load.utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# Nombres de query GraphQL derivados de los nombres de los recursos ODMGR
Q_CCAA      = resource_name_to_query("España - Comunidades Autónomas (INE)")
Q_PROVINCIAS = resource_name_to_query("España - Provincias (INE)")
Q_MUNICIPIOS = resource_name_to_query("España - Municipios (INE)")


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def main(odmgr_url: str, dry_run: bool):
    client = ODMGRClient(odmgr_url)

    log.info(f"Conectando a ODMGR: {odmgr_url}")
    log.info(f"  Queries: {Q_CCAA}, {Q_PROVINCIAS}, {Q_MUNICIPIOS}")

    # ── Obtener datos de ODMGR ────────────────────────────────────────────────

    log.info("Descargando CCAA desde ODMGR...")
    ccaa_records = list(client.fetch_all(Q_CCAA, ["Id", "Codigo", "Nombre"]))
    log.info(f"  {len(ccaa_records)} CCAA")

    log.info("Descargando Provincias desde ODMGR...")
    prov_records = list(client.fetch_all(Q_PROVINCIAS, ["Id", "Codigo", "Nombre", "FK_JerarquiaPadres"]))
    log.info(f"  {len(prov_records)} Provincias")

    log.info("Descargando Municipios desde ODMGR...")
    mun_records = list(client.fetch_all(Q_MUNICIPIOS, ["codauto", "cpro", "cmun", "nombre"]))
    log.info(f"  {len(mun_records):,} Municipios")

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")
        return

    # ── Conectar a SIPI ───────────────────────────────────────────────────────
    conn = await asyncpg.connect(get_dsn())
    try:
        await conn.execute("SET search_path TO sipi, public")
        await verificar_etluser(conn)
        now = datetime.utcnow()

        # ── 1. Comunidades Autónomas ──────────────────────────────────────────
        existing_ccaa = {
            r["codigo_ine"]: r["id"]
            for r in await conn.fetch("SELECT id, codigo_ine FROM sipi.comunidades_autonomas")
        }
        ccaa_by_ine_id: dict[str, str] = {}   # Id_interno_INE → sipi_uuid
        ccaa_map:       dict[str, str] = {}   # Codigo (2 dig) → sipi_uuid

        # Reconstruir mapas desde existentes (necesitamos Id interno → uuid pero no lo tenemos
        # en BD; los registros nuevos sí se mapean, los existentes se añadirán al mapa por código)
        for r in await conn.fetch("SELECT id, codigo_ine FROM sipi.comunidades_autonomas"):
            ccaa_map[r["codigo_ine"]] = r["id"]

        nuevas_ccaa = 0
        for row in ccaa_records:
            cod   = (row.get("Codigo") or "").strip()
            nombre = (row.get("Nombre") or "").strip()
            ine_id = str(row.get("Id") or "")
            if not cod:
                continue

            if cod in existing_ccaa:
                sipi_uuid = existing_ccaa[cod]
            else:
                sipi_uuid = str(uuid.uuid4())
                await conn.execute(
                    """INSERT INTO sipi.comunidades_autonomas
                       (id, codigo, codigo_ine, nombre, nombre_oficial, activo,
                        created_at, updated_at, created_by_id)
                       VALUES ($1, $2, $2, $3, $3, true, $4, $4, $5)
                       ON CONFLICT (codigo_ine) DO NOTHING""",
                    sipi_uuid, cod, nombre, now, ETL_USER_ID
                )
                nuevas_ccaa += 1
                ccaa_map[cod] = sipi_uuid

            if ine_id:
                ccaa_by_ine_id[ine_id] = sipi_uuid

        log.info(f"  CCAA: {nuevas_ccaa} nuevas, {len(existing_ccaa)} ya existían")

        # ── 2. Provincias ─────────────────────────────────────────────────────
        existing_prov = {
            r["codigo"]: r["id"]
            for r in await conn.fetch("SELECT id, codigo FROM sipi.provincias")
        }
        prov_map: dict[str, str] = dict(existing_prov)

        nuevas_prov = 0
        omitidas_prov = 0
        for row in prov_records:
            cod    = (row.get("Codigo") or "").strip()
            nombre = (row.get("Nombre") or "").strip()
            if not cod:
                continue

            # Resolver CCAA padre via FK_JerarquiaPadres (lista de Ids internos INE)
            fk_raw = row.get("FK_JerarquiaPadres") or "[]"
            if isinstance(fk_raw, str):
                try:
                    fk_list = json.loads(fk_raw)
                except (json.JSONDecodeError, ValueError):
                    fk_list = []
            else:
                fk_list = fk_raw if isinstance(fk_raw, list) else []

            ccaa_uuid = None
            if fk_list:
                # FK_JerarquiaPadres puede ser lista de ints [9004] o lista de dicts [{"Id": 9004}]
                first = fk_list[0]
                parent_ine_id = str(first["Id"]) if isinstance(first, dict) else str(first)
                ccaa_uuid = ccaa_by_ine_id.get(parent_ine_id)

            if not ccaa_uuid:
                omitidas_prov += 1
                continue

            if cod in existing_prov:
                prov_map[cod] = existing_prov[cod]
                continue

            sipi_uuid = str(uuid.uuid4())
            await conn.execute(
                """INSERT INTO sipi.provincias
                   (id, codigo, codigo_iso, nombre, comunidad_autonoma_id, activo,
                    created_at, updated_at, created_by_id)
                   VALUES ($1, $2, $2, $3, $4, true, $5, $5, $6)
                   ON CONFLICT (codigo) DO NOTHING""",
                sipi_uuid, cod, nombre, ccaa_uuid, now, ETL_USER_ID
            )
            prov_map[cod] = sipi_uuid
            nuevas_prov += 1

        msg = f"  Provincias: {nuevas_prov} nuevas, {len(existing_prov)} ya existían"
        if omitidas_prov:
            msg += f", {omitidas_prov} sin CCAA padre (FK no resuelta)"
        log.info(msg)

        # ── 3. Municipios ─────────────────────────────────────────────────────
        prov_ca = {
            r["id"]: r["comunidad_autonoma_id"]
            for r in await conn.fetch("SELECT id, comunidad_autonoma_id FROM sipi.provincias")
        }
        existing_mun = set(
            r["codigo_ine"]
            for r in await conn.fetch("SELECT codigo_ine FROM sipi.municipios")
        )

        nuevos_mun = 0
        omitidos_mun = 0
        BATCH = 500
        batch_args = []

        for row in mun_records:
            cpro   = (row.get("cpro") or "").strip()
            cmun   = (row.get("cmun") or "").strip()
            nombre = (row.get("nombre") or "").strip()
            if not cpro or not cmun:
                continue

            codigo_ine = cpro + cmun   # 5 dígitos: CPRO(2) + CMUN(3)
            if codigo_ine in existing_mun:
                continue

            prov_id = prov_map.get(cpro)
            if not prov_id:
                omitidos_mun += 1
                continue

            ca_id = prov_ca.get(prov_id)
            batch_args.append((
                str(uuid.uuid4()), codigo_ine, nombre,
                prov_id, ca_id, now, ETL_USER_ID
            ))

            if len(batch_args) >= BATCH:
                await conn.executemany(
                    """INSERT INTO sipi.municipios
                       (id, codigo_ine, nombre, provincia_id, comunidad_autonoma_id, activo,
                        created_at, updated_at, created_by_id)
                       VALUES ($1, $2, $3, $4, $5, true, $6, $6, $7)
                       ON CONFLICT (codigo_ine) DO NOTHING""",
                    batch_args
                )
                nuevos_mun += len(batch_args)
                batch_args = []

        if batch_args:
            await conn.executemany(
                """INSERT INTO sipi.municipios
                   (id, codigo_ine, nombre, provincia_id, comunidad_autonoma_id, activo,
                    created_at, updated_at, created_by_id)
                   VALUES ($1, $2, $3, $4, $5, true, $6, $6, $7)
                   ON CONFLICT (codigo_ine) DO NOTHING""",
                batch_args
            )
            nuevos_mun += len(batch_args)

        msg = f"  Municipios: {nuevos_mun:,} nuevos, {len(existing_mun):,} ya existían"
        if omitidos_mun:
            msg += f", {omitidos_mun} omitidos (provincia no encontrada)"
        log.info(msg)

    finally:
        await conn.close()

    log.info("✓ Geografía cargada desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L1: carga geografía desde ODMGR")
    parser.add_argument(
        "--odmgr-url",
        default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"),
        help="URL base de OpenDataManager"
    )
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run))
