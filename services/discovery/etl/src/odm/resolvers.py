# -*- coding: utf-8 -*-
"""Resolvers: resuelven registros normalizados de ODM sobre modelos sipi-core.

Cada resolver hace UPSERT por una clave estable (no por nombre libre):
  - Diócesis            -> nombre (o wikidata_qid)
  - Entidad religiosa   -> numero_registro (nº inscripción RER)   [REQUERIDO]
  - Administración      -> codigo_oficial (DIR3)
  - Notaría             -> codigo_oficial
  - Registro Propiedad  -> identificacion (código oficial)
  - Inmueble (IAPH)     -> denominación + municipio (directo)
  - Inmueble (OSM/CEE)  -> NO directo: alimentan el módulo de fusión

Los mapas FIELDS_* traducen el JSON normalizado de cada recurso ODM a columnas
sipi-core. Están sembrados con los esquemas conocidos (doc RER de ODM, manifests,
esquema del antiguo notarias-registros-backend) y DEBEN verificarse contra el
`schema.json` real de cada dataset (`/api/datasets/{id}/schema.json`).
"""
from __future__ import annotations

from sqlalchemy import select

from sipi_core.models import (
    Diocesis, EntidadReligiosa, Administracion, Notaria, RegistroPropiedad,
    Inmueble,
)


def _first(d: dict, *keys, default=None):
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return default


# =============================================================================
# AGENTES
# =============================================================================

async def upsert_diocesis(session, rec: dict, fuente: str) -> str:
    nombre = _first(rec, "nombre", "diocesis", "name")
    qid = _first(rec, "wikidata_qid", "wikidata", "qid")
    if not nombre and not qid:
        return "skip"
    stmt = select(Diocesis)
    obj = None
    if qid:
        obj = (await session.execute(stmt.where(Diocesis.wikidata_qid == qid))).scalar_one_or_none()
    if obj is None and nombre:
        obj = (await session.execute(stmt.where(Diocesis.nombre == nombre))).scalar_one_or_none()
    if obj is None:
        obj = Diocesis(nombre=nombre or qid)
        session.add(obj)
        action = "insert"
    else:
        action = "update"
    if nombre:
        obj.nombre = nombre
    if qid:
        obj.wikidata_qid = qid
    _apply_contacto(obj, rec)
    return action


async def upsert_entidad_religiosa(session, rec: dict, fuente: str) -> str:
    # Clave: nº inscripción RER. CONFER/parroquias sin nº RER no pueden crear
    # EntidadReligiosa (numero_registro es NOT NULL/UNIQUE): se derivan a
    # enriquecimiento por NIF/nombre o quedan en cola de enlace.
    num = _first(rec, "numero_inscripcion", "numero_registro", "num_registro")
    if not num:
        return "skip_no_rer"
    obj = (await session.execute(
        select(EntidadReligiosa).where(EntidadReligiosa.numero_registro == str(num))
    )).scalar_one_or_none()
    nombre = _first(rec, "nombre", "denominacion", "razon_social")
    if obj is None:
        obj = EntidadReligiosa(numero_registro=str(num), nombre=nombre or str(num))
        session.add(obj)
        action = "insert"
    else:
        action = "update"
    if nombre:
        obj.nombre = nombre
    nif = _first(rec, "nif", "cif", "identificacion")
    if nif:
        obj.identificacion = nif
    _apply_contacto(obj, rec)
    return action


async def upsert_administracion(session, rec: dict, fuente: str) -> str:
    codigo = _first(rec, "codigo_dir3", "dir3", "codigo_oficial", "id_organo")
    if not codigo:
        return "skip"
    obj = (await session.execute(
        select(Administracion).where(Administracion.codigo_oficial == str(codigo))
    )).scalar_one_or_none()
    nombre = _first(rec, "nombre", "denominacion", "descripcion")
    if obj is None:
        obj = Administracion(nombre=nombre or str(codigo), codigo_oficial=str(codigo))
        session.add(obj)
        action = "insert"
    else:
        action = "update"
    if nombre:
        obj.nombre = nombre
    obj.ambito = _first(rec, "ambito", "nivel_administracion", default=obj.ambito if obj else None)
    obj.nivel_jerarquico = _first(rec, "nivel_jerarquico", default=getattr(obj, "nivel_jerarquico", None))
    obj.tipo_organo = _first(rec, "tipo_organo", default=getattr(obj, "tipo_organo", None))
    _apply_contacto(obj, rec)
    return action


