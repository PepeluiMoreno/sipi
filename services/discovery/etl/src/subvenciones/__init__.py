# -*- coding: utf-8 -*-
"""Detección de subvenciones BDNS para rehabilitación de inmuebles inmatriculados.

Consume los recursos BDNS de OpenDataManager (concesiones y convocatorias),
filtra beneficiarios con NIF R (entidad religiosa) o G (asociación/fundación),
valora la fiabilidad de que la concesión financie la rehabilitación de un
edificio inmatriculado y emite `Hallazgo` para comprobación humana.
"""
from .scoring import (
    clasificar_nif,
    detectar_finalidad_rehab,
    nombre_es_religioso,
    evaluar,
    ClaseNif,
    Finalidad,
    Fiabilidad,
)
from .fuentes import (
    ConcesionBDNS,
    iter_concesiones,
    construir_indice_convocatorias,
    iter_concesiones_historico,
    extraer_nif_nombre,
    RESOURCE_CONCESIONES,
    RESOURCE_CONVOCATORIAS,
)
from .analyzer import analizar, Censo, FUENTE, UMBRAL_CIERTO_DEFECTO

__all__ = [
    "clasificar_nif", "detectar_finalidad_rehab", "nombre_es_religioso", "evaluar",
    "ClaseNif", "Finalidad", "Fiabilidad",
    "ConcesionBDNS", "iter_concesiones", "construir_indice_convocatorias",
    "extraer_nif_nombre", "RESOURCE_CONCESIONES", "RESOURCE_CONVOCATORIAS",
    "analizar", "Censo", "FUENTE", "UMBRAL_CIERTO_DEFECTO",
]
