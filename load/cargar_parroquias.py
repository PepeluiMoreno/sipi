#!/usr/bin/env python3
"""
load/cargar_parroquias.py — carga parroquias desde el JSON extraído por extract_parroquias.py

Fuente: data/output/cee/parroquias.json
  Campos: diocesis_slug, diocesis_nombre, nombre, titular, codigo_postal,
          nombre_via, telefono, municipio_nombre, provincia_nombre

Resolución de FKs:
  diocesis_id  ← sipi.diocesis WHERE cee_slug = diocesis_slug
  municipio_id ← sipi.municipios m
                 JOIN sipi.provincias p ON m.provincia_id = p.id
                 WHERE unaccent(lower(m.nombre)) = unaccent(lower(municipio_nombre))
                   AND unaccent(lower(p.nombre)) = unaccent(lower(provincia_nombre))

Idempotente: INSERT … ON CONFLICT (diocesis_id, nombre) DO UPDATE

Uso:
    python load/cargar_parroquias.py
    python load/cargar_parroquias.py --json data/output/cee/parroquias.json
    python load/cargar_parroquias.py --dry-run
"""

import argparse
import asyncio
import csv
import json
import logging
import re
import sys
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
import os

from utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

JSON_DEFAULT   = Path(__file__).parent.parent / "data" / "output" / "cee" / "parroquias.json"
INCIDENCIAS_OUT = Path(__file__).parent.parent / "data" / "output" / "incidencias_municipios.csv"

TABLA = "sipi.parroquias"


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


import unicodedata as _ud

def normalizar(texto: str | None) -> str:
    """Minúsculas sin acentos ni espacios extra para comparaciones."""
    s = (texto or "").strip().lower()
    # Normalizar variantes de apóstrofe a '
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")
    return "".join(c for c in _ud.normalize("NFD", s) if _ud.category(c) != "Mn")



async def construir_mapa_diocesis(conn) -> dict[str, tuple[str, str, str]]:
    """cee_slug → (id, diocesis_nombre, provincia_eclesiastica_nombre)"""
    filas = await conn.fetch(
        """
        SELECT d.id, d.cee_slug, d.nombre AS d_nombre,
               COALESCE(pe.nombre, '') AS pe_nombre
        FROM sipi.diocesis d
        LEFT JOIN sipi.provincias_eclesiasticas pe ON pe.id = d.provincia_eclesiastica_id
        WHERE d.cee_slug IS NOT NULL
        """
    )
    return {r["cee_slug"]: (r["id"], r["d_nombre"], r["pe_nombre"]) for r in filas}


async def construir_mapa_municipios_cpro(conn) -> dict[tuple[str, str], str]:
    """(unaccent_lower(nombre_municipio), cpro) → municipio_id  — para casos sin provincia_nombre"""
    filas = await conn.fetch(
        """
        SELECT id, unaccent(lower(nombre)) AS mun, left(codigo_ine, 2) AS cpro
        FROM sipi.municipios
        """
    )
    mapa: dict[tuple[str, str], str] = {}
    for r in filas:
        mun, cpro, mid = r["mun"], r["cpro"], r["id"]
        if (mun, cpro) not in mapa:
            mapa[(mun, cpro)] = mid
        # variantes bilingues: "alboraia/alboraya" → "alboraia" y "alboraya"
        if "/" in mun:
            for parte in mun.split("/"):
                parte = parte.strip()
                if parte and (parte, cpro) not in mapa:
                    mapa[(parte, cpro)] = mid
        # sin artículo: "campello, el" → "campello"
        sin_art = _ART_SUFIJO.sub("", mun).strip()
        if sin_art != mun and (sin_art, cpro) not in mapa:
            mapa[(sin_art, cpro)] = mid
    return mapa


