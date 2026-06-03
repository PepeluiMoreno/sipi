#!/usr/bin/env python3
"""
load/enriquecer_er_nivel_superior.py — Resuelve el nivel_superior_id de entidades subordinadas.

Las entidades de nivel 2 (CASA, PROVINCIA) contienen en el campo `congregacion` el nombre
de la orden o congregación madre (parseado del campo "Congregación y provincia" del RER).

Este script busca la entidad de nivel 1 (ORDEN_CONGREGACION_INSTITUTO, ASOCIACION, etc.)
cuyo nombre coincida mejor con el campo congregacion, y establece nivel_superior_id.

Estrategia de matching (en orden de confianza y robustez):
  1. Coincidencia exacta (nombre completamente normalizado)
     → Confianza: muy alta. Sin falsos positivos.
  
  2. Coincidencia multi-palabra (>=2 palabras clave en común)
     → Estrategia: split en palabras, intersección, score por similitud
     → Ejemplo: "CONGREGACIÓN DE JESÚS MARÍA" + "JESÚS MARÍA" (nivel1)
     → Confianza: alta.
  
  3. Substring (substring bi-directional)
     → Ejemplo: cong_norm in nombre_norm OR nombre_norm in cong_norm
     → Confianza: media (puede dar falsos positivos).
     → Fallback: solo si 1 y 2 fallan.

Pre-requisito: haber ejecutado enriquecer_er_tipos.py para que los tipos tengan nivel=1/2.

Nota: Los códigos naturales (numero_registro) se usan como índices únicos en la BD,
permitiendo relaciones 1:M confiables y reanudabilidad en actualizaciones futuras.

Uso:
    python load/enriquecer_er_nivel_superior.py              # ejecución normal
    python load/enriquecer_er_nivel_superior.py --dry-run    # simulación sin cambios
"""

import argparse
import asyncio
import logging
import re
from datetime import datetime
from pathlib import Path

import asyncpg
import os

load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _normalizar(texto: str) -> str:
    """Normaliza para comparación: minúsculas, sin tildes, sin puntuación."""
    tabla = str.maketrans("áéíóúÁÉÍÓÚàèìòùüÜñÑ", "aeiouAEIOUaeiouuUnn")
    return re.sub(r"[^a-z0-9 ]", " ", texto.lower().translate(tabla)).strip()


async def main(dry_run: bool):
    url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)
    now = datetime.now()

    try:
        # ── Cargar entidades de nivel 1 como índice de búsqueda ───────────────
        log.info("=== Cargando entidades de nivel 1 ===")
        nivel1 = await conn.fetch("""
            SELECT er.id, er.nombre, er.numero_registro
            FROM sipi.entidades_religiosas er
            JOIN sipi.tipos_entidad_religiosa t ON t.id = er.tipo_entidad_id
            WHERE t.nivel = 1
              AND er.deleted_at IS NULL
        """)
        log.info(f"  {len(nivel1)} entidades de nivel 1")

        # Índice: nombre_normalizado → id
        indice: dict[str, str] = {
            _normalizar(r["nombre"]): str(r["id"])
            for r in nivel1
        }

        # ── Cargar subordinadas que aún no tienen nivel_superior_id ───────────
        log.info("=== Cargando entidades subordinadas sin nivel superior ===")
        subordinadas = await conn.fetch("""
            SELECT er.id, er.congregacion, er.nombre, er.numero_registro, er.tipo_entidad_id
            FROM sipi.entidades_religiosas er
            JOIN sipi.tipos_entidad_religiosa t ON t.id = er.tipo_entidad_id
            WHERE t.nivel = 2
              AND er.nivel_superior_id IS NULL
              AND er.congregacion IS NOT NULL
              AND er.deleted_at IS NULL
        """)
        log.info(f"  {len(subordinadas)} subordinadas con congregacion sin resolver")

        # ── Resolver nivel_superior_id ─────────────────────────────────────────
        # Estrategia multi-nivel (en orden de confianza):
        # 1. Coincidencia exacta por nombre normalizado
        # 2. Coincidencia parcial (substring bi-directional)
        # 3. Similitud trigram usando Postgres (si lo soporta)
        exactas = parciales = sin_match = 0
        actualizaciones: list[tuple[str, str]] = []  # (nivel_superior_id, entidad_id)

        for row in subordinadas:
            cong = row["congregacion"]
            cong_norm = _normalizar(cong)
            entidad_id = str(row["id"])

            # 1. Coincidencia exacta (más confiable — sin falsos positivos)
            sup_id = indice.get(cong_norm)
            if sup_id:
                actualizaciones.append((sup_id, entidad_id))
                exactas += 1
                continue

            # 2. Coincidencia parcial mejorada:
            #    - Buscar si algún "palabra clave" de la congregación coincide
            #    - Dar prioridad a matching más largo (mejor especificidad)
            palabras_cong = set(cong_norm.split())
            mejores_matches: list[tuple[int, str]] = []  # (score, sup_id)
            
            for nombre_norm, nid in indice.items():
                palabras_nivel1 = set(nombre_norm.split())
                
                # Score 1: intersección de palabras clave (matches > 1 palabra)
                interseccion = palabras_cong & palabras_nivel1
                if len(interseccion) >= 2:
                    # Penalizar si la subordinada es más larga (evita falsos positivos)
                    score = len(interseccion) - abs(len(cong_norm) - len(nombre_norm)) / 100
                    mejores_matches.append((score, nid))
                
                # Score 2: substring containment (fallback menos confiable)
                elif cong_norm in nombre_norm or nombre_norm in cong_norm:
                    score = 0.5  # menor prioridad
                    mejores_matches.append((score, nid))
            
            if mejores_matches:
                mejores_matches.sort(reverse=True, key=lambda x: x[0])
                sup_id = mejores_matches[0][1]
                actualizaciones.append((sup_id, entidad_id))
                parciales += 1
                continue

            sin_match += 1

        log.info(
            f"  Exactas: {exactas}, Parciales (multi-palabra): {parciales}, Sin match: {sin_match}"
        )

        # ── Aplicar actualizaciones ────────────────────────────────────────────
        if not dry_run and actualizaciones:
            log.info(f"=== Aplicando {len(actualizaciones)} actualizaciones ===")
            await conn.executemany(
                """UPDATE sipi.entidades_religiosas
                   SET nivel_superior_id=$1, updated_at=$2
                   WHERE id=$3""",
                [(sup_id, now, entidad_id) for sup_id, entidad_id in actualizaciones],
            )

        # ── Informe final ──────────────────────────────────────────────────────
        total_vinculadas = await conn.fetchval(
            "SELECT COUNT(*) FROM sipi.entidades_religiosas WHERE nivel_superior_id IS NOT NULL"
        )
        log.info(
            f"Completado: {len(actualizaciones)} vínculos establecidos "
            f"(total en BD: {total_vinculadas})"
            + (" [DRY-RUN]" if dry_run else "")
        )

    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Resuelve nivel_superior_id en entidades religiosas")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Simula los cambios sin escribir en BD")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run))
