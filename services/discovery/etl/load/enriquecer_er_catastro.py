#!/usr/bin/env python3
"""
load/enriquecer_er_catastro.py — Geocodifica entidades religiosas via API del Catastro.

Para cada entidad religiosa con dirección (nombre_via + codigo_postal) pero sin
coordenadas, consulta la API pública OVC del Catastro para obtener:
  - Referencia catastral (RC)
  - Código INE de municipio (permite resolver municipio_id cuando falló el parsing)
  - Uso catastral del inmueble (RELIGIOSO, CULTURAL, SANITARIO…)
  - Coordenadas (via Consulta_CPMRC con la RC obtenida)

API usada (HTTP GET, sin autenticación):
  https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx
    Consulta_DNPLOC  — inmueble por localización (provincia, municipio, calle, número)
  https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx
    Consulta_CPMRC   — coordenadas por referencia catastral

Estrategia:
  1. Parsear nombre_via en tipo_via + nombre + número
  2. Llamar a Consulta_DNPLOC con provincia + municipio + calle + número
  3. Si hay resultado: guardar RC, cp INE, uso catastral
  4. Llamar a Consulta_CPMRC para obtener lat/lon (ETRS89 → WGS84)
  5. Si se resuelve municipio INE: intentar resolver municipio_id en SIPI

Nota: la API del Catastro NO devuelve el NIF del titular (datos protegidos).
      Para NIF ver enriquecer_er_nif.py.

Limitaciones:
  - Rate limit: ~5 req/s recomendado
  - Entidades sin número en la dirección tienen menor tasa de éxito
  - Religiosas en inmuebles compartidos pueden no coincidir exactamente

Uso:
    python load/enriquecer_er_catastro.py
    python load/enriquecer_er_catastro.py --dry-run
    python load/enriquecer_er_catastro.py --limite 100
    python load/enriquecer_er_catastro.py --solo-sin-municipio
"""

import argparse
import asyncio
import logging
import re
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import asyncpg
import requests
import os

load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

NS = {"c": "http://www.catastro.meh.es/"}

CALLEJERO_URL = (
    "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC"
    "/OVCCallejero.asmx/Consulta_DNPLOC"
)
COORDS_URL = (
    "https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC"
    "/OVCCoordenadas.asmx/Consulta_CPMRC"
)

# Siglas de tipo de vía más comunes (para separar del nombre)
TIPOS_VIA = {
    "CALLE": "CL", "CL": "CL", "C/": "CL",
    "AVENIDA": "AV", "AV": "AV", "AVDA": "AV",
    "PASEO": "PG", "PG": "PG",
    "PLAZA": "PZ", "PL": "PZ",
    "CAMINO": "CM", "CM": "CM",
    "CARRETERA": "CR", "CR": "CR",
    "RONDA": "RD", "RD": "RD",
    "URBANIZACION": "UR",
    "GLORIETA": "GL",
    "TRAVESIA": "TR",
    "BARRIO": "BO",
    "LUGAR": "LG",
    "PARAJE": "PJ",
}


def parsear_via(nombre_via: str) -> tuple[str, str, str]:
    """
    Intenta separar 'CALLE MAYOR 5' en ('CL', 'MAYOR', '5').
    Devuelve (sigla, nombre_calle, numero).
    """
    if not nombre_via:
        return ("CL", "", "")

    partes = nombre_via.strip().upper().split()
    if not partes:
        return ("CL", "", "")

    sigla = "CL"
    resto = partes

    # Detectar tipo de vía en el primer (o dos primeros) tokens
    if partes[0] in TIPOS_VIA:
        sigla = TIPOS_VIA[partes[0]]
        resto = partes[1:]
    elif len(partes) > 1 and f"{partes[0]} {partes[1]}" in TIPOS_VIA:
        sigla = TIPOS_VIA[f"{partes[0]} {partes[1]}"]
        resto = partes[2:]

    if not resto:
        return (sigla, "", "")

    # Separar número del final
    numero = ""
    if re.fullmatch(r"\d+[\w-]*", resto[-1]):
        numero = resto[-1]
        resto = resto[:-1]

    nombre_calle = " ".join(resto)
    return (sigla, nombre_calle, numero)


def consulta_dnploc(
    provincia: str, municipio: str, sigla: str, calle: str, numero: str,
    session: requests.Session, timeout: int = 10
) -> dict | None:
    """
    Llama a Consulta_DNPLOC y devuelve los datos del inmueble si se encuentra.
    Devuelve dict con: rc, cp_ine, nm_municipio, uso o None si no hay resultado.
    """
    params = {
        "Provincia": provincia,
        "Municipio": municipio,
        "Sigla": sigla,
        "Calle": calle,
        "Numero": numero,
        "Bloque": "", "Escalera": "", "Planta": "", "Puerta": "",
    }
    try:
        r = session.get(CALLEJERO_URL, params=params, timeout=timeout)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        log.debug(f"  DNPLOC error: {e}")
        return None

    # Verificar error catastral
    err = root.find(".//c:err/c:cod", NS)
    if err is not None:
        return None

    bi = root.find(".//c:bi", NS)
    if bi is None:
        return None

    # Referencia catastral
    pc1 = (bi.findtext(".//c:pc1", "", NS) or "").strip()
    pc2 = (bi.findtext(".//c:pc2", "", NS) or "").strip()
    rc = pc1 + pc2 if pc1 and pc2 else ""

    # Código INE municipio
    cp_ine = (bi.findtext(".//c:cm", "", NS) or "").strip()
    cod_prov = (bi.findtext(".//c:cp", "", NS) or "").strip()
    nm = (bi.findtext(".//c:nm", "", NS) or "").strip()

    # Código postal
    dp = (bi.findtext(".//c:dp", "", NS) or "").strip()

    # Uso principal del inmueble
    uso = (bi.findtext(".//c:luso", "", NS) or "").strip()

    return {
        "rc":         rc,
        "cp_ine":     cp_ine,
        "cod_prov":   cod_prov,
        "nm_municipio": nm,
        "codigo_postal": dp,
        "uso_catastral": uso,
    }