async def construir_mapa_entidades(conn) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str], str]]:
    """Devuelve dos mapas indexados por (unaccent_lower(nombre), cpro):
      - mapa_mun: → municipio_id
      - mapa_elm: → entidad_local_menor_id
    """
    filas = await conn.fetch(
        """
        SELECT e.id, unaccent(lower(e.nombre)) AS ent,
               left(e.codigo_ine_municipio, 2) AS cpro,
               e.municipio_id
        FROM sipi.entidades_locales_menores e
        WHERE e.municipio_id IS NOT NULL
        """
    )
    mapa_mun: dict[tuple[str, str], str] = {}
    mapa_elm: dict[tuple[str, str], str] = {}
    for r in filas:
        key = (r["ent"], r["cpro"])
        if key not in mapa_mun:
            mapa_mun[key] = r["municipio_id"]
            mapa_elm[key] = r["id"]
    return mapa_mun, mapa_elm


async def construir_mapa_cp(conn) -> dict[str, str]:
    """codigo_postal → municipio_id  (solo CPs que mapean a exactamente 1 municipio)"""
    filas = await conn.fetch(
        """
        SELECT codigo_postal, municipio_id, COUNT(*) OVER (PARTITION BY codigo_postal) AS n
        FROM (
            SELECT DISTINCT codigo_postal, municipio_id
            FROM sipi.parroquias
            WHERE municipio_id IS NOT NULL AND codigo_postal IS NOT NULL
        ) sub
        """
    )
    return {r["codigo_postal"]: r["municipio_id"] for r in filas if r["n"] == 1}


_ART_SUFIJO = re.compile(r",\s*(el|la|els|les|los|las|l'|lo|a|o|os|as)\s*$", re.IGNORECASE)


async def construir_mapa_municipios(conn) -> dict[tuple[str, str], str]:
    """(normalizado(nombre_o_topónimo), normalizado(provincia_o_topónimo)) → municipio_id

    Indexa:
      - nombre canónico INE + todas las variantes de sipi.toponimos (nivel='municipio')
      - cada parte de nombres con '/' y nombres sin artículo final
      - combinaciones con nombre canónico de provincia y topónimos de provincia
    """
    # Nombres canónicos de municipios con su provincia
    filas = await conn.fetch(
        """
        SELECT m.id,
               unaccent(lower(m.nombre)) AS mun,
               unaccent(lower(p.nombre)) AS prov
        FROM sipi.municipios m
        JOIN sipi.provincias p ON m.provincia_id = p.id
        """
    )
    # Topónimos de municipios: nombre_alternativo → municipio_id
    top_mun = await conn.fetch(
        "SELECT unaccent(lower(nombre)) AS nombre, entidad_id FROM sipi.toponimos WHERE nivel = 'municipio'"
    )
    # Topónimos de provincias: nombre_alternativo → provincia_id
    top_prov = await conn.fetch(
        "SELECT unaccent(lower(nombre)) AS nombre, entidad_id FROM sipi.toponimos WHERE nivel = 'provincia'"
    )
    # Mapa municipio_id → lista de nombres normalizados (canónico + topónimos)
    mun_nombres: dict[str, list[str]] = {}
    for r in filas:
        mun_nombres.setdefault(r["id"], []).append(r["mun"])
    for r in top_mun:
        mun_nombres.setdefault(r["entidad_id"], []).append(r["nombre"])

    # Mapa municipio_id → lista de nombres de provincia normalizados
    mun_prov: dict[str, str] = {r["id"]: r["prov"] for r in filas}  # canónico
    prov_topónimos: dict[str, list[str]] = {}  # provincia_id → alt nombres prov
    for r in top_prov:
        prov_topónimos.setdefault(r["entidad_id"], []).append(r["nombre"])
    # provincia_id → all prov names
    prov_id_of_mun: dict[str, str] = {}
    for r in filas:
        # necesitamos el provincia_id de cada municipio
        pass

    # Re-consultamos con provincia_id para cruzar topónimos de provincia
    filas2 = await conn.fetch(
        """
        SELECT m.id AS mun_id, m.provincia_id,
               unaccent(lower(p.nombre)) AS prov_canon
        FROM sipi.municipios m JOIN sipi.provincias p ON m.provincia_id = p.id
        """
    )
    mun_prov_id: dict[str, str] = {r["mun_id"]: r["provincia_id"] for r in filas2}
    prov_canon:  dict[str, str] = {r["mun_id"]: r["prov_canon"]   for r in filas2}

    mapa: dict[tuple[str, str], str] = {}

    def _agregar(nombres_mun: list[str], nombres_prov: list[str], mid: str):
        for mun in nombres_mun:
            variantes_mun = {mun}
            if "/" in mun:
                variantes_mun.update(p.strip() for p in mun.split("/"))
            sin_art = _ART_SUFIJO.sub("", mun).strip()
            if sin_art != mun:
                variantes_mun.add(sin_art)
            for vm in variantes_mun:
                for prov in nombres_prov:
                    if (vm, prov) not in mapa:
                        mapa[(vm, prov)] = mid

    for r in filas2:
        mid = r["mun_id"]
        prov_id = r["provincia_id"]
        nombres_mun  = mun_nombres.get(mid, [])
        nombres_prov = [r["prov_canon"]] + prov_topónimos.get(prov_id, [])
        _agregar(nombres_mun, nombres_prov, mid)

    return mapa


