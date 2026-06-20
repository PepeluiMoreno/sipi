# modules/comunicacion/services/seed.py
"""Seed idempotente de tipos de notificación (desde catalog.py)."""
from __future__ import annotations
from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from sipi_core.modules.comunicacion.notificacion import TipoNotificacion, PrioridadNotif
from sipi_core.modules.comunicacion import catalog


def seed(session: Session) -> Dict[str, int]:
    existentes = {t.codigo: t for t in session.execute(select(TipoNotificacion)).scalars()}
    creados = 0
    for d in catalog.TIPOS:
        t = existentes.get(d.codigo)
        if t is None:
            session.add(TipoNotificacion(
                codigo=d.codigo, nombre=d.nombre, categoria=d.categoria,
                prioridad=PrioridadNotif(d.prioridad), requiere_accion=d.requiere_accion,
                template_asunto=d.template_asunto, template_cuerpo=d.template_cuerpo,
                icono=d.icono, activo=True,
            ))
            creados += 1
        else:
            t.nombre, t.categoria = d.nombre, d.categoria
            t.template_asunto, t.template_cuerpo = d.template_asunto, d.template_cuerpo
    session.commit()
    return {"tipos_creados": creados}
