# modules/acceso/auditoria.py
from __future__ import annotations
from datetime import datetime
from typing import Optional, TYPE_CHECKING
from sqlalchemy import String, Text, Boolean, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin

if TYPE_CHECKING:
    from sipi_core.modules.usuarios.users import Usuario


class AuditoriaAcceso(UUIDPKMixin, Base):
    """Traza de autorizaciones (quién intentó qué transacción y con qué resultado)."""
    __tablename__ = "auditoria_acceso"

    usuario_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id"), index=True, nullable=True)
    transaccion: Mapped[str] = mapped_column(String(80), index=True, nullable=False,
                                             comment="Código de transacción solicitada")
    permitido: Mapped[bool] = mapped_column(Boolean, nullable=False)
    ambito: Mapped[Optional[str]] = mapped_column(String(100), comment="Ámbito territorial evaluado, si aplica")
    detalle: Mapped[Optional[str]] = mapped_column(Text)
    ts: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    usuario: Mapped[Optional["Usuario"]] = relationship("Usuario", foreign_keys=[usuario_id], viewonly=True)

    __table_args__ = (
        Index("ix_auditoria_acceso_usuario_ts", "usuario_id", "ts"),
    )
