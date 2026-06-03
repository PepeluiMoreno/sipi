#!/usr/bin/env python3
"""
load/cargar_entidades_religiosas.py — carga entidades del RER desde JSONL extraído

Fuente: data/output/mjer/rer_entidades.jsonl
Campos JSONL: numero_inscripcion, Nombre, Confesión, Sección, Tipo de entidad,
              Fecha de inscripción, Domicilio social, Comunidad autónoma

Resolución de FKs:
  tipo_entidad_id      ← sipi.tipos_entidad_religiosa (seed on-the-fly)
  municipio_id         ← parse Domicilio social → nombre municipio → SQL JOIN municipios
  provincia_id         ← parse Domicilio social → nombre provincia → SQL JOIN provincias
  comunidad_autonoma_id← Comunidad autónoma → SQL JOIN comunidades_autonomas
  codigo_postal        ← parse Domicilio social (campo 2)
  nombre_via           ← parse Domicilio social (campo 1)

El domicilio social viene en formato: "CALLE, CP, MUNICIPIO, PROVINCIA" (whitespace mezclado)

Idempotente: INSERT … ON CONFLICT (numero_registro) DO UPDATE

Uso:
    python load/cargar_entidades_religiosas.py
    python load/cargar_entidades_religiosas.py --dry-run
"""

import argparse
import asyncio
import json
import logging
import re
import uuid
from datetime import datetime, timezone
from pathlib import Path

import asyncpg
import os

from utils.etl_audit import ETL_USER_ID, verificar_etluser

load_dotenv(Path(__file__).parent.parent / ".env")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

JSONL_DEFAULT = Path(__file__).parent.parent / "data" / "output" / "mjer" / "rer_entidades.jsonl"


def get_dsn() -> str:
    url = os.getenv("DATABASE_URL", "")
    if url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql://")
    elif url.startswith("postgresql+psycopg2://"):
        url = url.replace("postgresql+psycopg2://", "postgresql://")
    if not url:
        host = os.getenv("DB_HOST", "localhost")
        port = os.getenv("DB_PORT", "5433")
        user = os.getenv("DB_USER", "sipi")
        password = os.getenv("DB_PASSWORD", "sipi")
        database = os.getenv("DB_NAME", "sipi")
        url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
    return url


def parse_fecha(value: str | None) -> datetime | None:
    if not value:
        return None
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


def normalizar_seccion(valor: str | None) -> str | None:
    if not valor:
        return None
    v = valor.upper()
    if "ESPECIAL" in v:
        return "ESPECIAL"
    if "GENERAL" in v:
        return "GENERAL"
    return valor[:20]


def parsear_congregacion(valor: str | None) -> tuple[str | None, str | None]:
    """
    El campo RER "Congregación y provincia" mezcla nombre e indicación geográfica.
    Ejemplos:
      "CONGREGACION DE JESÚS MARÍA,EN ESPAÑA ( MADRID )"
      "ORDEN DE PREDICADORES,PROVINCIA DE ARAGÓN"
      "HERMANAS CLARISAS DE LA DIVINA PROVIDENCIA"
      "CONGREGACIÓN DE LOS SAGRADOS CORAZONES,PROVINCIA INTERNACIONAL"

    Devuelve (nombre_congregacion, ambito_geografico).
    ambito_geografico: INTERNACIONAL | ESTATAL | PROVINCIAL | LOCAL
    """
    if not valor:
        return None, None

    valor = valor.strip()
    # Separar nombre de indicación geográfica (por la primera coma)
    partes = valor.split(",", 1)
    nombre = partes[0].strip()[:500] or None
    resto = partes[1].strip().upper() if len(partes) > 1 else ""

    ambito = None
    if not resto:
        ambito = None
    elif "INTERNAC" in resto:
        ambito = "INTERNACIONAL"
    elif any(k in resto for k in ("EN ESPAÑA", "ESPAÑA", "NACIONAL", "ESTATAL")):
        ambito = "ESTATAL"
    elif any(k in resto for k in ("PROVINCIA", "REGION", "AUTONOMI")):
        ambito = "PROVINCIAL"
    elif any(k in resto for k in ("LOCAL", "DIOC", "ARCIDIOC")):
        ambito = "LOCAL"

    return nombre, ambito


