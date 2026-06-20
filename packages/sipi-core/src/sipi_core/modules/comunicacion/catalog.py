# modules/comunicacion/catalog.py
"""Catálogo de tipos de notificación por defecto (fuente del seed)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TipoNotifDef:
    codigo: str
    nombre: str
    categoria: str = "dominio"
    prioridad: str = "normal"
    requiere_accion: bool = False
    template_asunto: str = ""
    template_cuerpo: str = ""
    icono: str = ""


TIPOS: List[TipoNotifDef] = [
    TipoNotifDef("hallazgo.propuesto", "Nuevo hallazgo propuesto", "expediente", "alta", True,
                 "Nuevo hallazgo: {titulo}",
                 "Se ha detectado un hallazgo ({tipo_evento}) pendiente de validación.", "search"),
    TipoNotifDef("expediente.ratificado", "Hallazgo ratificado", "expediente", "normal", False,
                 "Hallazgo ratificado: {titulo}",
                 "El hallazgo ha sido ratificado por {validador}.", "check"),
    TipoNotifDef("expediente.descartado", "Hallazgo descartado", "expediente", "normal", False,
                 "Hallazgo descartado: {titulo}",
                 "El hallazgo ha sido descartado por {validador}.", "x"),
    TipoNotifDef("dataset.actualizado", "Dataset actualizado (ODMGR)", "vigilancia", "normal", False,
                 "Dataset actualizado: {resource_name}",
                 "Nueva versión {dataset_version}: {altas} altas, {modificaciones} modif., {bajas} bajas.", "database"),
    TipoNotifDef("scoring.resultado", "Resultado de valoración", "vigilancia", "normal", False,
                 "Valoración completada: {resource_name}",
                 "Se han valorado {n} candidatos; {ciertos} ciertos, {dudosos} dudosos.", "gauge"),
]
