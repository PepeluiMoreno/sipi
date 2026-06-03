# modules/comunicacion/services/notificacion_service.py
"""
Servicio de notificaciones de dominio: crear, listar y marcar leídas.

    notificar(session, "hallazgo.propuesto",
              usuarios=[...] | roles=["validador"],
              contexto={"titulo": "...", "tipo_evento": "...", "expediente_id": "..."})
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from sipi_core.modules.usuarios.users import Usuario
from sipi_core.modules.comunicacion.notificacion import (
    TipoNotificacion, Notificacion, PrioridadNotif,
)
from sipi_core.modules.comunicacion.services.destinatario_resolver import usuarios_por_rol


def _render(plantilla: Optional[str], contexto: Dict[str, Any]) -> str:
    if not plantilla:
        return ""
    try:
        return plantilla.format(**contexto)
    except Exception:
        return plantilla


def notificar(session: Session, tipo_codigo: str, *,
              usuarios: Optional[Iterable[Usuario]] = None,
              roles: Optional[Iterable[str]] = None,
              contexto: Optional[Dict[str, Any]] = None,
              entidad_tipo: Optional[str] = None,
              entidad_id: Optional[str] = None) -> List[Notificacion]:
    """Crea una Notificacion por destinatario. Devuelve las creadas."""
    contexto = contexto or {}
    tipo = session.execute(
        select(TipoNotificacion).where(TipoNotificacion.codigo == tipo_codigo)
    ).scalar_one_or_none()
    if tipo is None:
        raise ValueError(f"TipoNotificacion desconocido: {tipo_codigo}")

    destinatarios: Dict[str, Usuario] = {}
    for u in (usuarios or []):
        destinatarios[u.id] = u
    if roles:
        for u in usuarios_por_rol(session, roles):
            destinatarios[u.id] = u

    titulo = _render(tipo.template_asunto, contexto) or tipo.nombre
    cuerpo = _render(tipo.template_cuerpo, contexto)
    creadas: List[Notificacion] = []
    for u in destinatarios.values():
        n = Notificacion(
            tipo_id=tipo.id, usuario_id=u.id, titulo=titulo, cuerpo=cuerpo,
            prioridad=tipo.prioridad, entidad_tipo=entidad_tipo, entidad_id=entidad_id,
            accion_url=contexto.get("accion_url"),
        )
        session.add(n); creadas.append(n)
    session.flush()
    return creadas


def no_leidas(session: Session, usuario_id: str) -> List[Notificacion]:
    return list(session.execute(
        select(Notificacion).where(
            Notificacion.usuario_id == usuario_id, Notificacion.leida.is_(False)
        ).order_by(Notificacion.created_at.desc())
    ).scalars())


def contar_no_leidas(session: Session, usuario_id: str) -> int:
    return session.execute(
        select(func.count()).select_from(Notificacion).where(
            Notificacion.usuario_id == usuario_id, Notificacion.leida.is_(False))
    ).scalar_one()


def marcar_leida(session: Session, notificacion_id: str) -> None:
    n = session.get(Notificacion, notificacion_id)
    if n and not n.leida:
        n.leida = True
        n.leida_at = datetime.utcnow()
        session.flush()
