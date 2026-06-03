#!/usr/bin/env python3
"""
load/cargar_administraciones_odmgr.py — L8b: carga administraciones desde ODMGR (DIR3)

Reemplaza cargar_administraciones.py (que leía CSV local) con lectura directa
desde el dataset DIR3 en OpenDataManager.

Fuente ODMGR: dir3_unidades (DIR3 - Unidades Orgánicas de España)
    Query:  dir3UnidadesOrganicasDeEspana
    Fuente original: JDA API → https://datos.juntadeandalucia.es/api/v0/dir3/all

Campos DIR3 (posibles nombres — la API JDA puede variar):
    codigo / codigoDir3    → codigo_oficial en sipi.administraciones
    denominacion / nombre  → nombre
    nivel / nivelJerarquico → nivel_jerarquico (1–4)
    padre / codigoPadre    → administracion_padre_id (2ª pasada)
    estado (V=vigente)
    fechaAlta, fechaBaja
    codigoCCAA / codigoComunidadAutonoma
    codigoProv / codigoProvincia
    codigoMun / codigoMunicipio
    tipoOrgano / tipoUnidadOrganica
    ambito / ambitoUnidadOrganica

Idempotente: INSERT / UPDATE por codigo_oficial.
Solo procesa niveles 1–4 y unidades vigentes (estado = V o campo ausente).

Uso:
    python load/cargar_administraciones_odmgr.py
    python load/cargar_administraciones_odmgr.py --odmgr-url http://172.18.0.3:8000
    python load/cargar_administraciones_odmgr.py --dry-run
    python load/cargar_administraciones_odmgr.py --list-fields
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

Q_DIR3 = resource_name_to_query("DIR3 - Unidades Orgánicas de España")

# Campos a pedir a ODMGR (superset — tomar el primero disponible en cada grupo)
FIELDS = [
    "codigo", "codigoDir3", "id",
    "denominacion", "nombre",
    "nivel", "nivelJerarquico",
    "padre", "codigoPadre", "codigoUnidadOrganicaPadre",
    "estado",
    "fechaAlta", "fechaAltaOficial",
    "fechaBaja", "fechaBajaOficial",
    "codigoCCAA", "codigoComunidadAutonoma",
    "codigoProv", "codigoProvincia",
    "codigoMun", "codigoMunicipio",
    "tipoOrgano", "tipoUnidadOrganica",
    "ambito", "ambitoUnidadOrganica",
]

AMBITO_MAP = {
    "E": "estatal", "A": "autonomico", "L": "local",
    "U": "universitario", "J": "judicial", "O": "otro",
}

TABLA = "sipi.administraciones"
BATCH  = 500


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


def _get(row: dict, *keys: str, default: str = "") -> str:
    for k in keys:
        v = row.get(k) or row.get(k.lower()) or ""
        if v:
            return str(v).strip()
    return default


def parse_fecha(s: str) -> datetime | None:
    if not s or str(s).strip() in ("", "null", "NULL", "None"):
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%Y%m%d"):
        try:
            return datetime.strptime(str(s).strip(), fmt)
        except ValueError:
            continue
    return None


async def main(odmgr_url: str, dry_run: bool, list_fields: bool, nivel_max: int):
    client = ODMGRClient(odmgr_url)

    log.info(f"Descargando DIR3 desde ODMGR: {odmgr_url}")
    records = list(client.fetch_all(Q_DIR3, FIELDS))
    log.info(f"  {len(records):,} unidades en ODMGR")

    if not records:
        log.warning("  Sin datos. ¿El recurso 'DIR3 - Unidades Orgánicas de España' ha sido ejecutado en ODMGR?")
        return

    if list_fields:
        log.info("Campos del 1er registro:")
        for k, v in records[0].items():
            log.info(f"  {k!r}: {v!r}")
        return

    # Filtrar: solo niveles 1–nivel_max y vigentes
    filtrados = []
    for row in records:
        estado = _get(row, "estado", default="V")
        if estado not in ("V", "v", "", "vigente"):
            continue
        nivel_raw = _get(row, "nivel", "nivelJerarquico")
        try:
            nivel = int(nivel_raw)
        except (ValueError, TypeError):
            nivel = 99
        if nivel > nivel_max:
            continue
        filtrados.append((row, nivel))
    log.info(f"  {len(filtrados):,} unidades (niveles 1–{nivel_max}, vigentes)")

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")
        return

    conn = await asyncpg.connect(get_dsn())
    try:
        await conn.execute("SET search_path TO sipi, public")
        await verificar_etluser(conn)
        now = datetime.utcnow()

        # ── Mapas geográficos ────────────────────────────────────────────────
        ccaa_map: dict[str, str] = {
            r["codigo_ine"].zfill(2): r["id"]
            for r in await conn.fetch("SELECT id, codigo_ine FROM sipi.comunidades_autonomas WHERE codigo_ine IS NOT NULL")
        }
        prov_map: dict[str, str] = {
            r["codigo"].zfill(2): r["id"]
            for r in await conn.fetch("SELECT id, codigo FROM sipi.provincias WHERE codigo IS NOT NULL")
        }
        mun_map: dict[str, str] = {
            r["codigo_ine"]: r["id"]
            for r in await conn.fetch("SELECT id, codigo_ine FROM sipi.municipios WHERE codigo_ine IS NOT NULL")
        }

        # ── Existentes ───────────────────────────────────────────────────────
        result = await conn.fetch("SELECT id, codigo_oficial FROM sipi.administraciones WHERE codigo_oficial IS NOT NULL")
        existentes: dict[str, str] = {r["codigo_oficial"]: r["id"] for r in result}

        # ── 1ª pasada: insertar / actualizar ─────────────────────────────────
        nuevas = actualizadas = 0

        for row, nivel in filtrados:
            codigo = _get(row, "codigo", "codigoDir3", "id")
            if not codigo:
                continue

            nombre        = _get(row, "denominacion", "nombre")
            tipo_organo   = _get(row, "tipoOrgano", "tipoUnidadOrganica") or None
            ambito_raw    = _get(row, "ambito", "ambitoUnidadOrganica") or ""
            ambito        = AMBITO_MAP.get(ambito_raw.upper()[:1], ambito_raw.lower() or None)
            fecha_alta    = parse_fecha(_get(row, "fechaAlta", "fechaAltaOficial")) or now
            fecha_baja    = parse_fecha(_get(row, "fechaBaja", "fechaBajaOficial"))

            cod_ccaa = _get(row, "codigoCCAA", "codigoComunidadAutonoma").zfill(2) if _get(row, "codigoCCAA", "codigoComunidadAutonoma") else ""
            cod_prov = _get(row, "codigoProv", "codigoProvincia").zfill(2) if _get(row, "codigoProv", "codigoProvincia") else ""
            cod_mun  = _get(row, "codigoMun", "codigoMunicipio") or ""

            ca_id   = ccaa_map.get(cod_ccaa) if cod_ccaa else None
            prov_id = prov_map.get(cod_prov) if cod_prov else None
            mun_id  = mun_map.get(cod_mun) if cod_mun else None

            if codigo in existentes:
                await conn.execute(
                    f"""UPDATE {TABLA} SET
                        nombre = $1, nivel_jerarquico = $2,
                        tipo_organo = $3, ambito = $4,
                        valido_desde = $5, valido_hasta = $6,
                        activa = $7,
                        comunidad_autonoma_id = COALESCE($8, comunidad_autonoma_id),
                        provincia_id = COALESCE($9, provincia_id),
                        municipio_sede_id = COALESCE($10, municipio_sede_id)
                    WHERE id = $11""",
                    nombre, str(nivel), tipo_organo, ambito,
                    fecha_alta, fecha_baja, (fecha_baja is None),
                    ca_id, prov_id, mun_id,
                    existentes[codigo],
                )
                actualizadas += 1
            else:
                adm_id = str(uuid.uuid4())
                await conn.execute(
                    f"""INSERT INTO {TABLA}
                        (id, created_at, created_by_id, nombre, codigo_oficial,
                         nivel_jerarquico, tipo_organo, ambito,
                         valido_desde, valido_hasta, activa,
                         comunidad_autonoma_id, provincia_id, municipio_sede_id)
                        VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14)
                        ON CONFLICT (codigo_oficial) DO NOTHING""",
                    adm_id, now, ETL_USER_ID, nombre, codigo,
                    str(nivel), tipo_organo, ambito,
                    fecha_alta, fecha_baja, (fecha_baja is None),
                    ca_id, prov_id, mun_id,
                )
                existentes[codigo] = adm_id
                nuevas += 1

        log.info(f"  1ª pasada: {nuevas} nuevas, {actualizadas} actualizadas")

        # ── 2ª pasada: jerarquía (padre) ──────────────────────────────────────
        resueltos = huerfanos = 0
        for row, _ in filtrados:
            codigo      = _get(row, "codigo", "codigoDir3", "id")
            cod_padre   = _get(row, "padre", "codigoPadre", "codigoUnidadOrganicaPadre")
            if not cod_padre or cod_padre == codigo:
                continue
            hijo_id  = existentes.get(codigo)
            padre_id = existentes.get(cod_padre)
            if hijo_id and padre_id:
                await conn.execute(
                    f"UPDATE {TABLA} SET administracion_padre_id = $1 WHERE id = $2",
                    padre_id, hijo_id
                )
                resueltos += 1
            else:
                huerfanos += 1

        log.info(f"  2ª pasada: {resueltos} relaciones resueltas"
                 + (f", {huerfanos} huérfanos" if huerfanos else ""))

    finally:
        await conn.close()

    log.info("✓ Administraciones cargadas desde ODMGR")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="L8b: carga administraciones DIR3 desde ODMGR")
    parser.add_argument("--odmgr-url", default=os.environ.get("ODMGR_URL", "http://172.18.0.3:8000"))
    parser.add_argument("--nivel-max", type=int, default=4, help="Nivel jerárquico máximo a importar (default: 4)")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--list-fields", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.odmgr_url, args.dry_run, args.list_fields, args.nivel_max))