async def construir_mapa_municipios_unico(conn) -> dict[str, str]:
    """nombre_o_topónimo_normalizado → municipio_id  (solo nombres únicos en España).

    Incluye los topónimos de sipi.toponimos para cubrir aliases CEE y variantes Geonames.
    """
    # Nombre canónico: count de repeticiones por nombre
    filas = await conn.fetch(
        """
        SELECT unaccent(lower(nombre)) AS mun, id,
               COUNT(*) OVER (PARTITION BY unaccent(lower(nombre))) AS n
        FROM sipi.municipios
        """
    )
    # Topónimos: cuenta cuántos municipios distintos tienen ese topónimo
    top = await conn.fetch(
        """
        SELECT mun, entidad_id, COUNT(*) OVER (PARTITION BY mun) AS n
        FROM (
            SELECT DISTINCT unaccent(lower(nombre)) AS mun, entidad_id
            FROM sipi.toponimos WHERE nivel = 'municipio'
        ) sub
        """
    )
    mapa: dict[str, str] = {}
    for r in filas:
        if r["n"] == 1:
            mun = r["mun"]
            mapa[mun] = r["id"]
            if "/" in mun:
                for parte in mun.split("/"):
                    parte = parte.strip()
                    if parte and parte not in mapa:
                        mapa[parte] = r["id"]
    for r in top:
        if r["n"] == 1 and r["mun"] not in mapa:
            mapa[r["mun"]] = r["entidad_id"]
    return mapa