def parsear_domicilio(domicilio: str | None) -> dict:
    """
    El domicilio social del RER tiene formato:
        CALLE, CP, MUNICIPIO, PROVINCIA
    con whitespace abundante entre campos. Devuelve dict con claves:
        nombre_via, codigo_postal, municipio_nombre, provincia_nombre
    """
    if not domicilio:
        return {}
    partes = [p.strip() for p in re.split(r'\s*,\s*|\t', domicilio) if p.strip()]
    result = {}
    # Buscar CP (5 dígitos exactos) — puede estar en cualquier posición
    cp_idx = None
    for i, p in enumerate(partes):
        if re.fullmatch(r'\d{5}', p):
            cp_idx = i
            result["codigo_postal"] = p
            break
    if cp_idx is not None:
        if cp_idx > 0:
            result["nombre_via"] = partes[0]
        if cp_idx + 1 < len(partes):
            result["municipio_nombre"] = partes[cp_idx + 1].upper()
        if cp_idx + 2 < len(partes):
            result["provincia_nombre"] = partes[cp_idx + 2].upper()
    elif partes:
        result["nombre_via"] = partes[0]
    return result


async def seed_tipos(conn, tipos_vistos: set[str]) -> dict[str, str]:
    """Crea los tipos de entidad que no existan y devuelve {codigo: id}."""
    mapa = {}
    now = datetime.now()
    for nombre in sorted(tipos_vistos):
        codigo = re.sub(r"[^A-Z0-9_]", "_", nombre.upper())[:50]
        row = await conn.fetchrow(
            "SELECT id FROM sipi.tipos_entidad_religiosa WHERE codigo = $1", codigo
        )
        if row:
            mapa[nombre] = str(row["id"])
        else:
            new_id = str(uuid.uuid4())
            await conn.execute(
                """
                INSERT INTO sipi.tipos_entidad_religiosa
                  (id, codigo, nombre, activo, created_at, created_by_id)
                VALUES ($1, $2, $3, true, $4, $5)
                """,
                new_id, codigo, nombre[:150], now, ETL_USER_ID,
            )
            mapa[nombre] = new_id
            log.info(f"  Tipo creado: {nombre}")
    return mapa


