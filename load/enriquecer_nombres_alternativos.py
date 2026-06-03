#!/usr/bin/env python3
"""
load/enriquecer_nombres_alternativos.py — puebla sipi.toponimos con nombres
alternativos de dos fuentes:

1. Aliases CEE (hardcodeados aquí como semilla inicial):
   Los PROV_ALIASES y MUN_ALIASES que antes vivían en cargar_parroquias.py
   se migran a la BD como fuente='cee'.

2. Geonames ES.zip — campo `alternatenames`:
   - ADM3 (municipio) → nivel='municipio'
   - ADM2 (provincia) → nivel='provincia'
   Proporciona nombres en lenguas cooficiales (ca, eu, gl…) y variantes
   históricas.

Uso:
    python load/enriquecer_nombres_alternativos.py
    python load/enriquecer_nombres_alternativos.py --dry-run
    python load/enriquecer_nombres_alternativos.py --solo-cee
"""

import argparse
import asyncio
import csv
import io
import logging
import os
import unicodedata
import urllib.request
import uuid
import zipfile
from datetime import datetime
from pathlib import Path

import asyncpg

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

GEONAMES_URL = "https://download.geonames.org/export/dump/ES.zip"
TABLA = "sipi.toponimos"

# ── Aliases CEE → INE ─────────────────────────────────────────────────────────
# Clave: nombre CEE tal como aparece en los datos de la Conferencia Episcopal
# Valor: nombre canónico INE (se buscará en la BD para obtener el id)

PROV_ALIASES_CEE: dict[str, str] = {
    "Araba/Álava":      "Álava",
    "Araba/Alava":      "Álava",
    "Alicante":         "Alicante/Alacant",
    "Castellon":        "Castellón/Castelló",
    "Castellón":        "Castellón/Castelló",
    "Baleares":         "Balears, Illes",
    "Illes Balears":    "Balears, Illes",
    "A Coruña":         "Coruña, A",
    "La Rioja":         "Rioja, La",
    "Las Palmas":       "Palmas, Las",
    "Valencia":         "Valencia/València",
    "Campoo":           "Cantabria",
}

MUN_ALIASES_CEE: dict[str, str] = {
    "Maó-Mahón":              "Maó",
    "Mahón":                  "Maó",
    "Calpe":                  "Calp",
    "Alfaz del Pí":           "Alfàs del Pi, l'",
    "Alfaz del Pi":           "Alfàs del Pi, l'",
    "Ollo":                   "Valle de Ollo/Ollaran",
    "Goñi":                   "Val de Goñi/Goñerri",
    "Lumbreras":              "Lumbreras de Cameros",
    "Pinell":                 "Pinell de Solsonès",
    "Buja Lance":             "Bujalance",
    "Calonge":                "Calonge i Sant Antoni",
    "Brunyola":               "Brunyola i Sant Martí Sapresa",
    "Callosa de Ensarriá":    "Callosa d'en Sarrià",
    "Polop de la Marina":     "Polop",
    "Quiñonería, La":         "Quiñonería",
    "Iglesuela, La":          "Iglesuela del Tiétar, La",
    "Bisbal de Montsant, La": "Bisbal de Falset, La",
    "Fresnedoso de Béjar":    "Fresnedoso",
    "Torremenga de la Vera":  "Torremenga",
    "Lantejuela, La":         "Lantejuela",
    "San Juan de Alicante":   "Sant Joan d'Alacant",
    "Alcocer de Planes":      "Alcosser",
}


# ── Normalización ──────────────────────────────────────────────────────────────

def normalizar(texto: str | None) -> str:
    s = (texto or "").strip().lower()
    s = s.replace("\u2019", "'").replace("\u2018", "'").replace("\u02bc", "'")
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def get_dsn() -> str:
    url = os.environ.get("DATABASE_URL", "")
    return url.replace("postgresql+asyncpg://", "postgresql://")


# ── Crear tabla ───────────────────────────────────────────────────────────────

