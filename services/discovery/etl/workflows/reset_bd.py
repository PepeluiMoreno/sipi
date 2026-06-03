#!/usr/bin/env python3
"""
workflows/reset_bd.py — Limpia las tablas pobladas por el ETL

Trunca en orden inverso de dependencia FK para poder volver a ejecutar
el pipeline desde cero. NO elimina la estructura (tablas, índices, etc.),
solo los datos.

Tablas que limpia:
    inmuebles y dependientes  (L5)
    registros_propiedad       (L4)
    administraciones          (L3)
    tipologías                (L2)
    municipios → provincias → comunidades_autonomas  (L1)

⚠️  DESTRUCTIVO: borra todos los datos de las tablas listadas.
    Úsalo solo en entornos de desarrollo/staging.

Uso:
    python workflows/reset_bd.py
    python workflows/reset_bd.py --solo geografia
    python workflows/reset_bd.py --solo tipologias
    python workflows/reset_bd.py --solo inmuebles
    python workflows/reset_bd.py --confirmar   # omite la pregunta interactiva
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

import asyncpg
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

# Grupos de tablas ordenadas por dependencia FK (orden de borrado)
GRUPOS: dict[str, list[str]] = {
    "inmuebles": [
        "sipi.inmuebles_osm_ext",
        "sipi.inmuebles_wd_ext",
        "sipi.inmuebles_documentos",
        "sipi.inmuebles_denominaciones",
        "sipi.inmatriculaciones",
        "sipi.actuaciones_tecnicos",
        "sipi.actuaciones_subvenciones",
        "sipi.actuaciones_documentos",
        "sipi.actuaciones",
        "sipi.transmision_anunciantes",
        "sipi.transmisiones_documentos",
        "sipi.transmisiones",
        "sipi.citas_bibliograficas",
        "sipi.documentos",
        "sipi.inmuebles",
    ],
    "registros": [
        "sipi.registros_propiedad_titulares",
        "sipi.registros_propiedad",
        "sipi.notarias",
    ],
    "administraciones": [
        "sipi.administraciones_titulares",
        "sipi.administraciones",
    ],
    "tipologias": [
        "sipi.tipos_inmueble",
        "sipi.estados_conservacion",
        "sipi.estados_tratamiento",
        "sipi.tipos_documento",
        "sipi.tipos_transmision",
        "sipi.tipos_persona",
        "sipi.tipos_via",
        "sipi.roles_tecnico",
        "sipi.tipos_certificacion_propiedad",
        "sipi.tipos_figura_proteccion",
        "sipi.tipos_licencia",
    ],
    "geografia": [
        "sipi.municipios",
        "sipi.provincias",
        "sipi.comunidades_autonomas",
    ],
}

# Orden de ejecución (más dependientes primero)
ORDEN_GRUPOS = ["inmuebles", "registros", "administraciones", "tipologias", "geografia"]


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


async def reset(grupos: list[str], confirmar: bool):
    tablas = []
    for g in grupos:
        tablas.extend(GRUPOS.get(g, []))

    print("\nTablas a truncar:")
    for t in tablas:
        print(f"  · {t}")

    if not confirmar:
        resp = input("\n¿Continuar? [s/N] ").strip().lower()
        if resp not in ("s", "si", "sí", "y", "yes"):
            print("Cancelado.")
            sys.exit(0)

    conn = await asyncpg.connect(get_dsn())
    try:
        for tabla in tablas:
            try:
                await conn.execute(f"TRUNCATE {tabla} CASCADE")
                print(f"  ✓ {tabla}")
            except Exception as e:
                print(f"  ✗ {tabla}: {e}")
    finally:
        await conn.close()

    print("\n✓ Reset completado")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Limpia tablas ETL para reejecutar el pipeline")
    parser.add_argument("--solo", choices=list(GRUPOS.keys()),
                        help="Limpiar solo este grupo de tablas")
    parser.add_argument("--confirmar", action="store_true",
                        help="No pedir confirmación interactiva")
    args = parser.parse_args()

    grupos = [args.solo] if args.solo else ORDEN_GRUPOS
    asyncio.run(reset(grupos, args.confirmar))
