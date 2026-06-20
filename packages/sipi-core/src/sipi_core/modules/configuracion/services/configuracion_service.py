# modules/configuracion/services/configuracion_service.py
"""
Acceso tipado a parámetros con caché de proceso e historial de cambios.

    from sipi_core.modules.configuracion.services import configuracion_service as cfg
    intervalo = cfg.get(session, "survey.idealista.intervalo_min", ambito="survey", default=60)
"""
from __future__ import annotations
import json
from typing import Any, Optional, Dict, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from sipi_core.modules.configuracion.configuracion import (
    Configuracion, HistorialConfiguracion, TipoDato, AmbitoConfig,
)

_CACHE: Dict[Tuple[str, str], Any] = {}


def _cast(valor: Optional[str], tipo: TipoDato) -> Any:
    if valor is None:
        return None
    if tipo == TipoDato.INT:
        return int(valor)
    if tipo == TipoDato.FLOAT:
        return float(valor)
    if tipo == TipoDato.BOOL:
        return str(valor).strip().lower() in ("1", "true", "t", "yes", "si", "sí")
    if tipo == TipoDato.JSON:
        return json.loads(valor)
    return valor


def get(session: Session, clave: str, *, ambito: str = "global", default: Any = None) -> Any:
    key = (ambito, clave)
    if key in _CACHE:
        return _CACHE[key]
    row = session.execute(
        select(Configuracion).where(
            Configuracion.clave == clave,
            Configuracion.ambito == AmbitoConfig(ambito),
        )
    ).scalar_one_or_none()
    val = default if row is None else _cast(row.valor, row.tipo_dato)
    _CACHE[key] = val
    return val


def set(session: Session, clave: str, valor: Any, *, ambito: str = "global",
        usuario_id: Optional[str] = None) -> Configuracion:
    row = session.execute(
        select(Configuracion).where(
            Configuracion.clave == clave,
            Configuracion.ambito == AmbitoConfig(ambito),
        )
    ).scalar_one_or_none()
    nuevo = valor if isinstance(valor, str) else json.dumps(valor) if isinstance(valor, (list, dict)) else str(valor)
    if row is None:
        row = Configuracion(clave=clave, valor=nuevo, ambito=AmbitoConfig(ambito), tipo_dato=TipoDato.STR)
        session.add(row)
    else:
        if not row.editable:
            raise ValueError(f"Parámetro no editable: {ambito}:{clave}")
        session.add(HistorialConfiguracion(
            configuracion_id=row.id, valor_anterior=row.valor, valor_nuevo=nuevo, usuario_id=usuario_id))
        row.valor = nuevo
    session.flush()
    _CACHE.pop((ambito, clave), None)
    return row


def invalidar_cache() -> None:
    _CACHE.clear()
