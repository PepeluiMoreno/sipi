#!/usr/bin/env python3
"""
load/enriquecer_er_nif.py — Enriquece entidades religiosas con NIFs y subvenciones BDNS.

Prerequisito: el recurso "Concesiones de subvenciones públicas" de opendatamanager
debe tener un dataset generado (ejecutado al menos una vez).

Flujo:
  1. Consulta opendatamanager para obtener el último dataset del recurso BDNS concesiones
  2. Descarga el JSONL línea a línea (streaming) desde /api/datasets/{id}/data.jsonl
  3. Filtra registros cuyo campo 'beneficiario' empieza por NIF R... o G...
     (entidades religiosas y asociaciones — sin máscara RGPD)
  4. Cruza por nombre normalizado con entidades SIPI sin NIF
  5. Actualiza nif en sipi.entidades_religiosas
  6. Inserta concesiones en sipi.subvenciones_entidades (idempotente por cod_concesion)

Uso:
    python load/enriquecer_er_nif.py --año 2023
    python load/enriquecer_er_nif.py --año 2023 --dry-run
    python load/enriquecer_er_nif.py --año 2023 --informe
    python load/enriquecer_er_nif.py --odm-url http://odmgr_app:8040 --año 2024

El parámetro --año es obligatorio: el dataset BDNS completo contiene millones
de registros y debe procesarse año a año. opendatamanager debe tener un dataset
generado para ese año (recurso "Concesiones BDNS {año}" o filtrado por fecha).
"""

import argparse
import asyncio
import json
import logging
import re
import uuid
from datetime import datetime
from pathlib import Path

import asyncpg
import requests
import os

load_dotenv(Path(__file__).parent.parent / ".env")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger(__name__)

SIPI_URL = os.getenv("DATABASE_URL", "").replace("postgresql+asyncpg://", "postgresql://")

# Nombre del recurso BDNS concesiones en opendatamanager
RESOURCE_NAME = "Concesiones de subvenciones públicas"
RESOURCE_ID   = "38942bf2-c6d2-4381-86f4-9114ba2dbef9"  # ID estable en esta instalación

# NIF de entidades religiosas (R) y asociaciones/fundaciones (G)
RE_NIF_RG = re.compile(r'^[RG]\d', re.IGNORECASE)


def _norm(texto: str) -> str:
    tabla = str.maketrans("áéíóúÁÉÍÓÚàèìòùüÜñÑ", "aeiouAEIOUaeiouuUnn")
    return re.sub(r"[^a-z0-9 ]", " ", texto.lower().translate(tabla)).strip()


def extraer_nif_nombre(campo: str) -> tuple[str, str]:
    """'R1234567A NOMBRE ENTIDAD' → ('R1234567A', 'NOMBRE ENTIDAD')"""
    parts = campo.strip().split(maxsplit=1)
    nif   = parts[0].strip(":-") if parts else ""
    nombre = parts[1].strip() if len(parts) > 1 else ""
    return nif, nombre


def parse_fecha(valor) -> datetime | None:
    if not valor:
        return None
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(str(valor).strip()[:10], fmt)
        except ValueError:
            pass
    return None


def obtener_dataset_para_año(odm_url: str, año: int) -> str | None:
    """
    Busca en opendatamanager el dataset BDNS correspondiente al año indicado.
    Primero busca un recurso específico del año ("Concesiones BDNS {año}"),
    luego cae al recurso genérico de concesiones.
    """
    # Intentar recurso específico del año vía GraphQL
    try:
        query = '{  datasets(resourceId: "%s") { id createdAt } }' % RESOURCE_ID
        r = requests.post(f"{odm_url}/graphql", json={"query": query}, timeout=15)
        if r.status_code == 200:
            datasets = r.json().get("data", {}).get("datasets", [])
            # Filtrar por datasets creados en el año indicado
            for d in datasets:
                created = (d.get("createdAt") or "")[:4]
                if created == str(año):
                    log.info(f"Dataset {año} encontrado: {d['id']}")
                    return d["id"]
            # Si no hay uno específico del año, usar el más reciente
            if datasets:
                log.info(f"Usando dataset más reciente (no hay específico de {año})")
                return datasets[0]["id"]
    except Exception as e:
        log.debug(f"  Error GraphQL: {e}")

    # Fallback REST
    try:
        r = requests.get(f"{odm_url}/api/resources/{RESOURCE_ID}/datasets", timeout=15)
        if r.status_code == 200 and r.json():
            return r.json()[0]["id"]
    except Exception as e:
        log.debug(f"  Error REST: {e}")

    return None


def stream_jsonl(odm_url: str, dataset_id: str, año: int):
    """
    Genera registros del JSONL del dataset línea a línea (streaming).
    Solo emite registros con NIF R/G y fecha de concesión del año indicado.
    """
    url = f"{odm_url}/api/datasets/{dataset_id}/data.jsonl"
    log.info(f"Streaming BDNS {año} desde {url}")

    with requests.get(url, stream=True, timeout=300) as r:
        r.raise_for_status()
        for line in r.iter_lines():
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            # Filtrar por año
            fecha = str(rec.get("fechaConcesion") or "")[:4]
            if fecha and fecha != str(año):
                continue
            ben = rec.get("beneficiario", "") or ""
            nif, nombre = extraer_nif_nombre(ben)
            if nombre and RE_NIF_RG.match(nif):
                yield rec, nif.upper(), _norm(nombre)


