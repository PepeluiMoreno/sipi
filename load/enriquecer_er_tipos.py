#!/usr/bin/env python3
"""
load/enriquecer_er_tipos.py — Normaliza la taxonomía de tipos de entidad religiosa.

Problema: el ETL de extracción crea tipos on-the-fly con los textos literales del
RER. Esto genera duplicados y entradas sin nivel asignado cuando el código ya existía
con un nombre distinto o fue creado antes de introducir la columna nivel.

Este script:
  1. Consolida tipos con el mismo nombre canónico (agrupa variantes)
  2. Asigna nivel (1 = autónoma, 2 = subordinada) según el nombre
  3. Reasigna las entidades de tipos eliminados al tipo canónico
  4. Genera un informe de cambios

Taxonomía canónica (nivel 1 = entidad madre, nivel 2 = entidad local):
  ORDEN_CONGREGACION_INSTITUTO  nivel=1   Orden, Congregación o Instituto
  ASOCIACION                    nivel=1   Asociación
  FEDERACION                    nivel=1   Federación
  FUNDACION                     nivel=1   Fundación
  IGLESIA_COMUNIDAD_CONFESION   nivel=1   Iglesia, Comunidad o Confesión
  ENTIDAD_RELIGIOSA_GENERICA    nivel=1   Entidad Religiosa (genérica)
  CASA                          nivel=2   Casa / Comunidad / Convento
  PROVINCIA                     nivel=2   Provincia canónica
  SIN_TIPO                      nivel=None Sin clasificación conocida

Uso:
    python load/enriquecer_er_tipos.py
    python load/enriquecer_er_tipos.py --dry-run
"""

import argparse
import asyncio
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
import os

load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


# ── Taxonomía canónica ─────────────────────────────────────────────────────────
# (codigo, nombre_oficial, nivel)
TIPOS_CANONICOS = [
    ("ORDEN_CONGREGACION_INSTITUTO", "Orden, Congregación o Instituto", 1),
    ("ASOCIACION",                   "Asociación",                      1),
    ("FEDERACION",                   "Federación",                      1),
    ("FUNDACION",                    "Fundación",                       1),
    ("IGLESIA_COMUNIDAD_CONFESION",  "Iglesia, Comunidad o Confesión",  1),
    ("ENTIDAD_RELIGIOSA_GENERICA",   "Entidad Religiosa",               1),
    ("CASA",                         "Casa / Comunidad / Convento",     2),
    ("PROVINCIA",                    "Provincia canónica",              2),
    ("SIN_TIPO",                     "Sin clasificación conocida",      None),
]

# Mapeo de variantes de nombre (sin tilde, sin puntuación, mayúsculas) → codigo canónico
def _normalizar(texto: str) -> str:
    """Normaliza un nombre de tipo para comparación: mayúsculas, sin tildes, sin puntuación."""
    tabla = str.maketrans("áéíóúÁÉÍÓÚàèìòùüÜ", "aeiouAEIOUaeiouuU")
    return re.sub(r"[^A-Z0-9 ]", "", texto.upper().translate(tabla)).strip()


VARIANTES: dict[str, str] = {
    # Variantes → codigo canónico
    "ORDEN CONGREGACION O INSTITUTO":           "ORDEN_CONGREGACION_INSTITUTO",
    "ORDEN CONGREGACION INSTITUTO":             "ORDEN_CONGREGACION_INSTITUTO",
    "ORDEN  CONGREGACION O INSTITUTO":          "ORDEN_CONGREGACION_INSTITUTO",
    "CONGREGACION":                             "ORDEN_CONGREGACION_INSTITUTO",
    "ORDEN RELIGIOSA":                          "ORDEN_CONGREGACION_INSTITUTO",
    "INSTITUTO RELIGIOSO":                      "ORDEN_CONGREGACION_INSTITUTO",
    "SOCIEDAD DE VIDA APOSTOLICA":              "ORDEN_CONGREGACION_INSTITUTO",
    "ASOCIACION":                               "ASOCIACION",
    "ASOCIACIONES":                             "ASOCIACION",
    "FEDERACION":                               "FEDERACION",
    "FEDERACIONES":                             "FEDERACION",
    "FUNDACION":                                "FUNDACION",
    "IGLESIA COMUNIDAD O CONFESION":            "IGLESIA_COMUNIDAD_CONFESION",
    "IGLESIA O COMUNIDAD":                      "IGLESIA_COMUNIDAD_CONFESION",
    "IGLESIA":                                  "IGLESIA_COMUNIDAD_CONFESION",
    "ENTIDAD RELIGIOSA":                        "ENTIDAD_RELIGIOSA_GENERICA",
    "ENTIDAD":                                  "ENTIDAD_RELIGIOSA_GENERICA",
    "CASA":                                     "CASA",
    "CASA DE CONGREGACION":                     "CASA",
    "COMUNIDAD":                                "CASA",
    "CONVENTO":                                 "CASA",
    "MONASTERIO":                               "CASA",
    "PROVINCIA":                                "PROVINCIA",
    "PROVINCIA CANONICA":                       "PROVINCIA",
    "PROVINCIA RELIGIOSA":                      "PROVINCIA",
    "SIN TIPO":                                 "SIN_TIPO",
    "SIN TIPO DE ENTIDAD":                      "SIN_TIPO",
    "SIN CLASIFICAR":                           "SIN_TIPO",
}


