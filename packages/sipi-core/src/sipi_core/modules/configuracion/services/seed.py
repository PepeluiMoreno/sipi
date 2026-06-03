# modules/configuracion/services/seed.py
"""Seed idempotente de parámetros por defecto (desde catalog.py)."""
from __future__ import annotations
from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from sipi_core.modules.configuracion.configuracion import Configuracion, TipoDato, AmbitoConfig
from sipi_core.modules.configuracion import catalog
from sipi_core.modules.configuracion.services.configuracion_service import invalidar_cache


def seed(session: Session) -> Dict[str, int]:
    existentes = {
        (c.ambito.value, c.clave)
        for c in session.execute(select(Configuracion)).scalars()
    }
    creados = 0
    for p in catalog.PARAMETROS:
        if (p.ambito, p.clave) in existentes:
            continue
        session.add(Configuracion(
            clave=p.clave, valor=p.valor, tipo_dato=TipoDato(p.tipo_dato),
            ambito=AmbitoConfig(p.ambito), categoria=p.categoria,
            descripcion=p.descripcion, editable=True, sistema=False,
        ))
        creados += 1
    session.commit()
    invalidar_cache()
    return {"parametros_creados": creados}