def consulta_coords(provincia: str, municipio: str, rc: str,
                    session: requests.Session, timeout: int = 10) -> tuple[float, float] | None:
    """
    Obtiene coordenadas (lat, lon WGS84) de una referencia catastral.
    Devuelve (latitud, longitud) o None.
    """
    params = {
        "Provincia": provincia,
        "Municipio": municipio,
        "SRS": "EPSG:4258",  # ETRS89 ≈ WGS84 para España
        "RC": rc,
    }
    try:
        r = session.get(COORDS_URL, params=params, timeout=timeout)
        r.raise_for_status()
        root = ET.fromstring(r.content)
    except Exception as e:
        log.debug(f"  CPMRC error: {e}")
        return None

    err = root.find(".//c:err", NS)
    if err is not None:
        return None

    xcen = root.findtext(".//c:xcen", "", NS)
    ycen = root.findtext(".//c:ycen", "", NS)
    if not xcen or not ycen:
        return None

    try:
        return float(ycen.replace(",", ".")), float(xcen.replace(",", "."))
    except ValueError:
        return None


async def main(dry_run: bool, limite: int, solo_sin_municipio: bool):
    url = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(url)

    try:
        # Cargar mapa municipio INE → id SIPI
        log.info("Cargando mapa de municipios INE → SIPI…")
        mapa_ine = {
            str(r["codigo_ine"]): str(r["id"])
            for r in await conn.fetch(
                "SELECT id, codigo_ine FROM sipi.municipios WHERE codigo_ine IS NOT NULL"
            )
        }
        log.info(f"  {len(mapa_ine)} municipios con código INE")

        # Seleccionar entidades a geocodificar
        filtro_extra = "AND er.municipio_id IS NULL" if solo_sin_municipio else ""
        limite_sql   = f"LIMIT {limite}" if limite else ""

        entidades = await conn.fetch(f"""
            SELECT er.id, er.nombre, er.nombre_via, er.codigo_postal,
                   p.nombre AS provincia_nombre,
                   m.nombre AS municipio_nombre
            FROM sipi.entidades_religiosas er
            LEFT JOIN sipi.provincias p ON p.id = er.provincia_id
            LEFT JOIN sipi.municipios m ON m.id = er.municipio_id
            WHERE er.deleted_at IS NULL
              AND er.nombre_via IS NOT NULL
              AND er.latitud IS NULL
              {filtro_extra}
            ORDER BY er.nombre_via
            {limite_sql}
        """)
        log.info(f"{len(entidades)} entidades a geocodificar")

        session = requests.Session()
        session.headers["Accept"] = "text/xml"

        ok = sin_match = errores = 0

        for i, er in enumerate(entidades):
            if i > 0 and i % 100 == 0:
                log.info(f"  Progreso: {i}/{len(entidades)} — ok={ok} sin_match={sin_match}")

            provincia   = (er["provincia_nombre"] or "").upper()
            municipio   = (er["municipio_nombre"]  or "").upper()
            sigla, calle, numero = parsear_via(er["nombre_via"] or "")

            dnp = consulta_dnploc(provincia, municipio, sigla, calle, numero, session)
            time.sleep(0.2)  # Rate limit: ~5 req/s

            if not dnp or not dnp["rc"]:
                sin_match += 1
                continue

            # Intentar obtener coordenadas
            coords = consulta_coords(provincia, municipio, dnp["rc"], session)
            time.sleep(0.2)

            # Resolver municipio_id por código INE
            cod_ine = (dnp["cod_prov"] or "").zfill(2) + (dnp["cp_ine"] or "").zfill(3)
            municipio_id = mapa_ine.get(cod_ine)

            if not dry_run:
                set_parts = [
                    "referencia_catastral = $2",
                    "uso_catastral = $3",
                    "updated_at = $4",
                ]
                params: list = [
                    str(er["id"]),
                    dnp["rc"],
                    (dnp.get("uso_catastral") or "")[:100] or None,
                    __import__("datetime").datetime.now(),
                ]

                idx = 5
                if coords:
                    set_parts.append(f"latitud = ${idx},  longitud = ${idx+1}")
                    params += [coords[0], coords[1]]
                    idx += 2

                if municipio_id and not er["municipio_nombre"]:
                    set_parts.append(f"municipio_id = ${idx}")
                    params.append(municipio_id)
                    idx += 1

                await conn.execute(
                    f"UPDATE sipi.entidades_religiosas SET {', '.join(set_parts)} WHERE id = $1",
                    *params,
                )

            ok += 1

        log.info(
            f"Completado: {ok} geocodificadas, {sin_match} sin match, {errores} errores"
            + (" [DRY-RUN]" if dry_run else "")
        )

    finally:
        session.close()
        await conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Geocodifica entidades religiosas via Catastro OVC")
    parser.add_argument("--dry-run",           action="store_true")
    parser.add_argument("--limite",            type=int, default=0,
                        help="Máximo de entidades a procesar (0=todas)")
    parser.add_argument("--solo-sin-municipio", action="store_true",
                        help="Procesar solo las entidades sin municipio_id resuelto")
    args = parser.parse_args()
    asyncio.run(main(args.dry_run, args.limite, args.solo_sin_municipio))