def _resolver_codigo(nombre: str) -> str:
    """Devuelve el código canónico para un nombre de tipo dado."""
    normalizado = _normalizar(nombre)
    # Coincidencia exacta
    if normalizado in VARIANTES:
        return VARIANTES[normalizado]
    # Coincidencia parcial: buscar si el nombre normalizado contiene alguna clave
    for clave, codigo in VARIANTES.items():
        if clave in normalizado:
            return codigo
    return "ENTIDAD_RELIGIOSA_GENERICA"


async def main(dry_run: bool):
    url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    now = datetime.now()

    try:
        async with conn.transaction():
            # ── 1. Asegurar tipos canónicos existen en BD ──────────────────────
            log.info("=== Paso 1: sincronizar tipos canónicos ===")
            id_por_codigo: dict[str, str] = {}

            for codigo, nombre, nivel in TIPOS_CANONICOS:
                row = await conn.fetchrow(
                    "SELECT id FROM sipi.tipos_entidad_religiosa WHERE codigo = $1", codigo
                )
                if row:
                    id_por_codigo[codigo] = str(row["id"])
                    if not dry_run:
                        await conn.execute(
                            """UPDATE sipi.tipos_entidad_religiosa
                               SET nombre=$1, nivel=$2, updated_at=$3
                               WHERE codigo=$4""",
                            nombre, nivel, now, codigo,
                        )
                    log.info(f"  Actualizado: {codigo} (nivel={nivel})")
                else:
                    new_id = str(uuid.uuid4())
                    id_por_codigo[codigo] = new_id
                    if not dry_run:
                        await conn.execute(
                            """INSERT INTO sipi.tipos_entidad_religiosa
                               (id, codigo, nombre, nivel, activo, created_at)
                               VALUES ($1,$2,$3,$4,true,$5)""",
                            new_id, codigo, nombre, nivel, now,
                        )
                    log.info(f"  Creado: {codigo} (nivel={nivel})")

            # ── 2. Reasignar entidades con tipos no canónicos ──────────────────
            log.info("=== Paso 2: reasignar entidades con tipos no canónicos ===")

            tipos_actuales = await conn.fetch(
                "SELECT id, codigo, nombre FROM sipi.tipos_entidad_religiosa"
            )
            reasignaciones = 0
            tipos_a_eliminar = []

            for tipo in tipos_actuales:
                if tipo["codigo"] in [t[0] for t in TIPOS_CANONICOS]:
                    continue  # ya es canónico

                codigo_canonico = _resolver_codigo(tipo["nombre"])
                id_canonico = id_por_codigo.get(codigo_canonico)
                if not id_canonico:
                    log.warning(f"  Sin canónico para: {tipo['nombre']} → {codigo_canonico}")
                    continue

                n = await conn.fetchval(
                    "SELECT COUNT(*) FROM sipi.entidades_religiosas WHERE tipo_entidad_id = $1",
                    tipo["id"],
                )
                log.info(f"  {tipo['codigo']} ({n} entidades) → {codigo_canonico}")

                if not dry_run and n > 0:
                    await conn.execute(
                        """UPDATE sipi.entidades_religiosas
                           SET tipo_entidad_id=$1, updated_at=$2
                           WHERE tipo_entidad_id=$3""",
                        id_canonico, now, tipo["id"],
                    )
                    reasignaciones += n

                tipos_a_eliminar.append(tipo["id"])

            # ── 3. Eliminar tipos no canónicos (ya sin referencias) ────────────
            log.info(f"=== Paso 3: eliminar {len(tipos_a_eliminar)} tipos no canónicos ===")
            if not dry_run:
                for tid in tipos_a_eliminar:
                    await conn.execute(
                        "DELETE FROM sipi.tipos_entidad_religiosa WHERE id=$1", tid
                    )

            log.info(
                f"Completado: {reasignaciones} entidades reasignadas, "
                f"{len(tipos_a_eliminar)} tipos eliminados"
                + (" [DRY-RUN]" if dry_run else "")
            )

            if dry_run:
                raise Exception("DRY-RUN: rollback")

    except Exception as e:
        if "DRY-RUN" not in str(e):
            log.error(f"Error: {e}")
            raise
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Normaliza tipos de entidad religiosa")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))
