#!/usr/bin/env python3
"""
load/cargar_entidades_locales_menores.py — carga ELM desde OpenDataManager (ODMGR)

Fuente ODMGR: geo_elm (Geonames ES.zip → ES.txt)
    Query: geonamesEntidadesDePoblacionEspana
    Campos: geonameid, name, feature_class, feature_code, admin3, lat, lon, population

Filtrado:
    feature_class = P (entidades de población)
    feature_code  ∈ FCODES_INCLUIR (PPL, PPLX, PPLL, PPLF, PPLH, PPLS, PPLR, PPLW, PPLA4)
    admin3        = código INE del municipio (5 dígitos) — omite si vacío o longitud ≠ 5

Vinculación con municipio:
    admin3 → municipio.codigo_ine → municipio.id (UUID SIPI)

Idempotente: ON CONFLICT (codigo_geonames) DO UPDATE

Uso:
    python load/cargar_entidades_locales_menores.py
    python load/cargar_entidades_locales_menores.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_entidades_locales_menores.py --dry-run
    python load/cargar_entidades_locales_menores.py --solo-ppl
"""

import argparse
import asyncio
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

Q_GEONAMES = resource_name_to_query("Geonames - Entidades de Población (España)")

TABLA = "sipi.entidades_locales_menores"

FCODES_INCLUIR  = {"PPL", "PPLA3", "PPLX", "PPLL", "PPLF", "PPLH", "PPLS", "PPLR", "PPLW", "PPLA4"}
FCODES_SOLO_PPL = {"PPL", "PPLX", "PPLL", "PPLF", "PPLH", "PPLS", "PPLR", "PPLW"}


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def main(odmgr_url: str, dry_run: bool, solo_ppl: bool):
    client = ODMGRClient(odmgr_url)
    fcodes = FCODES_SOLO_PPL if solo_ppl else FCODES_INCLUIR

    log.info(f"Conectando a ODMGR: {odmgr_url}")
    log.info(f"  Query: {Q_GEONAMES}")

    # ── Descargar desde ODMGR ─────────────────────────────────────────────────
    fields = ["geonameid", "name", "feature_class", "feature_code", "admin3", "lat", "lon", "population"]
    log.info("Descargando entidades de Geonames desde ODMGR...")

    entidades = []
    total_raw = 0
    for row in client.fetch_all(Q_GEONAMES, fields, page_size=1000):
        total_raw += 1
        if row.get("feature_class") != "P":
            continue
        if row.get("feature_code") not in fcodes:
            continue
        admin3 = (row.get("admin3") or "").strip()
        if not admin3 or len(admin3) != 5:
            continue
        entidades.append({
            "geonameid": int(row["geonameid"]) if row.get("geonameid") else None,
            "nombre":    (row.get("name") or "").strip(),
            "tipo":      row.get("feature_code", ""),
            "admin3":    admin3,
            "lat":       float(row["lat"]) if row.get("lat") else None,
            "lon":       float(row["lon"]) if row.get("lon") else None,
            "poblacion": int(row["population"]) if row.get("population") else None,
        })

    log.info(f"  Total bruto: {total_raw:,} | Filtradas (clase P, fcode, admin3): {len(entidades):,}")

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")
        return

    # ── Cargar en SIPI ────────────────────────────────────────────────────────
    conn = await asyncpg.connect(get_dsn())
    try:
        await verificar_etluser(conn)

        # Garantizar constraint único en codigo_geonames
        await conn.execute("""
            DO $$ BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint WHERE conname = 'uq_elm_codigo_geonames'
                ) THEN
                    ALTER TABLE sipi.entidades_locales_menores
                        ADD CONSTRAINT uq_elm_codigo_geonames UNIQUE (codigo_geonames);
                END IF;
            END $$;
        """)

        # Mapa codigo_ine → municipio_id
        mapa_mun = {
            r["codigo_ine"]: r["id"]
            for r in await conn.fetch("SELECT id, codigo_ine FROM sipi.municipios")
        }
        log.info(f"  Municipios en BD: {len(mapa_mun):,}")

        now = datetime.utcnow()
        sin_municipio = 0
        insertadas = 0
        actualizadas = 0
        BATCH = 500

        sql = f"""
            INSERT INTO {TABLA}
                (id, nombre, tipo_geonames, codigo_geonames, codigo_ine_municipio,
                 latitud, longitud, poblacion, municipio_id, created_at, updated_at, created_by_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12)
            ON CONFLICT (codigo_geonames) DO UPDATE SET
                nombre               = EXCLUDED.nombre,
                tipo_geonames        = EXCLUDED.tipo_geonames,
                codigo_ine_municipio = EXCLUDED.codigo_ine_municipio,
                latitud              = EXCLUDED.latitud,
                longitud             = EXCLUDED.longitud,
                poblacion            = EXCLUDED.poblacion,
                municipio_id         = EXCLUDED.municipio_id,
                updated_at           = EXCLUDED.updated_at
        """

        records = []
        for e in entidades:
            municipio_id = mapa_mun.get(e["admin3"])
            if not municipio_id:
                sin_municipio += 1
            records.append((
                str(uuid.uuid4()),
                e["nombre"],
                e["tipo"],
                e["geonameid"],
                e["admin3"],
                e["lat"],
                e["lon"],
                e["poblacion"],
                municipio_id,
                now, now,
                ETL_USER_ID,
            ))

        async with conn.transaction():
            for i in range(0, len(records), BATCH):
                batch = records[i:i + BATCH]
                for r in batch:
                    status = await conn.execute(sql, *r)
                    if "INSERT 0 1" in status:
                        insertadas += 1
                    else:
                        actualizadas += 1
                log.info(f"  … {min(i + BATCH, len(records)):,}/{len(records):,}")

        log.info(
            f"  ELMs: {insertadas:,} insertadas, {actualizadas:,} actualizadas"
            + (f", {sin_municipio:,} sin municipio INE" if sin_municipio else "")
        )

    finally:
        await conn.close()

    log.info("✓ Entidades locales menores cargadas desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga ELM desde ODMGR (Geonames)")
    parser.add_argument(
        "--odmgr-url",
        default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"),
        help="URL base de OpenDataManager"
    )
    parser.add_argument("--dry-run",  action="store_true", help="Simula sin escribir en BD")
    parser.add_argument("--solo-ppl", action="store_true",
                        help="Solo PPL (excluye PPLA3 que solapan con municipios INE)")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.solo_ppl))
