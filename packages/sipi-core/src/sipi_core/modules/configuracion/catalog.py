# modules/configuracion/catalog.py
"""Catálogo de parámetros por defecto (fuente del seed idempotente)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class ParamDef:
    clave: str
    valor: str
    tipo_dato: str   # str | int | float | bool | json
    ambito: str      # global | sipi | survey
    categoria: str = ""
    descripcion: str = ""


PARAMETROS: List[ParamDef] = [
    # Global
    ParamDef("geo.geocoder.preferente", "nominatim", "str", "global", "geo", "Geocoder por defecto"),
    ParamDef("bdns.api_url", "https://www.infosubvenciones.es/bdnstrans/api", "str", "global", "fuentes", "API BDNS"),
    # SIPI (expedientes)
    ParamDef("expediente.auto_descartar_dias", "180", "int", "sipi", "expediente",
             "Días tras los que un propuesto sin acción se auto-descarta"),
    ParamDef("expediente.certeza.umbral_auto_ratificar", "0.85", "float", "sipi", "expediente",
             "Confianza mínima para auto-ratificar un hallazgo CIERTO"),
    ParamDef("notif.email.activo", "false", "bool", "sipi", "comunicacion", "Enviar notificaciones por email"),
    # Seguridad / sesión (Parámetros generales)
    ParamDef("seguridad.timeout_inactividad_min", "30", "int", "sipi", "seguridad",
             "Minutos de inactividad tras los que se cierra la sesión (0 = sin timeout)"),
    ParamDef("seguridad.timeout_sesion_min", "480", "int", "sipi", "seguridad",
             "Duración máxima de la sesión en minutos (0 = sin límite)"),
    # Survey (vigilancia)
    ParamDef("survey.idealista.intervalo_min", "60", "int", "survey", "vigilancia",
             "Intervalo (min) entre barridos de Idealista"),
    ParamDef("survey.portales.activos", '["idealista","fotocasa"]', "json", "survey", "vigilancia",
             "Portales de vigilancia habilitados"),
    # Política de eventos ODMGR (bifurcación notificar/trigger) — ver §2bis del diseño
    ParamDef("evento.data_update.bdns.accion", "trigger+notify", "str", "survey", "eventos",
             "Acción ante data_update de BDNS: notify | trigger | trigger+notify"),
]
