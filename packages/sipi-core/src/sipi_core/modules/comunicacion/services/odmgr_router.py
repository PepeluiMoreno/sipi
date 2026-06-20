# modules/comunicacion/services/odmgr_router.py
"""
Router de eventos ODMGR (§2bis del diseño).

Una `OdmgrNotification` (data_update | search_finding) NO es solo monitorización:
es un evento que se bifurca según `notification_type` y la POLÍTICA configurable
(módulo `configuracion`, clave `evento.<tipo>.<fuente>.accion`):

  - (a) NOTIFY  → notificación de dominio a los roles implicados (comunicacion)
  - (b) TRIGGER → dispara el pipeline de descubrimiento (extracción→análisis→
                  scoring→materialización en Expediente) en services/discovery,
                  orquestado por apps/sipi-survey.

Este módulo decide (a)/(b)/ambas y ejecuta (a). El (b) se delega a un callable
inyectable (`trigger_pipeline`) que vive en services/discovery (no en el core),
para no acoplar el dominio al pipeline.
"""
from __future__ import annotations
from typing import Callable, Optional, Dict, Any, List

from sqlalchemy.orm import Session

from sipi_core.modules.configuracion.services import configuracion_service as cfg
from sipi_core.modules.comunicacion.services import notificacion_service as notif

# Tipo del hook del pipeline: (session, evento) -> dict resultado
TriggerPipeline = Callable[[Session, Any], Dict[str, Any]]


def _accion_para(session: Session, notification_type: str, fuente: Optional[str]) -> str:
    """Lee la política de configuracion. Devuelve: notify | trigger | trigger+notify | ignore."""
    if fuente:
        val = cfg.get(session, f"evento.{notification_type}.{fuente}.accion", ambito="survey", default=None)
        if val:
            return val
    return cfg.get(session, f"evento.{notification_type}.accion", ambito="survey", default="notify")


def enrutar(session: Session, evento, *,
            trigger_pipeline: Optional[TriggerPipeline] = None,
            roles_notificar: Optional[List[str]] = None) -> Dict[str, Any]:
    """Procesa un OdmgrNotification. Devuelve un resumen de lo realizado."""
    ntype = getattr(evento, "notification_type", "data_update")
    fuente = getattr(evento, "resource_name", None)
    accion = _accion_para(session, ntype, fuente)
    resultado: Dict[str, Any] = {"accion": accion, "notificadas": 0, "pipeline": None}

    if accion in ("notify", "trigger+notify"):
        contexto = {
            "resource_name": fuente or "—",
            "dataset_version": getattr(evento, "dataset_version", "") or "",
        }
        creadas = notif.notificar(
            session, "dataset.actualizado",
            roles=roles_notificar or ["operador_vigilancia"],
            contexto=contexto,
            entidad_tipo="OdmgrNotification", entidad_id=getattr(evento, "id", None),
        )
        resultado["notificadas"] = len(creadas)

    if accion in ("trigger", "trigger+notify") and trigger_pipeline is not None:
        resultado["pipeline"] = trigger_pipeline(session, evento)

    return resultado
