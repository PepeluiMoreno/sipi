#!/usr/bin/env python3
"""
load/enriquecer_er_confer.py — Vincula entidades religiosas RER con CONFER.

CONFER (Conferencia Española de Religiosos) publica su mapa de congregaciones
y comunidades. Este script cruza los datos extraídos de CONFER con las entidades
del RER para enriquecer el censo con:
  - Página web oficial CONFER
  - Tipos de entidad CONFER (Casa de Congregación, Obra propia, etc.)
  - Marca de afiliación a CONFER
  - Datos de comunidades/casas con localidad y provincia CONFER

Fuentes de datos:
  data/output/confer/congregaciones.jsonl   — 399 congregaciones CONFER
  data/output/confer/comunidades.jsonl      — 4.153 comunidades/casas CONFER

Estrategia de matching RER ↔ CONFER:
  1. Exact match: nombre RER normalizado = nombre CONFER normalizado
  2. Partial match: uno contiene al otro tras normalización
  3. Los sin match quedan marcados para revisión manual

El campo codigo_natural = 'CONFER:' + nombre_confer (slug) actúa como clave
estable para posteriores actualizaciones.

Uso:
    python load/enriquecer_er_confer.py
    python load/enriquecer_er_confer.py --dry-run
    python load/enriquecer_er_confer.py --informe   # solo muestra stats, no modifica
"""

import argparse
import asyncio
import json
import logging
import re
from pathlib import Path
from datetime import datetime

import asyncpg
import os

load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

CONFER_DIR = Path(__file__).parent.parent / "data" / "output" / "confer"


def _norm(texto: str) -> str:
    """Normaliza para matching: sin tildes, sin puntuación, minúsculas."""
    tabla = str.maketrans("áéíóúÁÉÍÓÚàèìòùüÜñÑ", "aeiouAEIOUaeiouuUnn")
    return re.sub(r"[^a-z0-9 ]", " ", texto.lower().translate(tabla)).strip()


def cargar_jsonl(path: Path) -> list[dict]:
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


async def main(dry_run: bool, solo_informe: bool):
    # ── Cargar datos CONFER ────────────────────────────────────────────────────
    cong_path = CONFER_DIR / "congregaciones.jsonl"
    com_path  = CONFER_DIR / "comunidades.jsonl"

    if not cong_path.exists():
        log.error(f"No existe {cong_path}. Ejecuta primero: python extract/confer/extract_confer.py")
        return

    congregaciones = cargar_jsonl(cong_path)
    comunidades    = cargar_jsonl(com_path) if com_path.exists() else []
    log.info(f"CONFER: {len(congregaciones)} congregaciones, {len(comunidades)} comunidades")

    # Índice CONFER: nombre_norm → datos
    indice_confer: dict[str, dict] = {
        _norm(c["nombre_confer"]): c
        for c in congregaciones
        if c.get("nombre_confer")
    }

    # ── Conectar a BD ──────────────────────────────────────────────────────────
    db_url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    now  = datetime.now()

    try:
        # ── Cargar entidades religiosas nivel 1 de la BD ───────────────────────
        entidades = await conn.fetch("""
            SELECT er.id, er.nombre, er.sitio_web
            FROM sipi.entidades_religiosas er
            JOIN sipi.tipos_entidad_religiosa t ON t.id = er.tipo_entidad_id
            WHERE t.nivel = 1
              AND er.deleted_at IS NULL
        """)
        log.info(f"BD: {len(entidades)} entidades de nivel 1")

        # ── Matching RER ↔ CONFER ──────────────────────────────────────────────
        exactas = parciales = sin_match = 0
        actualizaciones: list[tuple] = []

        for er in entidades:
            nombre_norm = _norm(er["nombre"])
            confer_data = indice_confer.get(nombre_norm)
            match_tipo  = None

            if confer_data:
                match_tipo = "exacto"
                exactas += 1
            else:
                # Partial: buscar si nombre CONFER contiene el nombre RER o viceversa
                for cnorm, cdata in indice_confer.items():
                    if nombre_norm in cnorm or cnorm in nombre_norm:
                        confer_data = cdata
                        match_tipo  = "parcial"
                        break
                if confer_data:
                    parciales += 1
                else:
                    sin_match += 1

            if confer_data:
                actualizaciones.append((
                    str(er["id"]),
                    confer_data.get("pagina_web"),
                    True,                        # afiliada_confer
                    confer_data.get("nombre_confer"),
                ))

        log.info(
            f"Matching: {exactas} exactos, {parciales} parciales, {sin_match} sin match"
        )

        if solo_informe:
            log.info("[INFORME] No se aplican cambios")
            return

        # ── Verificar columnas necesarias en BD ───────────────────────────────
        cols_er = {
            r["column_name"]
            for r in await conn.fetch(
                "SELECT column_name FROM information_schema.columns "
                "WHERE table_schema='sipi' AND table_name='entidades_religiosas'"
            )
        }
        tiene_sitio_web     = "sitio_web"         in cols_er
        tiene_afil_confer   = "afiliada_confer"   in cols_er
        tiene_nombre_confer = "nombre_confer"     in cols_er

        # ── Aplicar actualizaciones ────────────────────────────────────────────
        if not dry_run and actualizaciones:
            log.info(f"Aplicando {len(actualizaciones)} actualizaciones…")
            for entidad_id, web, afil, nombre_confer in actualizaciones:
                sets  = ["updated_at = $2"]
                vals  = [entidad_id, now]
                idx   = 3

                # Web CONFER: rellenar solo si la entidad no tiene sitio_web del RER
                if tiene_sitio_web and web:
                    sets.append(f"sitio_web = COALESCE(sitio_web, ${idx})")
                    vals.append(web); idx += 1

                if tiene_afil_confer:
                    sets.append(f"afiliada_confer = ${idx}")
                    vals.append(afil); idx += 1

                if tiene_nombre_confer and nombre_confer:
                    sets.append(f"nombre_confer = ${idx}")
                    vals.append(nombre_confer); idx += 1

                await conn.execute(
                    f"UPDATE sipi.entidades_religiosas SET {', '.join(sets)} WHERE id = $1",
                    *vals,
                )

        # ── Estadísticas finales ───────────────────────────────────────────────
        afiliadas = await conn.fetchval(
            "SELECT COUNT(*) FROM sipi.entidades_religiosas "
            "WHERE afiliada_confer = true AND deleted_at IS NULL"
        ) if tiene_afil_confer else "N/A (columna no existe aún)"

        log.info(
            f"Completado: {len(actualizaciones)} entidades vinculadas a CONFER "
            f"(afiliadas en BD: {afiliadas})"
            + (" [DRY-RUN]" if dry_run else "")
        )

        if sin_match > 0:
            log.info(
                f"ATENCIÓN: {sin_match} entidades de nivel 1 sin match CONFER. "
                f"Pueden ser no afiliadas o con nombre muy distinto."
            )

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Vincula entidades RER con CONFER")
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--informe",  action="store_true",
                        help="Solo muestra estadísticas, no modifica BD")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run, args.informe))
