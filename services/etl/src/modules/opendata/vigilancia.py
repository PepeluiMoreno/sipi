# -*- coding: utf-8 -*-
"""Procesos de vigilancia (lado SIPI).

Orquesta el refresco y el consumo de datasets de ODM hacia las tablas maestras
de SIPI. El disparo programado (cron) vive en ODM; aquí cubrimos:
  - refresco **a demanda** (executeResource) — lo que pulsa el usuario en el UI;
  - **consumo**: leer el dataset y upsert en la tabla maestra vía un MaestroSink.

Las fuentes de EVENTOS (BDNS/PLACSP/portales/OSM) no upsertan maestros: van al
descubrimiento (fusión -> Expediente), que es otro consumidor del mismo cliente.
"""
import logging
from .client import ODMClient
from .mapping import MAPEOS
from .sink import MaestroSink, LogSink

logger = logging.getLogger(__name__)

__all__ = ["descubrir_datasets", "refrescar", "sincronizar_maestro", "sincronizar_todos"]


def descubrir_datasets(client: ODMClient):
    """Lista los datasets que ODM expone (queryName + fields)."""
    return client.list_datasets()


def refrescar(client: ODMClient, resource_id: str, params=None):
    """Refresco a demanda de un resource en ODM."""
    logger.info("Refresco a demanda del resource %s", resource_id)
    return client.execute_resource(resource_id, params)


def _mapear(filas, mapeo):
    out = []
    for fila in filas:
        reg = {}
        for campo_odm, col_sipi in mapeo.columnas.items():
            reg[col_sipi] = fila.get(campo_odm)
        if reg.get(mapeo.clave_natural) in (None, ""):
            continue  # sin clave natural no se puede upsertar
        out.append(reg)
    return out


def sincronizar_maestro(client: ODMClient, mapeo, sink: MaestroSink, limit=None) -> int:
    """Lee el dataset del mapeo, lo proyecta a columnas SIPI y upserta."""
    filas = client.fetch_dataset(mapeo.dataset_query_name, mapeo.campos_origen, limit=limit)
    registros = _mapear(filas, mapeo)
    n = sink.upsert(mapeo.tabla_sipi, registros, mapeo.clave_natural)
    logger.info("Sincronizado %s: %d registros (de %d filas ODM)", mapeo.tabla_sipi, n, len(filas))
    return n


def sincronizar_todos(client: ODMClient, sink: MaestroSink = None, mapeos=None, limit=None) -> dict:
    """Sincroniza todas las tablas maestras mapeadas. Devuelve {tabla: n}."""
    sink = sink or LogSink()
    mapeos = mapeos or MAPEOS
    resultado = {}
    for mapeo in mapeos:
        try:
            resultado[mapeo.tabla_sipi] = sincronizar_maestro(client, mapeo, sink, limit=limit)
        except Exception as e:  # un dataset que falle no debe tumbar el resto
            logger.error("Fallo sincronizando %s: %s", mapeo.tabla_sipi, e)
            resultado[mapeo.tabla_sipi] = -1
    return resultado