async def main(dry_run: bool, solo_informe: bool, odm_url: str, año: int):
    # Verificar que hay dataset disponible
    dataset_id = obtener_dataset_para_año(odm_url, año)
    if not dataset_id:
        log.error(
            f"No se encontró dataset para {año} del recurso '{RESOURCE_NAME}'. "
            f"Ejecuta primero el recurso desde {odm_url}"
        )
        return

    log.info(f"Usando dataset BDNS: {dataset_id}")

    sipi = await asyncpg.connect(SIPI_URL)
    now  = datetime.now()

    try:
        # ── Índice SIPI ───────────────────────────────────────────────────────
        entidades = await sipi.fetch("""
            SELECT id, nombre, nif FROM sipi.entidades_religiosas
            WHERE deleted_at IS NULL
        """)
        indice_sipi: dict[str, tuple] = {
            _norm(e["nombre"]): (str(e["id"]), e["nif"])
            for e in entidades
            if e["nombre"]
        }
        log.info(
            f"SIPI: {len(entidades)} entidades "
            f"({sum(1 for e in entidades if e['nif'])} con NIF)"
        )

        # ── Códigos ya en BD ──────────────────────────────────────────────────
        existentes = {
            r["cod_concesion"]
            for r in await sipi.fetch(
                "SELECT cod_concesion FROM sipi.subvenciones_entidades"
            )
        }

        # ── Streaming y cruce ─────────────────────────────────────────────────
        procesados = nifs_act = conc_nuevas = sin_match = 0

        for rec, nif, bnorm in stream_jsonl(odm_url, dataset_id, año):
            procesados += 1
            if procesados % 100_000 == 0:
                log.info(
                    f"  {procesados:,} registros R/G procesados "
                    f"| NIFs={nifs_act} concesiones={conc_nuevas}"
                )

            # Match en SIPI
            er_id = er_nif = None
            match = indice_sipi.get(bnorm)
            if match:
                er_id, er_nif = match
            else:
                for snorm, (sid, snif) in indice_sipi.items():
                    if bnorm and (bnorm in snorm or snorm in bnorm):
                        er_id, er_nif = sid, snif
                        break

            if not er_id:
                sin_match += 1
                continue

            if solo_informe:
                nifs_act += 1
                conc_nuevas += 1
                continue

            # Actualizar NIF
            if not er_nif and not dry_run:
                await sipi.execute(
                    "UPDATE sipi.entidades_religiosas SET nif=$1, updated_at=$2 WHERE id=$3",
                    nif, now, er_id,
                )
                indice_sipi[bnorm] = (er_id, nif)
                nifs_act += 1

            # Insertar concesión
            cod = rec.get("codConcesion") or ""
            if not cod or cod in existentes:
                continue
            existentes.add(cod)
            conc_nuevas += 1

            if not dry_run:
                await sipi.execute(
                    """
                    INSERT INTO sipi.subvenciones_entidades (
                        id, entidad_religiosa_id, cod_concesion, id_bdns, id_persona_bdns,
                        fecha_concesion, importe, ayuda_equivalente,
                        instrumento, beneficiario_bdns,
                        id_convocatoria_bdns, numero_convocatoria, convocatoria,
                        descripcion_cooficial, tiene_proyecto, codigo_invente,
                        nivel1, nivel2, nivel3, url_bdns,
                        created_at
                    ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13,$14,$15,$16,$17,$18,$19,$20,$21)
                    ON CONFLICT (cod_concesion) DO NOTHING
                    """,
                    str(uuid.uuid4()), er_id, cod,
                    rec.get("id"), rec.get("idPersona"),
                    parse_fecha(rec.get("fechaConcesion")),
                    rec.get("importe"), rec.get("ayudaEquivalente"),
                    (rec.get("instrumento") or "")[:200] or None,
                    (rec.get("beneficiario") or "")[:500] or None,
                    rec.get("idConvocatoria"),
                    (str(rec.get("numeroConvocatoria") or ""))[:50] or None,
                    (rec.get("convocatoria") or "")[:500] or None,
                    (rec.get("descripcionCooficial") or "")[:500] or None,
                    rec.get("tieneProyecto"),
                    (str(rec.get("codigoInvente") or ""))[:50] or None,
                    (rec.get("nivel1") or "")[:50] or None,
                    (rec.get("nivel2") or "")[:200] or None,
                    (rec.get("nivel3") or "")[:200] or None,
                    (rec.get("urlBR") or "")[:500] or None,
                    now,
                )

        log.info(
            f"Completado: {nifs_act} NIFs"
            + (" (simulados)" if solo_informe else " actualizados")
            + f", {conc_nuevas} concesiones"
            + (" (simuladas)" if solo_informe else " cargadas")
            + f", {sin_match} sin match"
            + (" [DRY-RUN]" if dry_run else "")
        )

    finally:
        await sipi.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Enriquece entidades religiosas SIPI con NIFs y subvenciones BDNS"
    )
    parser.add_argument("--dry-run",  action="store_true")
    parser.add_argument("--informe",  action="store_true", help="Solo estadísticas")
    parser.add_argument(
        "--año", type=int, required=True,
        help="Año de concesiones a procesar (ej: 2023). Obligatorio."
    )
    parser.add_argument(
        "--odm-url",
        default=os.getenv("OPENDATAMANAGER_URL", "http://odmgr_app:8040"),
        help="URL base de opendatamanager (default: http://odmgr_app:8040)"
    )
    args = parser.parse_args()
    asyncio.run(main(args.dry_run, args.informe, args.odm_url, args.año))