async def upsert_notaria(session, rec: dict, fuente: str) -> str:
    codigo = _first(rec, "codigo_notaria", "codigo_oficial", "codigo")
    if not codigo:
        return "skip"
    obj = (await session.execute(
        select(Notaria).where(Notaria.codigo_oficial == str(codigo))
    )).scalar_one_or_none()
    nombre = _first(rec, "nombre_notario", "nombre", "titular")
    if obj is None:
        obj = Notaria(codigo_oficial=str(codigo), nombre=nombre or str(codigo))
        session.add(obj)
        action = "insert"
    else:
        action = "update"
    if nombre:
        obj.nombre = nombre
    _apply_contacto(obj, rec)
    return action


async def upsert_registro_propiedad(session, rec: dict, fuente: str) -> str:
    codigo = _first(rec, "codigo_registro", "codigo_oficial", "codigo", "identificacion")
    if not codigo:
        return "skip"
    obj = (await session.execute(
        select(RegistroPropiedad).where(RegistroPropiedad.identificacion == str(codigo))
    )).scalar_one_or_none()
    nombre = _first(rec, "denominacion", "nombre")
    if obj is None:
        obj = RegistroPropiedad(identificacion=str(codigo), nombre=nombre or str(codigo))
        session.add(obj)
        action = "insert"
    else:
        action = "update"
    if nombre:
        obj.nombre = nombre
    _apply_contacto(obj, rec)
    return action


# =============================================================================
# INMUEBLES
# =============================================================================

async def upsert_inmueble_iaph(session, rec: dict, fuente: str) -> str:
    """IAPH: patrimonio inmueble andaluz, inserción directa por id IAPH."""
    iaph_id = _first(rec, "id_iaph", "codigo", "id")
    nombre = _first(rec, "denominacion", "nombre", "name")
    if not nombre:
        return "skip"
    # Clave estable: denominacion (idealmente id IAPH guardado en una denominación)
    obj = (await session.execute(
        select(Inmueble).where(Inmueble.nombre == nombre)
    )).scalar_one_or_none()
    if obj is None:
        obj = Inmueble(nombre=nombre)
        session.add(obj)
        action = "insert"
    else:
        action = "update"
    lat = _first(rec, "lat", "latitud")
    lon = _first(rec, "lon", "longitud")
    if lat and lon:
        from geoalchemy2.elements import WKTElement
        obj.coordenadas = WKTElement(f"POINT({lon} {lat})", srid=4326)
    return action


# OSM y CEE inmatriculaciones NO se insertan aquí: se vuelcan a la fusión
# (services/discovery/etl/src/modules/fusion), que deduplica CEE×OSM y emite hallazgos.
# Ver pipeline.feed_fusion().


# =============================================================================
# helpers
# =============================================================================

def _apply_contacto(obj, rec: dict):
    """Vuelca dirección/contacto plano a las columnas estructuradas (best-effort).
    La resolución de municipio_id (geocoding a Municipio) se delega a una pasada
    posterior, igual que en el modelo de inmuebles."""
    direccion = _first(rec, "domicilio_social", "direccion", "domicilio")
    if direccion and hasattr(obj, "nombre_via"):
        obj.nombre_via = direccion[:255]
    tel = _first(rec, "telefono")
    if tel and hasattr(obj, "telefono"):
        obj.telefono = str(tel)[:20]
    email = _first(rec, "email", "correo")
    if email and hasattr(obj, "email_corporativo"):
        obj.email_corporativo = email[:255]
    web = _first(rec, "sitio_web", "web", "url")
    if web and hasattr(obj, "sitio_web"):
        obj.sitio_web = web[:500]


# Despacho por dominio (lo usa el pipeline)
RESOLVERS = {
    "diocesis": upsert_diocesis,
    "entidad_religiosa": upsert_entidad_religiosa,
    "administracion": upsert_administracion,
    "notaria": upsert_notaria,
    "registro_propiedad": upsert_registro_propiedad,
}

# Inmuebles con resolver directo (los demás van a fusión)
RESOLVERS_INMUEBLE_DIRECTO = {
    "IAPH": upsert_inmueble_iaph,
}