async def cargar(conn, parroquias: list[dict], dry_run: bool) -> dict:
    mapa_diocesis        = await construir_mapa_diocesis(conn)
    mapa_municipios      = await construir_mapa_municipios(conn)
    mapa_municipios_cpro = await construir_mapa_municipios_cpro(conn)
    mapa_entidades_mun, mapa_entidades_elm = await construir_mapa_entidades(conn)
    mapa_municipios_unico = await construir_mapa_municipios_unico(conn)
    mapa_cp              = await construir_mapa_cp(conn)
    now = datetime.utcnow()

    sin_diocesis    = 0
    sin_municipio   = 0
    por_alias       = 0
    por_cp          = 0
    por_entidad     = 0
    insertadas      = 0
    actualizadas    = 0
    incidencias     = []  # filas que no pudieron resolverse

    records = []
    for p in parroquias:
        diocesis_slug   = p.get("diocesis_slug", "")
        diocesis_entry  = mapa_diocesis.get(diocesis_slug)
        if not diocesis_entry:
            sin_diocesis += 1
            log.debug(f"Sin diocesis_id para slug '{diocesis_slug}'")
            continue
        diocesis_id, diocesis_nombre, prov_eclesiastica_nombre = diocesis_entry

        municipio_id         = None
        entidad_local_menor_id = None
        metodo = "-"

        # Intento 1: nombre + provincia — el mapa ya incluye topónimos de ambos lados
        mun_norm  = normalizar(p.get("municipio_nombre"))
        prov_norm = normalizar(p.get("provincia_nombre"))
        if mun_norm:
            municipio_id = mapa_municipios.get((mun_norm, prov_norm))
            if not municipio_id and "/" in mun_norm:
                # Nombres bilingues CEE (Salvatierra/Agurain): probar cada parte
                for parte in mun_norm.split("/"):
                    municipio_id = mapa_municipios.get((parte.strip(), prov_norm))
                    if municipio_id:
                        break
            if municipio_id:
                metodo = "nombre"
                prov_orig = normalizar(p.get("provincia_nombre"))
                if prov_orig != prov_norm:
                    por_alias += 1

        # Intento 2: fallback por entidad local menor (nombre_municipio + código provincia del CP)
        if not municipio_id and mun_norm and p.get("codigo_postal"):
            cpro = (p["codigo_postal"] or "")[:2]
            municipio_id = mapa_entidades_mun.get((mun_norm, cpro))
            if municipio_id:
                entidad_local_menor_id = mapa_entidades_elm.get((mun_norm, cpro))
                metodo = "entidad"
                por_entidad += 1

        # Intento 3: cuando municipio_nombre está vacío, usar nombre de parroquia
        # (para diócesis como Valencia donde el nombre de la parroquia ES el municipio/pedanía)
        if not municipio_id and not mun_norm and p.get("codigo_postal"):
            nombre_norm = normalizar(p.get("nombre"))
            cpro = (p["codigo_postal"] or "")[:2]
            if nombre_norm and cpro:
                # Probar nombre completo y cada parte si es bilingüe (slash)
                candidatos = [nombre_norm] + ([pt.strip() for pt in nombre_norm.split("/") if pt.strip()] if "/" in nombre_norm else [])
                for cand in candidatos:
                    if not municipio_id:
                        municipio_id = mapa_municipios_cpro.get((cand, cpro))
                    if not municipio_id:
                        municipio_id = mapa_entidades_mun.get((cand, cpro))
                        if municipio_id:
                            entidad_local_menor_id = mapa_entidades_elm.get((cand, cpro))
                    if municipio_id:
                        break
                if municipio_id:
                    metodo = "nombre_como_mun"
                    por_entidad += 1

        # Intento 4: fallback por código postal (CP → 1 municipio único)
        if not municipio_id and p.get("codigo_postal"):
            municipio_id = mapa_cp.get(p["codigo_postal"])
            if municipio_id:
                metodo = "cp"
                por_cp += 1

        # Intento 5: nombre único en España (ignora provincia incorrecta del CEE)
        if not municipio_id and mun_norm:
            municipio_id = mapa_municipios_unico.get(mun_norm)
            if not municipio_id and "/" in mun_norm:
                for parte in mun_norm.split("/"):
                    municipio_id = mapa_municipios_unico.get(parte.strip())
                    if municipio_id:
                        break
            if municipio_id:
                metodo = "nombre_unico"
                por_alias += 1

        # Intento 6: CEE pone el municipio en el campo provincia (pedanías gallegas y similares)
        # Si prov_norm es un nombre de municipio único en España, usarlo como municipio
        if not municipio_id and prov_norm:
            municipio_id = mapa_municipios_unico.get(prov_norm)
            if municipio_id:
                metodo = "prov_como_mun"
                por_alias += 1

        if not municipio_id:
            sin_municipio += 1
            incidencias.append({
                "nombre":        p.get("nombre", ""),
                "titular":       p.get("titular", ""),
                "diocesis":      p.get("diocesis_nombre", ""),
                "municipio_cee": p.get("municipio_nombre", ""),
                "provincia_cee": p.get("provincia_nombre", ""),
                "cp":            p.get("codigo_postal", ""),
                "motivo":        "sin_municipio_nombre" if not p.get("municipio_nombre") else "sin_match_ine",
            })

        titular      = (p.get("titular") or "").strip()
        mun_nombre   = (p.get("municipio_nombre") or "").strip()
        prov_nombre  = (p.get("provincia_nombre") or "").strip()

        # Nombre: "Parroquia de {titular}" — el resto de datos accesibles via relaciones
        if titular:
            nombre_compuesto = f"Parroquia de {titular}"
        else:
            nombre_compuesto = (p.get("nombre") or "").strip()

        records.append({
            "id":                      str(uuid.uuid4()),
            "nombre":                  nombre_compuesto,
            "titular":                 titular or None,
            "diocesis_id":             diocesis_id,
            "municipio_id":            municipio_id,
            "entidad_local_menor_id":  entidad_local_menor_id,
            "nombre_via":              (p.get("nombre_via") or "").strip() or None,
            "codigo_postal":           p.get("codigo_postal"),
            "telefono":                p.get("telefono"),
            "cee_url_diocesis":        p.get("cee_url_diocesis"),
            "created_at":              now,
            "updated_at":              now,
            "created_by_id":           ETL_USER_ID,
        })

    if not records:
        log.warning("No hay registros válidos para cargar")
        return {"insertadas": 0, "actualizadas": 0, "sin_diocesis": sin_diocesis,
                "sin_municipio": sin_municipio, "por_alias": 0, "por_entidad": 0, "por_cp": 0, "incidencias": []}

    log.info(f"  Registros a procesar: {len(records)} "
             f"(sin diócesis: {sin_diocesis} | sin municipio: {sin_municipio} "
             f"| por alias: {por_alias} | por entidad: {por_entidad} | por CP: {por_cp})")

    if dry_run:
        return {"insertadas": len(records), "actualizadas": 0,
                "sin_diocesis": sin_diocesis, "sin_municipio": sin_municipio,
                "por_alias": por_alias, "por_entidad": por_entidad, "por_cp": por_cp, "incidencias": incidencias}

    # Construir índice de existentes: (diocesis_id, nombre) → id
    # Incluye soft-deleted para poder reactivarlos en un rerun
    existentes: dict[tuple[str, str], str] = {
        (r["diocesis_id"], r["nombre"]): r["id"]
        for r in await conn.fetch(f"SELECT id, diocesis_id, nombre FROM {TABLA}")
    }

    sql_insert = f"""
        INSERT INTO {TABLA}
            (id, nombre, titular, diocesis_id, municipio_id, entidad_local_menor_id,
             nombre_via, codigo_postal, telefono, cee_url_diocesis,
             created_at, updated_at, created_by_id)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
    """
    # deleted_at = NULL para reactivar si estaba borrado lógicamente
    sql_update = f"""
        UPDATE {TABLA} SET
            titular                = COALESCE($1, titular),
            municipio_id           = COALESCE($2, municipio_id),
            entidad_local_menor_id = COALESCE($3, entidad_local_menor_id),
            nombre_via             = COALESCE($4, nombre_via),
            codigo_postal          = COALESCE($5, codigo_postal),
            telefono               = COALESCE($6, telefono),
            cee_url_diocesis       = COALESCE($7, cee_url_diocesis),
            updated_at             = $8,
            updated_by_id          = $9,
            deleted_at             = NULL
        WHERE id = $10
    """

    async with conn.transaction():
        for r in records:
            key = (r["diocesis_id"], r["nombre"])
            if key in existentes:
                await conn.execute(
                    sql_update,
                    r["titular"], r["municipio_id"], r["entidad_local_menor_id"],
                    r["nombre_via"], r["codigo_postal"], r["telefono"], r["cee_url_diocesis"],
                    r["updated_at"], ETL_USER_ID, existentes[key],
                )
                actualizadas += 1
            else:
                await conn.execute(
                    sql_insert,
                    r["id"], r["nombre"], r["titular"], r["diocesis_id"],
                    r["municipio_id"], r["entidad_local_menor_id"],
                    r["nombre_via"], r["codigo_postal"], r["telefono"], r["cee_url_diocesis"],
                    r["created_at"], r["updated_at"], r["created_by_id"],
                )
                insertadas += 1

    return {"insertadas": insertadas, "actualizadas": actualizadas,
            "sin_diocesis": sin_diocesis, "sin_municipio": sin_municipio,
            "por_alias": por_alias, "por_entidad": por_entidad, "por_cp": por_cp, "incidencias": incidencias}


