# -*- coding: utf-8 -*-
"""Persistencia DB-first de los parámetros del proceso de descubrimiento.

Un perfil = un juego de ponderaciones/umbrales (el `DiscoveryConfig` del módulo
de investigación, services/etl/.../fusion/config.py). Editable desde el UI; el
servicio de descubrimiento carga el perfil ACTIVO y, si no hay, usa los valores
por defecto del código (DiscoveryConfig()). Las claves de `parametros` coinciden
con DiscoveryConfig.to_dict(), de modo que `DiscoveryConfig.from_mapping(parametros)`
reconstruye la configuración.
"""
from __future__ import annotations
from typing import Optional

from sqlalchemy import String, Text, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from sipi_core.db.registry import Base
from sipi_core.mixins import UUIDPKMixin, AuditMixin


class ConfiguracionDescubrimiento(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "configuracion_descubrimiento"

    nombre: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    # = DiscoveryConfig.to_dict() (pesos, umbrales, tolerancias, pesos_religiosidad)
    parametros: Mapped[dict] = mapped_column(JSONB, nullable=False)
    activo: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
