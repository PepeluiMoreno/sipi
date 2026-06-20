"""Consumidor de OpenDataManager (ODM) para el ETL de SIPI.

SIPI no extrae: consume los recursos producidos por ODM y los resuelve sobre
los modelos de sipi-core. El ensamblaje (fusión, scoring, hallazgos) es del
consumidor.
"""
from .client import ODMClient
from .pipeline import poblar_recurso, poblar_todo

__all__ = ["ODMClient", "poblar_recurso", "poblar_todo"]