async def cargar(jsonl_path: Path, dry_run: bool):
    # Leer JSONL
    entidades = []
    with open(jsonl_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entidades.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    log.info(f"{len(entidades)} entidades leídas de {jsonl_path.name}")

    tipos_vistos = {e["Tipo de entidad"] for e in entidades if e.get("Tipo de entidad")}

    dsn = get_dsn()
    conn = await asyncpg.connect(dsn)
    try:
        await verificar_etluser(conn)
        # Seed tipos
        tipo_mapa = await seed_tipos(conn, tipos_vistos)

        # Mapas geográficos para resolución de FKs
        mapa_municipios = {
            r["nombre"].upper(): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.municipios")
        }
        mapa_provincias = {
            r["nombre"].upper(): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.provincias")
        }
        mapa_ccaa = {
            r["nombre"].upper(): r["id"]
            for r in await conn.fetch("SELECT id, nombre FROM sipi.comunidades_autonomas")
        }
        # Alias comunes CCAA
        alias_ccaa = {
            "ANDALUCIA": "ANDALUCÍA",
            "ARAGON": "ARAGÓN",
            "ASTURIAS": "PRINCIPADO DE ASTURIAS",
            "BALEARES": "ILLES BALEARS",
            "ISLAS BALEARES": "ILLES BALEARS",
            "CANARIAS": "CANARIAS",
            "CANTABRIA": "CANTABRIA",
            "CASTILLA LA MANCHA": "CASTILLA-LA MANCHA",
            "CASTILLA Y LEON": "CASTILLA Y LEÓN",
            "CATALUÑA": "CATALUÑA",
            "CATALUNYA": "CATALUÑA",
            "CEUTA": "CIUDAD AUTÓNOMA DE CEUTA",
            "EXTREMADURA": "EXTREMADURA",
            "GALICIA": "GALICIA",
            "LA RIOJA": "LA RIOJA",
            "MADRID": "COMUNIDAD DE MADRID",
            "MELILLA": "CIUDAD AUTÓNOMA DE MELILLA",
            "MURCIA": "REGIÓN DE MURCIA",
            "NAVARRA": "COMUNIDAD FORAL DE NAVARRA",
            "PAIS VASCO": "PAÍS VASCO",
            "EUSKADI": "PAÍS VASCO",
            "VALENCIA": "COMUNITAT VALENCIANA",
            "COMUNIDAD VALENCIANA": "COMUNITAT VALENCIANA",
        }

        now = datetime.now()
        insertados = actualizados = errores = 0
        sin_municipio = 0

        for e in entidades:
            numero = e.get("numero_inscripcion") or e.get("Número de inscripción", "")
            numero = str(numero).strip()
            if not numero:
                continue

            numero_antiguo = (e.get("Número de inscripción antiguo") or "").strip() or None
            seccion_rer = (e.get("Sección") or "").strip()[:50] or None

            nombre = (e.get("Nombre") or "").strip()[:255] or numero
            confesion = (e.get("Confesión") or "").strip()[:100] or None
            seccion = normalizar_seccion(e.get("Sección"))
            tipo_nombre = e.get("Tipo de entidad")
            tipo_id = tipo_mapa.get(tipo_nombre) if tipo_nombre else None
            fecha_inscripcion = parse_fecha(e.get("Fecha de inscripción"))
            congregacion, ambito_geografico = parsear_congregacion(e.get("Congregación y provincia"))

            # Contacto
            sitio_web         = (e.get("Página web") or "").strip()[:500] or None
            email_corporativo = (e.get("Correo electrónico") or "").strip()[:255] or None

            # Campos RER adicionales
            fecha_aprobacion  = parse_fecha(e.get("Fecha de aprobación de estatutos"))
            federaciones      = (e.get("Federaciones") or "").strip() or None
            entidades_federadas = (e.get("Entidades federadas") or "").strip() or None
            lugares_culto     = (e.get("Lugares de culto") or "").strip() or None

            # Resolver geografía desde Domicilio social
            domicilio = parsear_domicilio(e.get("Domicilio social"))
            codigo_postal = domicilio.get("codigo_postal")
            nombre_via = (domicilio.get("nombre_via") or "")[:255] or None

            mun_nombre = domicilio.get("municipio_nombre", "")
            prov_nombre = domicilio.get("provincia_nombre", "")
            municipio_id = mapa_municipios.get(mun_nombre) if mun_nombre else None
            provincia_id = mapa_provincias.get(prov_nombre) if prov_nombre else None

            # Comunidad autónoma
            ccaa_raw = (e.get("Comunidad autónoma") or "").strip().upper()
            ccaa_nombre = alias_ccaa.get(ccaa_raw, ccaa_raw)
            ccaa_id = mapa_ccaa.get(ccaa_nombre)

            if not municipio_id and mun_nombre:
                sin_municipio += 1

            if dry_run:
                insertados += 1
                continue

            # Representantes legales → titulares
            representantes_raw = e.get("Representantes legales") or ""
            representantes = [
                r.strip() for r in re.split(r'\n|\r', representantes_raw)
                if r.strip() and len(r.strip()) > 3
            ]

            try:
                row = await conn.fetchrow(
                    """
                    INSERT INTO sipi.entidades_religiosas
                      (id, numero_registro, numero_registro_antiguo, seccion_rer,
                       nombre, confesion, seccion,
                       tipo_entidad_id, fecha_inscripcion_rer, activa, es_territorial,
                       nombre_via, codigo_postal,
                       municipio_id, provincia_id, comunidad_autonoma_id,
                       congregacion, ambito_geografico,
                       sitio_web, email_corporativo,
                       fecha_aprobacion_estatutos, federaciones,
                       entidades_federadas, lugares_culto,
                       created_at, created_by_id)
                    VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,true,false,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21,$22,$23,$24)
                    ON CONFLICT (numero_registro) DO UPDATE SET
                      numero_registro_antiguo    = EXCLUDED.numero_registro_antiguo,
                      seccion_rer                = EXCLUDED.seccion_rer,
                      nombre                     = EXCLUDED.nombre,
                      confesion                  = EXCLUDED.confesion,
                      seccion                    = EXCLUDED.seccion,
                      tipo_entidad_id            = EXCLUDED.tipo_entidad_id,
                      fecha_inscripcion_rer      = EXCLUDED.fecha_inscripcion_rer,
                      nombre_via                 = EXCLUDED.nombre_via,
                      codigo_postal              = EXCLUDED.codigo_postal,
                      municipio_id               = EXCLUDED.municipio_id,
                      provincia_id               = EXCLUDED.provincia_id,
                      comunidad_autonoma_id      = EXCLUDED.comunidad_autonoma_id,
                      congregacion               = EXCLUDED.congregacion,
                      ambito_geografico          = EXCLUDED.ambito_geografico,
                      sitio_web                  = EXCLUDED.sitio_web,
                      email_corporativo          = EXCLUDED.email_corporativo,
                      fecha_aprobacion_estatutos = EXCLUDED.fecha_aprobacion_estatutos,
                      federaciones               = EXCLUDED.federaciones,
                      entidades_federadas        = EXCLUDED.entidades_federadas,
                      lugares_culto              = EXCLUDED.lugares_culto,
                      updated_at                 = $23,
                      updated_by_id              = $24
                    RETURNING id, (xmax = 0) AS es_nuevo
                    """,
                    str(uuid.uuid4()), numero, numero_antiguo, seccion_rer,
                    nombre, confesion, seccion,
                    tipo_id, fecha_inscripcion,
                    nombre_via, codigo_postal,
                    municipio_id, provincia_id, ccaa_id,
                    congregacion, ambito_geografico,
                    sitio_web, email_corporativo,
                    fecha_aprobacion, federaciones,
                    entidades_federadas, lugares_culto,
                    now, ETL_USER_ID,
                )
                entidad_id = row["id"]
                if row["es_nuevo"]:
                    insertados += 1
                else:
                    actualizados += 1

                # Carga titulares (representantes legales): reemplaza los existentes
                if representantes:
                    await conn.execute(
                        "DELETE FROM sipi.entidades_religiosas_titulares WHERE entidad_religiosa_id = $1",
                        entidad_id,
                    )
                    for rep in representantes:
                        partes = rep.rsplit(" ", 1)
                        rep_nombre = partes[0] if len(partes) > 1 else rep
                        rep_apellidos = partes[1] if len(partes) > 1 else None
                        await conn.execute(
                            """
                            INSERT INTO sipi.entidades_religiosas_titulares
                              (id, entidad_religiosa_id, nombre, apellidos, cargo,
                               created_at, created_by_id)
                            VALUES ($1,$2,$3,$4,'Representante legal',$5,$6)
                            """,
                            str(uuid.uuid4()), entidad_id,
                            rep_nombre[:255], rep_apellidos[:200] if rep_apellidos else None,
                            now, ETL_USER_ID,
                        )

            except Exception as exc:
                log.warning(f"  Error {numero}: {exc}")
                errores += 1

        log.info(
            f"Completado: {insertados} insertados, {actualizados} actualizados, "
            f"{errores} errores, {sin_municipio} sin municipio resuelto"
        )
        if dry_run:
            log.info("[DRY-RUN] Ningún cambio aplicado")

    finally:
        await conn.close()


def main():
    parser = argparse.ArgumentParser(description="Carga entidades del RER en la BD")
    parser.add_argument("--jsonl", type=Path, default=JSONL_DEFAULT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.jsonl.exists():
        log.error(f"No existe {args.jsonl}")
        return

    asyncio.run(cargar(args.jsonl, args.dry_run))


if __name__ == "__main__":
    main()