async def enriquecer_cp_entidades(conn):
    """Propaga el codigo_postal de parroquias a sus entidades locales menores.

    Para cada ELM sin CP, toma el CP más frecuente de las parroquias que lo referencian.
    Luego usa esos CPs para resolver parroquias pendientes (sin ELM) por CP.
    """
    # 1. Actualizar ELMs con CP deducido de sus parroquias
    res = await conn.execute("""
        UPDATE sipi.entidades_locales_menores elm
        SET codigo_postal = sub.cp
        FROM (
            SELECT DISTINCT ON (entidad_local_menor_id)
                entidad_local_menor_id,
                codigo_postal AS cp
            FROM sipi.parroquias
            WHERE entidad_local_menor_id IS NOT NULL
              AND codigo_postal IS NOT NULL
              AND deleted_at IS NULL
            ORDER BY entidad_local_menor_id, codigo_postal
        ) sub
        WHERE elm.id = sub.entidad_local_menor_id
          AND elm.codigo_postal IS NULL
    """)
    n_elm = int((res or "UPDATE 0").split()[-1])
    log.info(f"  ELMs con CP deducido de parroquias: {n_elm}")

    # 2. Usando los CPs recién asignados, resolver parroquias sin ELM
    res2 = await conn.execute("""
        UPDATE sipi.parroquias p
        SET entidad_local_menor_id = elm.id
        FROM sipi.entidades_locales_menores elm
        WHERE p.entidad_local_menor_id IS NULL
          AND p.deleted_at IS NULL
          AND p.codigo_postal IS NOT NULL
          AND elm.codigo_postal = p.codigo_postal
          AND elm.municipio_id = p.municipio_id
    """)
    n_par = int((res2 or "UPDATE 0").split()[-1])
    log.info(f"  Parroquias con ELM deducido por CP: {n_par}")
    return n_elm, n_par


