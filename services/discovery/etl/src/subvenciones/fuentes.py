# -*- coding: utf-8 -*-
"""Lectura de los recursos BDNS publicados por OpenDataManager.

No reextrae nada de infosubvenciones: consume el JSONL que ODM ya produce
(`ODMClient.iter_resource`). Dos piezas:

  - `iter_concesiones`: concesiones concedidas, ya filtradas a beneficiarios con
    NIF R o G (entidades religiosas / asociaciones-fundaciones).
  - `construir_indice_convocatorias`: índice opcional id_convocatoria → finalidad,
    para enriquecer el texto de finalidad cuando la concesión solo trae el título.

Esquema JSONL del recurso de concesiones (claves camelCase, verificadas contra
`load/enriquecer_er_nif.py`): beneficiario, fechaConcesion, codConcesion,
importe, ayudaEquivalente, instrumento, id, idPersona, idConvocatoria,
numeroConvocatoria, convocatoria, descripcionCooficial, nivel1/2/3, urlBR.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Iterator, Optional

from .scoring import _norm, clasificar_nif

# Nombres de recurso en ODM (deben coincidir EXACTAMENTE con `resource.name`).
# El nombre es el contrato neutral; el id es por-instalación y se resuelve.
RESOURCE_CONCESIONES = "BDNS - Concesiones de Subvenciones"
RESOURCE_CONVOCATORIAS = "BDNS - Convocatorias de Subvenciones"

_RE_NIF_RG = re.compile(r"^[RG]\d", re.IGNORECASE)


# --- resolución de recurso/dataset (esquema ODM real) -------------------------
def resolver_recurso_id(client, resource_name: str) -> Optional[str]:
    """nombre de recurso → id, listando `resources` (el esquema no acepta
    `resources(name:...)`)."""
    data = client._post_json("/graphql", {"query": "{ resources { id name } }"})
    for r in (data.get("data") or {}).get("resources") or []:
        if r.get("name") == resource_name:
            return r.get("id")
    return None


def resolver_ultimo_dataset(client, resource_id: str) -> Optional[str]:
    """id de recurso → id del último dataset publicado (mayor versión)."""
    q = ("{ datasets(resourceId:\"%s\"){ id majorVersion minorVersion patchVersion "
         "createdAt recordCount } }" % resource_id)
    data = client._post_json("/graphql", {"query": q})
    ds = (data.get("data") or {}).get("datasets") or []
    if not ds:
        return None
    ds.sort(key=lambda d: (d.get("majorVersion") or 0, d.get("minorVersion") or 0,
                           d.get("patchVersion") or 0, d.get("createdAt") or ""))
    return ds[-1]["id"]


def _dataset_de_recurso(client, resource_name: str) -> Optional[str]:
    rid = resolver_recurso_id(client, resource_name)
    if not rid:
        return None
    return resolver_ultimo_dataset(client, rid)


def extraer_nif_nombre(beneficiario: str) -> tuple[str, str]:
    """'R1234567A NOMBRE ENTIDAD' → ('R1234567A', 'NOMBRE ENTIDAD')."""
    parts = (beneficiario or "").split(maxsplit=1)
    nif = parts[0].strip(":-") if parts else ""
    nombre = parts[1].strip() if len(parts) > 1 else ""
    return nif, nombre


def _parse_fecha(valor) -> Optional[date]:
    s = str(valor or "")[:10]
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


@dataclass
class ConcesionBDNS:
    cod_concesion: str
    beneficiario_raw: str
    nif: str
    nombre: str
    importe: Optional[float]
    fecha_concesion: Optional[date]
    instrumento: Optional[str]
    id_convocatoria: Optional[int]
    numero_convocatoria: Optional[str]
    convocatoria: Optional[str]
    descripcion_cooficial: Optional[str]
    nivel1: Optional[str]
    nivel2: Optional[str]
    nivel3: Optional[str]
    url_bdns: Optional[str]
    raw: dict = field(default_factory=dict)

    def textos_finalidad(self, indice_convocatorias: Optional[dict] = None) -> list[str]:
        """Textos sobre los que se evalúa la finalidad de rehabilitación."""
        txts = [self.convocatoria, self.instrumento, self.descripcion_cooficial]
        if indice_convocatorias and self.id_convocatoria is not None:
            extra = indice_convocatorias.get(self.id_convocatoria)
            if extra:
                txts.append(extra)
        return [t for t in txts if t]


def _to_concesion(rec: dict) -> Optional[ConcesionBDNS]:
    cod = rec.get("codConcesion") or ""
    ben = rec.get("beneficiario") or ""
    nif, nombre = extraer_nif_nombre(ben)
    if not cod or not nombre or not _RE_NIF_RG.match(nif):
        return None
    return ConcesionBDNS(
        cod_concesion=cod,
        beneficiario_raw=ben,
        nif=nif.upper(),
        nombre=nombre,
        importe=rec.get("importe"),
        fecha_concesion=_parse_fecha(rec.get("fechaConcesion")),
        instrumento=rec.get("instrumento") or None,
        id_convocatoria=rec.get("idConvocatoria"),
        numero_convocatoria=(str(rec.get("numeroConvocatoria") or "") or None),
        convocatoria=rec.get("convocatoria") or None,
        descripcion_cooficial=rec.get("descripcionCooficial") or None,
        nivel1=rec.get("nivel1") or None,
        nivel2=rec.get("nivel2") or None,
        nivel3=rec.get("nivel3") or None,
        url_bdns=rec.get("urlBR") or None,
        raw=rec,
    )


def iter_concesiones(
    client,
    resource_name: str = RESOURCE_CONCESIONES,
    anio: Optional[int] = None,
) -> Iterator[ConcesionBDNS]:
    """Concesiones del último dataset del recurso, filtradas a NIF R/G y
    (opcionalmente) a un año de concesión."""
    ds = _dataset_de_recurso(client, resource_name)
    if not ds:
        return
    for rec in client.iter_jsonl(ds):
        if anio is not None:
            f = str(rec.get("fechaConcesion") or "")[:4]
            if f and f != str(anio):
                continue
        c = _to_concesion(rec)
        if c is not None:
            yield c


def construir_indice_convocatorias(
    client,
    resource_name: str = RESOURCE_CONVOCATORIAS,
) -> dict[int, str]:
    """Índice id_convocatoria → texto de finalidad (descripción de la
    convocatoria). Tolerante a la ausencia del recurso: devuelve {} si no existe.

    El recurso real de convocatorias BDNS usa la clave `id` y el texto en
    `descripcion`; se admiten alias por robustez ante cambios de esquema.
    """
    indice: dict[int, str] = {}
    try:
        ds = _dataset_de_recurso(client, resource_name)
        if not ds:
            return {}
        for rec in client.iter_jsonl(ds):
            cid = rec.get("id") or rec.get("idConvocatoria")
            if cid is None:
                continue
            texto = (
                rec.get("descripcion")
                or rec.get("descripcionFinalidad")
                or rec.get("finalidad")
                or rec.get("objeto")
                or rec.get("convocatoria")
                or ""
            )
            if texto:
                try:
                    indice[int(cid)] = str(texto)
                except (TypeError, ValueError):
                    continue
    except Exception:
        # El recurso de convocatorias puede no estar publicado todavía en ODM:
        # el analyzer seguirá usando el texto inline de cada concesión.
        return {}
    return indice
