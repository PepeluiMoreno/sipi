# -*- coding: utf-8 -*-
"""Transporte ODM (urllib) para los recursos BDNS, sobre la lógica pura de
sipi-core. El consumidor batch resuelve nombre→id→último dataset y entrega las
concesiones ya normalizadas y filtradas a NIF R/G.

La normalización del registro, el scorer y la resolución son de
`sipi_core.modules.discovery.subvenciones` (fuente única); aquí solo vive el
acoplamiento al cliente ODM (`ODMClient._post_json` / `iter_jsonl`).
"""
from __future__ import annotations

from typing import Iterator, Optional

from sipi_core.modules.discovery.subvenciones import (
    ConcesionBDNS, to_concesion as _to_concesion, extraer_nif_nombre,  # noqa: F401
    convocatoria_texto, RESOURCE_CONCESIONES, RESOURCE_CONVOCATORIAS,
    Q_RESOURCES, q_datasets, resolver_recurso_id, elegir_ultimo_dataset,
    recursos_por_ejercicio, ETIQUETA_HIST_CONCESIONES,
)


def resolver_ultimo_dataset(client, resource_id: str) -> Optional[str]:
    data = client._post_json("/graphql", {"query": q_datasets(resource_id)})
    return elegir_ultimo_dataset((data.get("data") or {}).get("datasets") or [])


def _dataset_de_recurso(client, resource_name: str) -> Optional[str]:
    data = client._post_json("/graphql", {"query": Q_RESOURCES})
    rid = resolver_recurso_id((data.get("data") or {}).get("resources") or [], resource_name)
    if not rid:
        return None
    return resolver_ultimo_dataset(client, rid)


def iter_concesiones(client, resource_name: str = RESOURCE_CONCESIONES,
                     anio: Optional[int] = None) -> Iterator[ConcesionBDNS]:
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


def iter_concesiones_historico(client, etiqueta: str = ETIQUETA_HIST_CONCESIONES
                               ) -> Iterator[ConcesionBDNS]:
    """Une el ÚLTIMO dataset de cada recurso hijo por ejercicio de la colección
    BDNS (los que crea seed_bdns_ejercicios.py en ODM), de más reciente a más
    antiguo, filtrando a NIF R/G y deduplicando por codConcesion (por si conviven
    granularidad anual y mensual del mismo año). Si no hay hijos, no emite nada
    (el consumidor puede recaer en iter_concesiones del recurso del año en curso).
    """
    data = client._post_json("/graphql", {"query": Q_RESOURCES})
    hijos = recursos_por_ejercicio((data.get("data") or {}).get("resources") or [], etiqueta)
    vistos: set = set()
    for rid, _name, _clave in hijos:
        ds = resolver_ultimo_dataset(client, rid)
        if not ds:
            continue
        for rec in client.iter_jsonl(ds):
            cod = rec.get("codConcesion")
            if cod and cod in vistos:
                continue
            c = _to_concesion(rec)
            if c is None:
                continue
            if cod:
                vistos.add(cod)
            yield c


def construir_indice_convocatorias(client,
                                   resource_name: str = RESOURCE_CONVOCATORIAS) -> dict[int, str]:
    """Índice id_convocatoria → texto de finalidad. Tolerante a ausencia: {}."""
    indice: dict[int, str] = {}
    try:
        ds = _dataset_de_recurso(client, resource_name)
        if not ds:
            return {}
        for rec in client.iter_jsonl(ds):
            cid, texto = convocatoria_texto(rec)
            if cid is not None and texto:
                indice[cid] = texto
    except Exception:
        return {}
    return indice