async def main(json_path: Path, dry_run: bool):
    if not json_path.exists():
        log.error(f"No existe {json_path}. Ejecuta primero extract_parroquias.py")
        sys.exit(1)

    parroquias = json.loads(json_path.read_text(encoding="utf-8"))
    log.info(f"JSON cargado: {len(parroquias)} parroquias desde {json_path}")

    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")

    conn = await asyncpg.connect(get_dsn())
    try:
        await verificar_etluser(conn)
        stats = await cargar(conn, parroquias, dry_run)
        log.info(
            f"Parroquias: {stats['insertadas']} insertadas, "
            f"{stats['actualizadas']} actualizadas | "
            f"sin diócesis: {stats['sin_diocesis']} | "
            f"sin municipio: {stats['sin_municipio']} | "
            f"por alias: {stats['por_alias']} | "
            f"por entidad: {stats['por_entidad']} | "
            f"por CP: {stats['por_cp']}"
        )
        # Exportar incidencias a CSV
        incidencias = stats["incidencias"]
        if incidencias:
            INCIDENCIAS_OUT.parent.mkdir(parents=True, exist_ok=True)
            with INCIDENCIAS_OUT.open("w", newline="", encoding="utf-8") as f:
                w = csv.DictWriter(f, fieldnames=["nombre", "titular", "diocesis",
                                                   "municipio_cee", "provincia_cee", "cp", "motivo"])
                w.writeheader()
                w.writerows(incidencias)
            log.warning(f"  {len(incidencias)} incidencias sin municipio → {INCIDENCIAS_OUT}")

        if not dry_run:
            await enriquecer_cp_entidades(conn)

        log.info("✓ Carga de parroquias completada")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Carga parroquias desde JSON CEE")
    parser.add_argument("--json", type=Path, default=JSON_DEFAULT,
                        help=f"Ruta al JSON (default: {JSON_DEFAULT})")
    parser.add_argument("--dry-run", action="store_true", help="Simula sin escribir en BD")
    args = parser.parse_args()
    asyncio.run(main(args.json, args.dry_run))
