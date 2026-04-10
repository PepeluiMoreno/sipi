#!/usr/bin/env python3
"""
load/cargar_agencias_inmobiliarias.py — L14: agencias inmobiliarias desde ODMGR

Fuentes ODMGR:
    - agencias_inmobiliarias_rera (Agencias Inmobiliarias - RERA Andalucía)
      Query: agenciasInmobiliariasReraAndalucia
      Campos: nombre, nif, municipio, provincia, telefono, email, fecha_registro
      Clave SIPI: nombre (ON CONFLICT DO NOTHING)

    - agencias_inmobiliarias_fotocasa (Agencias Inmobiliarias - Fotocasa)
      Query: agenciasInmobiliariasFotocasa
      Campos: agency_id, nombre, provincia, inmuebles_zona, inmuebles_total,
              precio_minimo, url_busqueda
      Clave SIPI: fotocasa_id (agencias_inmobiliarias) + (agencia_id, provincia_id, fuente)
                  en agencias_provincias

Modelo SIPI:
    sipi.agencias_inmobiliarias   — una fila por agencia (clave: fotocasa_id / nombre)
    sipi.agencias_provincias      — pivot: presencia provincial por fuente

Idempotente:
    - RERA:     ON CONFLICT (nombre) DO NOTHING
    - Fotocasa: ON CONFLICT (fotocasa_id) DO UPDATE nombre/fuente
                ON CONFLICT (agencia_id, provincia_id, fuente) DO UPDATE métricas

Uso:
    python load/cargar_agencias_inmobiliarias.py
    python load/cargar_agencias_inmobiliarias.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_agencias_inmobiliarias.py --dry-run
    python load/cargar_agencias_inmobiliarias.py --list-fields
"""

import argparse
import asyncio
import logging
import os
import re
import sys
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))
from extract.clients.odmgr_client import ODMGRClient, resource_name_to_query
from load.utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv(Path(__file__).parent.parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

# ── Fuente RERA ────────────────────────────────────────────────────────────────
Q_RERA   = resource_name_to_query("Agencias Inmobiliarias (RERA Andalucía)")
FIELDS_RERA = [
    "nombre", "nif", "municipio", "provincia", "telefono", "email", "fecha_registro",
    "Nombre", "NIF", "Municipio", "Provincia", "Telefono", "Email",
]

# ── Fuente Fotocasa ────────────────────────────────────────────────────────────
Q_FOTOCASA   = resource_name_to_query("Agencias Inmobiliarias (Fotocasa)")
FIELDS_FOTOCASA = [
    "agency_id", "nombre", "provincia", "inmuebles_zona", "inmuebles_total",
    "precio_minimo", "url_busqueda",
]

TABLA       = "sipi.agencias_inmobiliarias"
TABLA_PROV  = "sipi.agencias_provincias"


def get_dsn() -> str:
    return os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")


def slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto or "")
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _get(row: dict, *keys: str) -> str:
    for k in keys:
        v = row.get(k) or row.get(k.lower()) or ""
        if v:
            return str(v).strip()
    return ""


def _parse_int(text: str) -> int | None:
    """Convierte '1.138' o '12313' a int."""
    try:
        return int(re.sub(r"[^\d]", "", text or ""))
    except (ValueError, TypeError):
        return None


