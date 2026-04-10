#!/usr/bin/env python3
"""
load/cargar_diocesis_odmgr.py — L5b: diócesis desde OpenDataManager (ODMGR)

Fuente ODMGR: entidades_religiosas (Diócesis y Entidades Religiosas - CEE)
    Query:  diocesisYEntidadesReligiosasCee
    Fuente: XLSX de conferenciaepiscopal.es

Campos XLSX CEE (normalizados a snake_case por ODMGR):
    nombre, tipo, obispo / obispo_nombre,
    municipio / sede, provincia,
    telefono, web / sitio_web

Target SIPI: sipi.diocesis
    nombre (único), es_archidiocesis, obispo_nombre,
    telefono, sitio_web_propio, municipio_id

Idempotente: UPDATE si existe por nombre, INSERT si no.

Uso:
    python load/cargar_diocesis_odmgr.py
    python load/cargar_diocesis_odmgr.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_diocesis_odmgr.py --dry-run
    python load/cargar_diocesis_odmgr.py --list-fields
"""

import argparse
import asyncio
import logging
import os
import sys
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

Q_CEE = resource_name_to_query("Diócesis y Entidades Religiosas (CEE)")

FIELDS = [
    "nombre", "tipo", "obispo", "obispo_nombre",
    "sede", "municipio", "provincia",
    "telefono", "web", "sitio_web", "sitio_web_propio",
    "email",
]

TABLA = "sipi.diocesis"


def get_dsn() -> str:
    return os.environ.get("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")


def _get(row: dict, *keys: str, default: str = "") -> str:
    for k in keys:
        v = row.get(k) or row.get(k.lower()) or ""
        if v:
            return str(v).strip()
    return default


def _es_archidiocesis(tipo: str) -> bool:
    return "archi" in tipo.lower() or "metropolitana" in tipo.lower()


async def main(odmgr_url: str, dry_run: bool, list_fields: bool):
    client = ODMGRClient(odmgr_url)

    log.info(f"Descargando diócesis desde ODMGR: {odmgr_url}")
    records = list(client.fetch_all(Q_CEE, FIELDS))
    log.info(f"  {len(records)} entradas")

    if not records:
        log.warning("  Sin datos. ¿El recurso 'Diócesis y Entidades Religiosas (CEE)' está ejecutado en ODMGR?")
        return

    if list_fields:
        log.info("Campos del 1er registro:")
        for k, v in records[0].items():
            log.info(f"  {k!r}: {v!r}")
        return

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")
        return

    conn = await asyncpg.connect(get_dsn())
    try:
        await conn.execute("SET search_path TO sipi, public")
        await verificar_etluser(conn)
        now = datetime.utcnow()

        # ── Mapa de municipios ────────────────────────────────────────────────
        import re, unicodedata

        def slugify(t: str) -> str:
            nfkd = unicodedata.normalize("NFKD", t or "")
            ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
            return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")

        mun_prov: dict[tuple[str, str], str] = {}
        for r in await conn.fetch(
            "SELECT m.id, lower(m.nombre) AS mun, lower(p.nombre) AS prov "
            "FROM sipi.municipios m JOIN sipi.provincias p ON m.provincia_id = p.id"
        ):
            mun_prov[(r["mun"], r["prov"])] = r["id"]

        # ── Existentes ────────────────────────────────────────────────────────
        existentes: dict[str, str] = {
            r["nombre"]: r["id"]
            for r in await conn.fetch(f"SELECT id, nombre FROM {TABLA}")
        }

        nuevos = actualizados = sin_mun = 0

        for row in records:
            nombre = _get(row, "nombre")
            if not nombre:
                continue

            tipo        = _get(row, "tipo", default="")
            es_archi    = _es_archidiocesis(tipo)
            obispo      = _get(row, "obispo_nombre", "obispo") or None
            mun_nombre  = _get(row, "municipio", "sede", "ciudad").lower()
            prov_nombre = _get(row, "provincia").lower()
            telefono    = _get(row, "telefono") or None
            sitio_web   = _get(row, "web", "sitio_web", "sitio_web_propio") or None
            email       = _get(row, "email") or None

            municipio_id = mun_prov.get((mun_nombre, prov_nombre))
            if not municipio_id and mun_nombre:
                # Fallback: solo por nombre municipio
                candidatos = [v for (m, p), v in mun_prov.items() if m == mun_nombre]
                municipio_id = candidatos[0] if len(candidatos) == 1 else None
            if not municipio_id:
                sin_mun += 1

            if nombre in existentes:
                await conn.execute(
                    f"""UPDATE {TABLA} SET
                        es_archidiocesis = $1,
                        obispo_nombre    = COALESCE(NULLIF($2,''), obispo_nombre),
                        telefono         = COALESCE(NULLIF($3,''), telefono),
                        sitio_web_propio = COALESCE(NULLIF($4,''), sitio_web_propio),
                        email_personal   = COALESCE(NULLIF($5,''), email_personal),
                        municipio_id     = COALESCE($6, municipio_id),
                        updated_at       = $7
                    WHERE id = $8""",
                    es_archi, obispo, telefono, sitio_web, email,
                    municipio_id, now, existentes[nombre],
                )
                actualizados += 1
            else:
                new_id = str(uuid.uuid4())
                await conn.execute(
                    f"""INSERT INTO {TABLA}
                        (id, created_at, updated_at, created_by_id,
                         nombre, es_archidiocesis, obispo_nombre,
                         telefono, sitio_web_propio, email_personal, municipio_id)
                        VALUES ($1,$2,$2,$3,$4,$5,$6,$7,$8,$9,$10)
                        ON CONFLICT (nombre) DO NOTHING""",
                    new_id, now, ETL_USER_ID,
                    nombre, es_archi, obispo,
                    telefono, sitio_web, email, municipio_id,
                )
                existentes[nombre] = new_id
                nuevos += 1

        log.info(f"  Diócesis: {nuevos} nuevas, {actualizados} actualizadas")
        if sin_mun:
            log.warning(f"  {sin_mun} sin municipio resuelto")

    finally:
        await conn.close()

    log.info("✓ Diócesis cargadas desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L5b: diócesis desde ODMGR (CEE)")
    parser.add_argument("--odmgr-url", default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-fields", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.list_fields))
