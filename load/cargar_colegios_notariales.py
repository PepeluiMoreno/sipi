#!/usr/bin/env python3
"""
load/cargar_colegios_notariales.py
— Carga Colegios Notariales en sipi.colegios_profesionales

Lee:    data/input/notarios/colegios_notariales.csv  (generado por E4)
Carga:  sipi.colegios_profesionales

Resolución de FKs:
  - municipio_id          → sipi.municipios   por slug de nombre
  - comunidad_autonoma_id → via municipio
  - tipo_via_id           → sipi.tipos_via    por nombre normalizado
  - provincia_id          → via municipio

Uso:
    python load/cargar_colegios_notariales.py
    python load/cargar_colegios_notariales.py --dry-run
"""

import asyncio
import csv
import re
import sys
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from config import cfg, dsn

from utils.etl_audit import ETL_USER_ID, verificar_etluser

try:
    import asyncpg
except ImportError:
    print("ERROR: pip install asyncpg")
    sys.exit(1)

INPUT = Path(__file__).parent.parent / "data" / "input" / "notarios" / "colegios_notariales.csv"


def slugify(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto)
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


# Municipios cuyo nombre en el CSV no coincide con el nombre INE en BD
MUNICIPIO_ALIAS: dict[str, str] = {
    "a-coruna":                      "coruna-a",
    "las-palmas-de-gran-canaria":    "palmas-de-gran-canaria-las",
    "pamplona":                      "pamplona-iruna",
}


def codigo_colegio(nombre: str, municipio: str) -> str:
    """Genera código único: CNOTAR-{slug_municipio}"""
    return f"CNOTAR-{slugify(municipio).upper()[:20]}"


async def cargar(dry_run: bool = False):
    if not INPUT.exists():
        print(f"ERROR: no encontrado {INPUT}")
        print("       Ejecuta primero: python extract/colegios-notariales/descargar_colegios_notariales.py")
        sys.exit(1)

    with open(INPUT, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    print(f"  {len(filas)} colegios en CSV")

    conn = await asyncpg.connect(dsn())
    try:
        await verificar_etluser(conn)
        # ── Lookups ───────────────────────────────────────────────────────────
        mun_map: dict[str, tuple[str, str, str]] = {}  # slug → (id, ca_id, prov_id)
        for r in await conn.fetch(
            "SELECT id, nombre, provincia_id, comunidad_autonoma_id FROM sipi.municipios"
        ):
            mun_map[slugify(r["nombre"])] = (r["id"], r["comunidad_autonoma_id"], r["provincia_id"])

        via_map: dict[str, str] = {
            slugify(r["nombre"]): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.tipos_via")
        }

        existentes: set[str] = {
            r["codigo"]
            for r in await conn.fetch("SELECT codigo FROM sipi.colegios_profesionales WHERE codigo LIKE 'CNOTAR-%'")
        }

        # ── Insertar ─────────────────────────────────────────────────────────
        insertados = sin_mun = 0

        for row in filas:
            codigo = codigo_colegio(row["nombre"], row["municipio"])
            if codigo in existentes:
                print(f"  SKIP ya existe: {codigo}")
                continue

            mun_slug = slugify(row["municipio"])
            mun_slug = MUNICIPIO_ALIAS.get(mun_slug, mun_slug)
            mun_data = mun_map.get(mun_slug)
            if not mun_data:
                sin_mun += 1
                print(f"  WARN sin municipio: '{row['municipio']}'", file=sys.stderr)

            municipio_id          = mun_data[0] if mun_data else None
            comunidad_autonoma_id = mun_data[1] if mun_data else None
            provincia_id          = mun_data[2] if mun_data else None
            tipo_via_id           = via_map.get(slugify(row["tipo_via"])) if row.get("tipo_via") else None

            # Provincias que abarca → guardadas en notas
            notas = f"Provincias: {row['provincias']}" if row.get("provincias") else None

            # Si el nombre no es único, añadir el municipio sede como disambiguador
            nombre = row["nombre"]
            if sum(1 for r in filas if r["nombre"] == nombre) > 1:
                nombre = f"{nombre} ({row['municipio']})"

            if not dry_run:
                await conn.execute("""
                    INSERT INTO sipi.colegios_profesionales (
                        id, created_at, created_by_id,
                        codigo, nombre,
                        telefono,
                        tipo_via_id, nombre_via, numero, piso, codigo_postal,
                        municipio_id, provincia_id, comunidad_autonoma_id,
                        notas
                    ) VALUES (
                        $1,  $2,  $3,
                        $4,  $5,
                        $6,
                        $7,  $8,  $9,  $10,  $11,
                        $12, $13, $14,
                        $15
                    )
                """,
                    str(uuid.uuid4()), datetime.utcnow(), ETL_USER_ID,
                    codigo, nombre,
                    row["telefono"] or None,
                    tipo_via_id,
                    row["nombre_via"] or None,
                    (row["numero"] or "")[:10] or None,
                    (row["piso"] or "")[:10] or None,
                    row["codigo_postal"] or None,
                    municipio_id, provincia_id, comunidad_autonoma_id,
                    notas,
                )

            insertados += 1
            existentes.add(codigo)

        modo = "[DRY-RUN] " if dry_run else ""
        print(f"  {modo}Insertados: {insertados}")
        if sin_mun:
            print(f"  Sin municipio: {sin_mun}")

    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Carga Colegios Notariales en BD")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    print("Cargando Colegios Notariales…")
    asyncio.run(cargar(args.dry_run))
    print("✓ Completado")
