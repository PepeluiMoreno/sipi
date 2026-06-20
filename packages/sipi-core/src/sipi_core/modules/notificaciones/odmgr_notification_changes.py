# models/odmgr_notification_changes.py
"""
Cambios individuales de una notificación (diff a nivel de registro).

Cada fila representa un cambio concreto en un registro de SIPI:
  - alta:        nuevo registro en el dataset fuente
  - baja:        registro desaparecido del dataset fuente
  - modificacion: campo concreto que cambió de valor

Ciclo de vida del cambio:
  pending  → pendiente de revisión por el administrador
  accepted → aceptado; se aplicará cuando se ejecute el apply
  rejected → rechazado; no se aplicará
  applied  → ya aplicado a la BD de SIPI
  failed   → falló al intentar aplicar
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import String, Text, ForeignKey, DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin


class OdmgrNotificationChange(UUIDPKMixin, Base):
    """Un cambio individual (alta / baja / modificación de campo) dentro de una notificación."""
    __tablename__ = "odmgr_notification_changes"

    # Notificación padre
    notification_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.odmgr_notifications.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Tipo de cambio
    change_type: Mapped[str] = mapped_column(
        String(20), nullable=False, index=True
    )  # alta | baja | modificacion

    # Referencia al registro afectado
    entity_id:   Mapped[Optional[str]] = mapped_column(String(200))  # clave natural en la fuente
    entity_name: Mapped[Optional[str]] = mapped_column(String(500))  # nombre legible

    # Solo para change_type=modificacion
    field_name: Mapped[Optional[str]] = mapped_column(String(100))
    old_value:  Mapped[Optional[str]] = mapped_column(Text)
    new_value:  Mapped[Optional[str]] = mapped_column(Text)

    # Snapshot completo del registro (JSON) — útil para aplicar altas sin rellamada a la fuente
    raw_record: Mapped[Optional[str]] = mapped_column(Text)

    # Orden de presentación dentro de la notificación
    sort_order: Mapped[Optional[int]] = mapped_column(Integer)

    # Estado de revisión
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | accepted | rejected | applied | failed

    # Quién revisó y cuándo
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    applied_at:  Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[Optional[str]]    = mapped_column(Text)

    # Relación inversa (opcional, útil en queries)
    notification: Mapped["OdmgrNotification"] = relationship(  # type: ignore[name-defined]
        "OdmgrNotification",
        back_populates="changes",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return (
            f"<OdmgrNotificationChange {self.change_type} "
            f"entity={self.entity_name!r} status={self.status}>"
        )
