#!/usr/bin/env python3
"""
load/cargar_registros_propiedad.py
— L4: Carga Registros de la Propiedad en sipi.registros_propiedad

Lee:    data/input/registradores/registros_propiedad.csv  (salida de T4)
Carga:  sipi.registros_propiedad

Resolución de FKs:
  - provincia_id          → sipi.provincias   por codigo = codigo_ine_prov
  - municipio_id          → sipi.municipios   por slug normalizado + provincia_id
  - comunidad_autonoma_id → via municipio
  - tipo_via_id           → sipi.tipos_via    por nombre (normalizado)

Uso:
    python load/cargar_registros_propiedad.py
    python load/cargar_registros_propiedad.py --dry-run
"""

import asyncio
import csv
import os
import re
import sys
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

try:
    import asyncpg
except ImportError:
    print("ERROR: pip install asyncpg")
    sys.exit(1)

load_dotenv(Path(__file__).parent.parent / ".env")

from utils.etl_audit import ETL_USER_ID, verificar_etluser

INPUT = Path(__file__).parent.parent / "data" / "input" / "registradores" / "registros_propiedad.csv"

# Municipios cuyo slug en la URL de registradores.org no coincide con
# el slugify() del nombre oficial INE (bilingüismo, truncados, históricos).
# Clave: slug de la URL  →  Valor: slugify(nombre INE)
SLUG_ALIAS: dict[str, str] = {
    # Alicante — nombres bilingüe invertido (URL: castellano+valenciano, INE: valenciano+castellano)
    "alicantealacant":           "alacant-alicante",
    "alcoyalcoi":                "alcoi-alcoy",
    "calpecalp":                 "calp",
    "elcheelx":                  "elx-elche",
    "javeaxabia":                "xabia-javea",
    "jijonaxixona":              "xixona-jijona",
    "monovarmonover":            "monover-monovar",
    "san-vicente-del-raspeig":   "sant-vicent-del-raspeig-san-vicente-del-raspeig",
    "villajoyosavila-joiosa-la": "vila-joiosa-la-villajoyosa",
    "callosa-den-sarria":        "callosa-d-en-sarria",
    # Baleares — Palma (antes "Palma de Mallorca"), Maó/Mahón
    "palma-de-mallorca":         "palma",
    "mahon":                     "mao",
    # Burgos — slug truncado por longitud
    "villarcayo-de-merindad-de-castilla-la-vi": "villarcayo-de-merindad-de-castilla-la-vieja",
    # Castellón — bilingüe truncado + nombres valenciano+castellano
    "castellon-de-la-planacastello-de-la-pla": "castello-de-la-plana",
    "lucena-del-cid":            "llucena-lucena-del-cid",
    "oropesa-del-marorpesa":     "orpesa-oropesa-del-mar",
    "villarrealvila-real":       "vila-real",
    # Girona
    "bisbal-demporda-la":        "bisbal-d-emporda-la",
    # Lleida
    "seu-durgell-la":            "seu-d-urgell-la",
    # Navarra — bilingüe castellano+euskera
    "aoizagoitz":                "aoiz-agoitz",
    "estellalizarra":            "estella-lizarra",
    "pamplonairuna":             "pamplona-iruna",
    # Valencia
    "saguntosagunt":             "sagunt-sagunto",
}


def get_dsn() -> str:
    url = os.environ["DATABASE_URL"]
    return url.replace("postgresql+asyncpg://", "postgresql://")


def slugify(texto: str) -> str:
    """Normaliza texto para comparación: sin tildes, minúsculas, guiones."""
    nfkd = unicodedata.normalize("NFKD", texto)
    ascii_ = nfkd.encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", ascii_.lower()).strip("-")


def _split_nombre(full_name: str) -> tuple[str, str | None]:
    """Divide nombre completo en (nombre, apellidos). Primera palabra = nombre."""
    parts = full_name.strip().split(None, 1)
    if len(parts) == 1:
        return (parts[0], None)
    return (parts[0], parts[1])


def slug_sin_articulos(slug: str) -> str:
    """Elimina artículos para comparación tolerante: del/de/la/el/los/las."""
    s = re.sub(r"(?:^|-)(del?|las?|los|el)(?=-|$)", "", slug)
    return re.sub(r"-+", "-", s).strip("-")


