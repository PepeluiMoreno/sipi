# -*- coding: utf-8 -*-
"""Shim: el scorer canónico vive en sipi-core (fuente única de la lógica de
dominio). Se re-exporta aquí para no romper imports del consumidor/CLI."""
from sipi_core.modules.discovery.subvenciones import (  # noqa: F401
    norm as _norm,
    clasificar_nif, detectar_finalidad_rehab, nombre_es_religioso, evaluar,
    ClaseNif, Finalidad, Fiabilidad,
)

__all__ = [
    "_norm", "clasificar_nif", "detectar_finalidad_rehab", "nombre_es_religioso",
    "evaluar", "ClaseNif", "Finalidad", "Fiabilidad",
]