async def crear_tabla(conn):
    await conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLA} (
            id          VARCHAR(36)  PRIMARY KEY,
            nombre      VARCHAR(300) NOT NULL,
            idioma      VARCHAR(10),
            fuente      VARCHAR(50),
            nivel       VARCHAR(50)  NOT NULL,
            entidad_id  VARCHAR(36)  NOT NULL,
            created_at  TIMESTAMP,
            updated_at  TIMESTAMP,
            UNIQUE (nivel, entidad_id, nombre)
        )
    """)
    await conn.execute(
        f"CREATE INDEX IF NOT EXISTS ix_toponimo_nivel_entidad ON {TABLA}(nivel, entidad_id)"
    )
    await conn.execute(
        f"CREATE INDEX IF NOT EXISTS ix_toponimo_nombre ON {TABLA}(nombre)"
    )
    log.info("Tabla sipi.toponimos verificada/creada")


# ── Aliases CEE ───────────────────────────────────────────────────────────────

async def cargar_aliases_cee(conn, dry_run: bool):
    now = datetime.utcnow()
    sql = f"""
        INSERT INTO {TABLA} (id, nombre, idioma, fuente, nivel, entidad_id, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (nivel, entidad_id, nombre) DO NOTHING
    """

    # Mapa nombre_norm → provincia_id
    prov_rows = await conn.fetch("SELECT id, unaccent(lower(nombre)) AS n FROM sipi.provincias")
    mapa_prov = {r["n"]: r["id"] for r in prov_rows}

    # Mapa nombre_norm → municipio_id (solo nombres únicos para evitar ambigüedad)
    mun_rows = await conn.fetch("""
        SELECT id, unaccent(lower(nombre)) AS n,
               COUNT(*) OVER (PARTITION BY unaccent(lower(nombre))) AS cnt
        FROM sipi.municipios
    """)
    mapa_mun = {r["n"]: r["id"] for r in mun_rows if r["cnt"] == 1}

    ins_p = ins_m = 0
    batch = []

    for alias, nombre_ine in PROV_ALIASES_CEE.items():
        prov_id = mapa_prov.get(normalizar(nombre_ine))
        if not prov_id:
            log.warning(f"  Provincia no encontrada: {nombre_ine!r}")
            continue
        batch.append((str(uuid.uuid4()), alias, "es", "cee", "provincia", prov_id, now, now))
        ins_p += 1

    for alias, nombre_ine in MUN_ALIASES_CEE.items():
        mun_id = mapa_mun.get(normalizar(nombre_ine))
        if not mun_id:
            log.warning(f"  Municipio no encontrado/ambiguo: {nombre_ine!r}")
            continue
        batch.append((str(uuid.uuid4()), alias, "es", "cee", "municipio", mun_id, now, now))
        ins_m += 1

    log.info(f"  Aliases CEE: {ins_p} provincias, {ins_m} municipios")
    if not dry_run and batch:
        await conn.executemany(sql, batch)


# ── Geonames ──────────────────────────────────────────────────────────────────

GEONAMES_COLS = [
    "geonameid", "name", "asciiname", "alternatenames",
    "lat", "lon", "feature_class", "feature_code",
    "country", "cc2", "admin1", "admin2", "admin3", "admin4",
    "population", "elevation", "dem", "timezone", "modification",
]


def descargar_geonames() -> bytes:
    log.info(f"Descargando {GEONAMES_URL} …")
    req = urllib.request.Request(
        GEONAMES_URL,
        headers={"User-Agent": "SIPI-ETL/1.0 (investigacion patrimonial)"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = r.read()
    log.info(f"  {len(data)/1024/1024:.1f} MB")
    return data


async def cargar_geonames(conn, data: bytes, dry_run: bool):
    now = datetime.utcnow()
    sql = f"""
        INSERT INTO {TABLA} (id, nombre, idioma, fuente, nivel, entidad_id, created_at, updated_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        ON CONFLICT (nivel, entidad_id, nombre) DO NOTHING
    """

    mun_rows = await conn.fetch("SELECT id, codigo_ine FROM sipi.municipios")
    mapa_mun = {r["codigo_ine"]: r["id"] for r in mun_rows}

    # Geonames usa código ISO alfa ('V', 'TO', 'SE'…) sin equivalente directo en INE.
    # Construimos el mapa código-ISO-Geonames → provincia_id en dos pasos:
    # 1. Leemos los ADM2 de Geonames y guardamos admin2 → nombre_principal
    # 2. Hacemos match por nombre normalizado con nuestra tabla de provincias
    prov_rows = await conn.fetch(
        "SELECT id, unaccent(lower(nombre)) AS n FROM sipi.provincias"
    )
    mapa_prov_nombre: dict[str, str] = {r["n"]: r["id"] for r in prov_rows}

    # Primera pasada: construir admin2_code → provincia_id via nombre
    z_preview = zipfile.ZipFile(io.BytesIO(data))
    mapa_prov: dict[str, str] = {}
    with z_preview.open("ES.txt") as f:
        reader0 = csv.DictReader(
            io.TextIOWrapper(f, encoding="utf-8"),
            fieldnames=GEONAMES_COLS,
            delimiter="\t",
        )
        for row in reader0:
            if row["feature_class"] == "A" and row["feature_code"] == "ADM2":
                nombre_n = normalizar(row["name"].replace("Provincia de ", "")
                                     .replace("Província de ", "")
                                     .replace("Province of ", ""))
                prov_id = mapa_prov_nombre.get(nombre_n)
                if prov_id:
                    mapa_prov[row["admin2"]] = prov_id

    batch_mun: list[tuple] = []
    batch_prov: list[tuple] = []
    sin_ref = 0

    z = zipfile.ZipFile(io.BytesIO(data))
    with z.open("ES.txt") as f:
        reader = csv.DictReader(
            io.TextIOWrapper(f, encoding="utf-8"),
            fieldnames=GEONAMES_COLS,
            delimiter="\t",
        )
        for row in reader:
            fc   = row["feature_class"]
            code = row["feature_code"]
            alts = [a.strip() for a in (row["alternatenames"] or "").split(",") if a.strip()]
            if not alts:
                continue

            if fc == "A" and code == "ADM3":
                admin3 = (row["admin3"] or "").strip()
                mun_id = mapa_mun.get(admin3)
                if not mun_id:
                    sin_ref += 1
                    continue
                for alt in alts:
                    if alt == row["name"]:
                        continue
                    batch_mun.append((str(uuid.uuid4()), alt, None, "geonames", "municipio", mun_id, now, now))

            elif fc == "A" and code == "ADM2":
                admin2 = (row["admin2"] or "").strip().zfill(2)
                prov_id = mapa_prov.get(admin2)
                if not prov_id:
                    sin_ref += 1
                    continue
                for alt in alts:
                    if alt == row["name"]:
                        continue
                    batch_prov.append((str(uuid.uuid4()), alt, None, "geonames", "provincia", prov_id, now, now))

    log.info(f"  Geonames: {len(batch_mun)} alt-municipios, {len(batch_prov)} alt-provincias | sin referencia: {sin_ref}")

    if not dry_run:
        BATCH = 1000
        async with conn.transaction():
            for i in range(0, len(batch_mun), BATCH):
                await conn.executemany(sql, batch_mun[i:i+BATCH])
            for i in range(0, len(batch_prov), BATCH):
                await conn.executemany(sql, batch_prov[i:i+BATCH])


# ── Main ──────────────────────────────────────────────────────────────────────

async def main(dry_run: bool, solo_cee: bool):
    if dry_run:
        log.info("[DRY-RUN: no se escribirá en BD]")
    conn = await asyncpg.connect(get_dsn())
    try:
        await crear_tabla(conn)
        log.info("── Aliases CEE ──────────────────────────────────")
        await cargar_aliases_cee(conn, dry_run)
        if not solo_cee:
            log.info("── Geonames alternatenames ──────────────────────")
            data = descargar_geonames()
            await cargar_geonames(conn, data, dry_run)
        log.info("✓ Enriquecimiento completado")
    finally:
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--solo-cee", action="store_true",
                        help="Solo carga aliases CEE, sin descargar Geonames")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run, args.solo_cee))
