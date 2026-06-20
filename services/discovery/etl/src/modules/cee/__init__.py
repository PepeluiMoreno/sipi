"""
Módulo CEE — Listado de inmatriculaciones de la Conferencia Episcopal Española.

Carga los inmuebles inmatriculados desde los CSVs (generados por transform/cee a
partir de Inmatriculaciones_CEE.xlsx) al modelo Inmueble + Inmatriculacion.
"""

from .loader import listado_ceeLoader
from .mapper import listado_ceeMapper

__all__ = ["listado_ceeLoader", "listado_ceeMapper"]