async def main(odmgr_url: str, dry_run: bool, list_fields: bool):
    client = ODMGRClient(odmgr_url)
    now = datetime.utcnow()

    # ── Descarga RERA ──────────────────────────────────────────────────────────
    rera_records = []
    try:
        rera_records = list(client.fetch_all(Q_RERA, FIELDS_RERA))
        log.info(f"RERA Andalucía: {len(rera_records)} registros")
        if rera_records and list_fields:
            log.info("  Campos RERA:")
            for k, v in rera_records[0].items():
                log.info(f"    {k!r}: {v!r}")
    except Exception as e:
        log.warning(f"  RERA: sin datos ({e})")

    # ── Descarga Fotocasa ──────────────────────────────────────────────────────
    foto_records = []
    try:
        foto_records = list(client.fetch_all(Q_FOTOCASA, FIELDS_FOTOCASA))
        log.info(f"Fotocasa: {len(foto_records)} registros (agency × provincia)")
        if foto_records and list_fields:
            log.info("  Campos Fotocasa:")
            for k, v in foto_records[0].items():
                log.info(f"    {k!r}: {v!r}")
    except Exception as e:
        log.warning(f"  Fotocasa: sin datos ({e})")

    if list_fields or dry_run:
        if dry_run:
            log.info("[DRY-RUN: no se escribirá en BD]")
        return

    if not rera_records and not foto_records:
        log.warning("Sin datos de ninguna fuente.")
        return

    conn = await asyncpg.connect(get_dsn())
    try:
        await conn.execute("SET search_path TO sipi, public")
        await verificar_etluser(conn)

        # ── Lookups geográficos ────────────────────────────────────────────────
        mun_map: dict[str, tuple[str, str, str]] = {}
        for r in await conn.fetch(
            "SELECT m.id, m.nombre, m.provincia_id, m.comunidad_autonoma_id FROM sipi.municipios m"
        ):
            mun_map[slugify(r["nombre"])] = (r["id"], r["provincia_id"], r["comunidad_autonoma_id"])

        prov_by_nombre: dict[str, str] = {
            slugify(r["nombre"]): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.provincias")
        }
        # Fotocasa usa slugs de provincia tipo "madrid-provincia"
        prov_by_slug: dict[str, str] = {}
        for r in await conn.fetch("SELECT id, nombre FROM sipi.provincias"):
            slug = slugify(r["nombre"])
            prov_by_slug[slug]                   = r["id"]
            prov_by_slug[slug + "-provincia"]    = r["id"]
            prov_by_slug[slug + "-comunidad"]    = r["id"]

        # ── Carga RERA ─────────────────────────────────────────────────────────
        existentes_nombre: set[str] = {
            r["nombre"] for r in await conn.fetch(f"SELECT nombre FROM {TABLA}")
        }

        ins_rera = sin_mun_rera = 0
        for row in rera_records:
            nombre = _get(row, "nombre", "Nombre")
            if not nombre or nombre in existentes_nombre:
                continue

            mun_nombre  = _get(row, "municipio", "Municipio")
            prov_nombre = _get(row, "provincia", "Provincia")
            mun_data    = mun_map.get(slugify(mun_nombre)) if mun_nombre else None
            prov_id     = prov_by_nombre.get(slugify(prov_nombre)) if prov_nombre else None

            if not mun_data:
                sin_mun_rera += 1

            await conn.execute(
                f"""INSERT INTO {TABLA}
                    (id, created_at, created_by_id, nombre, fuente,
                     telefono, email_corporativo,
                     municipio_id, provincia_id, comunidad_autonoma_id)
                    VALUES ($1,$2,$3,$4,'RERA',$5,$6,$7,$8,$9)
                    ON CONFLICT (nombre) DO NOTHING""",
                str(uuid.uuid4()), now, ETL_USER_ID, nombre,
                _get(row, "telefono", "Telefono") or None,
                _get(row, "email", "Email") or None,
                mun_data[0] if mun_data else None,
                mun_data[1] if mun_data else prov_id,
                mun_data[2] if mun_data else None,
            )
            existentes_nombre.add(nombre)
            ins_rera += 1

        log.info(f"  RERA: {ins_rera} insertadas" + (f", {sin_mun_rera} sin municipio" if sin_mun_rera else ""))

        # ── Carga Fotocasa ─────────────────────────────────────────────────────
        # Mapa fotocasa_id → id SIPI (para la tabla pivot)
        foto_existing: dict[str, str] = {
            r["fotocasa_id"]: r["id"]
            for r in await conn.fetch(
                f"SELECT id, fotocasa_id FROM {TABLA} WHERE fotocasa_id IS NOT NULL"
            )
        }

        ins_foto = upd_foto = ins_prov = upd_prov = sin_prov = 0

        # Agrupar por agency_id para insertar una sola vez la agencia principal
        agencias_vistas: dict[str, str] = {}  # fotocasa_id → sipi_id

        for row in foto_records:
            agency_id = _get(row, "agency_id")
            nombre    = _get(row, "nombre")
            if not agency_id or not nombre:
                continue

            # 1. Upsert agencia principal
            if agency_id not in agencias_vistas:
                if agency_id in foto_existing:
                    # Actualizar nombre si ha cambiado
                    sipi_id = foto_existing[agency_id]
                    await conn.execute(
                        f"UPDATE {TABLA} SET nombre=$1, updated_at=$2 WHERE id=$3",
                        nombre, now, sipi_id,
                    )
                    upd_foto += 1
                else:
                    sipi_id = str(uuid.uuid4())
                    await conn.execute(
                        f"""INSERT INTO {TABLA}
                            (id, created_at, created_by_id, nombre, fotocasa_id, fuente)
                            VALUES ($1,$2,$3,$4,$5,'Fotocasa')
                            ON CONFLICT (fotocasa_id) DO UPDATE
                              SET nombre=EXCLUDED.nombre, updated_at=$2""",
                        sipi_id, now, ETL_USER_ID, nombre, agency_id,
                    )
                    foto_existing[agency_id] = sipi_id
                    ins_foto += 1

                agencias_vistas[agency_id] = foto_existing[agency_id]

            sipi_id = agencias_vistas[agency_id]

            # 2. Upsert presencia provincial
            provincia_slug = _get(row, "provincia")
            prov_id = prov_by_slug.get(provincia_slug)
            if not prov_id:
                sin_prov += 1
                continue

            inmuebles_zona  = _parse_int(_get(row, "inmuebles_zona"))
            inmuebles_total = _parse_int(_get(row, "inmuebles_total"))
            precio_minimo   = _get(row, "precio_minimo") or None
            url_busqueda    = _get(row, "url_busqueda") or None

            await conn.execute(
                f"""INSERT INTO {TABLA_PROV}
                    (id, agencia_id, provincia_id, fuente,
                     inmuebles_zona, inmuebles_total, precio_minimo, url_busqueda,
                     created_at, updated_at)
                    VALUES ($1,$2,$3,'Fotocasa',$4,$5,$6,$7,$8,$8)
                    ON CONFLICT (agencia_id, provincia_id, fuente) DO UPDATE
                      SET inmuebles_zona  = EXCLUDED.inmuebles_zona,
                          inmuebles_total = EXCLUDED.inmuebles_total,
                          precio_minimo   = EXCLUDED.precio_minimo,
                          url_busqueda    = EXCLUDED.url_busqueda,
                          updated_at      = EXCLUDED.updated_at""",
                str(uuid.uuid4()), sipi_id, prov_id,
                inmuebles_zona, inmuebles_total, precio_minimo, url_busqueda, now,
            )
            ins_prov += 1

        log.info(
            f"  Fotocasa: {ins_foto} agencias nuevas, {upd_foto} actualizadas | "
            f"{ins_prov} registros provinciales"
            + (f", {sin_prov} provincias no resueltas" if sin_prov else "")
        )

    finally:
        await conn.close()

    log.info("✓ Agencias inmobiliarias cargadas desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L14: agencias inmobiliarias desde ODMGR")
    parser.add_argument("--odmgr-url", default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-fields", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.list_fields))
