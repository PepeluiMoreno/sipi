# models/fuentes_historiograficas.py
from __future__ import annotations
from typing import Optional, List, TYPE_CHECKING
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Boolean

from sipi_core.db.registry import Base
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.modules.inmuebles.inmuebles import InmuebleCita


class FuenteHistoriografica(UUIDPKMixin, AuditMixin, Base):
    __tablename__ = "fuentes_historiograficas"

    nombre: Mapped[str] = mapped_column(String(255), index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, index=True)

    citas_bibliograficas: Mapped[List["InmuebleCita"]] = relationship(
        "InmuebleCita",
        back_populates="fuente",
        cascade="all, delete-orphan",
    )