async def cargar(dry_run: bool = False):
    if not INPUT.exists():
        print(f"ERROR: no encontrado {INPUT}")
        print("       Ejecuta primero: python transform/registradores/transformar_registros_propiedad.py")
        sys.exit(1)

    with open(INPUT, encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    print(f"  {len(filas)} filas en CSV")

    conn = await asyncpg.connect(get_dsn())
    try:
        await verificar_etluser(conn)
        # ── Lookups en memoria ────────────────────────────────────────────────

        # provincias: codigo_ine (2 dígitos) → id
        prov_map: dict[str, str] = {
            r["codigo"]: r["id"]
            for r in await conn.fetch("SELECT id, codigo FROM sipi.provincias")
        }

        # municipios: (slug_nombre, provincia_id) → (municipio_id, ca_id)
        # También índice sin artículos para fallback tolerante
        mun_map: dict[tuple[str, str], tuple[str, str]] = {}
        mun_map_sin_art: dict[tuple[str, str], tuple[str, str]] = {}
        for r in await conn.fetch(
            "SELECT id, nombre, provincia_id, comunidad_autonoma_id FROM sipi.municipios"
        ):
            sl = slugify(r["nombre"])
            val = (r["id"], r["comunidad_autonoma_id"])
            mun_map[(sl, r["provincia_id"])] = val
            mun_map_sin_art[(slug_sin_articulos(sl), r["provincia_id"])] = val

        # tipos_via: slug_nombre → id
        via_map: dict[str, str] = {
            slugify(r["nombre"]): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.tipos_via")
        }

        # registros ya cargados: nombre → (id, nombre_via, codigo_postal)
        existentes: dict[str, dict] = {
            r["nombre"]: {"id": r["id"], "nombre_via": r["nombre_via"], "codigo_postal": r["codigo_postal"]}
            for r in await conn.fetch("SELECT id, nombre, nombre_via, codigo_postal FROM sipi.registros_propiedad")
        }

        # registros que ya tienen al menos un titular activo (fecha_fin IS NULL)
        con_titular: set[str] = {
            r["registro_propiedad_id"]
            for r in await conn.fetch(
                "SELECT DISTINCT registro_propiedad_id FROM sipi.registros_propiedad_titulares WHERE fecha_fin IS NULL"
            )
        }

        # ── Insertar / actualizar ──────────────────────────────────────────────
        insertados  = 0
        actualizados = 0
        omitidos    = 0
        sin_mun     = 0
        titulares_creados = 0

        for row in filas:
            nombre = row["nombre"]

            # Si ya existe, actualizar dirección solo si estaba vacía
            if nombre in existentes:
                existing = existentes[nombre]
                nombre_via   = row.get("nombre_via", "").strip() or None
                codigo_postal = row.get("codigo_postal", "").strip() or None
                if codigo_postal and not existing["codigo_postal"]:
                    tipo_via_id = via_map.get(slugify(row["tipo_via_nombre"])) \
                                  if row.get("tipo_via_nombre") else None
                    if not dry_run:
                        await conn.execute("""
                            UPDATE sipi.registros_propiedad
                            SET tipo_via_id = $1, nombre_via = $2,
                                numero = $3, piso = $4, codigo_postal = $5
                            WHERE id = $6
                        """,
                            tipo_via_id,
                            nombre_via,
                            (row.get("numero") or "")[:10] or None,
                            (row.get("piso") or "")[:10] or None,
                            codigo_postal,
                            existing["id"],
                        )
                    actualizados += 1
                else:
                    omitidos += 1
                # Crear titular si no tiene ninguno activo
                reg_id = existing["id"]
                if reg_id not in con_titular and row.get("nombre_registrador"):
                    nom, ape = _split_nombre(row["nombre_registrador"])
                    if not dry_run:
                        await conn.execute("""
                            INSERT INTO sipi.registros_propiedad_titulares
                                (id, created_at, registro_propiedad_id, nombre, apellidos, fecha_inicio)
                            VALUES ($1, $2, $3, $4, $5, $6)
                        """, str(uuid.uuid4()), datetime.utcnow(), ETL_USER_ID, reg_id, nom, ape, datetime.utcnow())
                    con_titular.add(reg_id)
                    titulares_creados += 1
                continue

            cod_prov = row["codigo_ine_prov"]
            provincia_id = prov_map.get(cod_prov)
            if not provincia_id:
                print(f"  WARN sin provincia: {cod_prov} ({nombre})", file=sys.stderr)
                omitidos += 1
                continue

            # Municipio por slug + provincia (con alias para bilingüismo/truncados)
            mun_slug = SLUG_ALIAS.get(row["municipio_slug"], row["municipio_slug"])
            mun_data = (
                mun_map.get((mun_slug, provincia_id))
                or mun_map_sin_art.get((slug_sin_articulos(mun_slug), provincia_id))
            )
            if not mun_data:
                # Fallback: solo por slug (municipios que aparecen en una sola provincia)
                candidatos = [v for k, v in mun_map.items() if k[0] == mun_slug]
                if not candidatos:
                    sa = slug_sin_articulos(mun_slug)
                    candidatos = [v for k, v in mun_map_sin_art.items() if k[0] == sa]
                mun_data = candidatos[0] if len(candidatos) == 1 else None
                if not mun_data:
                    sin_mun += 1
                    print(f"  WARN sin municipio: '{mun_slug}' prov={cod_prov}", file=sys.stderr)

            municipio_id          = mun_data[0] if mun_data else None
            comunidad_autonoma_id = mun_data[1] if mun_data else None

            tipo_via_id = via_map.get(slugify(row["tipo_via_nombre"])) \
                          if row.get("tipo_via_nombre") else None

            reg_id = str(uuid.uuid4())
            if not dry_run:
                await conn.execute("""
                    INSERT INTO sipi.registros_propiedad (
                        id, created_at, created_by_id,
                        nombre, apellidos,
                        telefono, email_personal, email_corporativo,
                        tipo_via_id, nombre_via, numero, piso, codigo_postal,
                        provincia_id, municipio_id, comunidad_autonoma_id,
                        notas
                    ) VALUES (
                        $1,  $2,  $3,
                        $4,  $5,
                        $6,  $7,  $8,
                        $9,  $10,  $11,  $12,  $13,
                        $14, $15, $16,
                        $17
                    )
                """,
                    reg_id, datetime.utcnow(), ETL_USER_ID,
                    nombre, row["nombre_registrador"] or None,
                    row["telefono"] or None,
                    None,                           # email_personal no disponible
                    row["email"] or None,           # email_corporativo
                    tipo_via_id,
                    row["nombre_via"] or None,
                    (row["numero"] or "")[:10] or None,
                    (row["piso"] or "")[:10] or None,
                    row["codigo_postal"] or None,
                    provincia_id,
                    municipio_id,
                    comunidad_autonoma_id,
                    row["url_detalle"] or None,   # URL guardada en notas para trazabilidad
                )

                # Crear titular inicial (el registrador actual)
                if row.get("nombre_registrador"):
                    nom, ape = _split_nombre(row["nombre_registrador"])
                    await conn.execute("""
                        INSERT INTO sipi.registros_propiedad_titulares
                            (id, created_at, created_by_id, registro_propiedad_id, nombre, apellidos, fecha_inicio)
                        VALUES ($1, $2, $3, $4, $5, $6, $7)
                    """, str(uuid.uuid4()), datetime.utcnow(), ETL_USER_ID, reg_id, nom, ape, datetime.utcnow())
                    titulares_creados += 1

            insertados += 1

        modo = "[DRY-RUN] " if dry_run else ""
        print(f"  {modo}Insertados:   {insertados}")
        if actualizados:
            print(f"  {modo}Actualizados: {actualizados}  (dirección rellenada)")
        if omitidos:
            print(f"  Sin cambios:  {omitidos}")
        if sin_mun:
            print(f"  Sin municipio resuelto: {sin_mun}  (cargados sin municipio_id)")
        if titulares_creados:
            print(f"  {modo}Titulares creados: {titulares_creados}")

    finally:
        await conn.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="L4: carga Registros de la Propiedad")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD")
    args = parser.parse_args()

    print("L4 — Registros de la Propiedad…")
    asyncio.run(cargar(args.dry_run))
    print("✓ Completado")
