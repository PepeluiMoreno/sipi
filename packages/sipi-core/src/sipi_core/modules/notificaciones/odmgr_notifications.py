# models/odmgr_notifications.py
"""
Notificaciones del sistema (actualizaciones de datos, hallazgos de daemons, etc.)

Ciclo de vida:
  pending → el diff está siendo calculado en background
  ready   → diff listo, el administrador puede verla y aplicarla
  applied → los cambios ya fueron aplicados a SIPI
  error   → el cálculo del diff o la aplicación fallaron
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from sqlalchemy import String, Text, Boolean, Integer, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sipi_core.db.registry import Base
from sipi_core.mixins import UUIDPKMixin


class OdmgrNotification(UUIDPKMixin, Base):
    """Notificación de actualización de dataset recibida desde ODMGR."""
    __tablename__ = "odmgr_notifications"

    # Tipo de notificación (genérico para todos los eventos del sistema)
    notification_type: Mapped[str] = mapped_column(
        String(40), nullable=False, default="data_update", index=True
    )  # data_update | search_finding | ...

    # Datos del dataset actualizado (relevante cuando notification_type=data_update)
    resource_id:      Mapped[Optional[str]] = mapped_column(String(36), index=True)
    resource_name:    Mapped[Optional[str]] = mapped_column(String(200))
    dataset_version:  Mapped[Optional[str]] = mapped_column(String(20))
    version_type:     Mapped[Optional[str]] = mapped_column(String(20))  # patch | minor | major
    record_count:     Mapped[Optional[int]] = mapped_column(Integer)
    consumption_mode: Mapped[Optional[str]] = mapped_column(String(20))  # graphql | webhook | both

    # Estado del ciclo de vida
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )  # pending | ready | applied | error

    # Resumen del diff (JSON): {"altas": N, "modificaciones": N, "bajas": N}
    diff_summary: Mapped[Optional[str]] = mapped_column(Text)

    # Error si status=error
    error_message: Mapped[Optional[str]] = mapped_column(Text)

    # Estado de lectura (solo relevante cuando status=ready)
    read:    Mapped[bool]               = mapped_column(Boolean, default=False, nullable=False, index=True)
    read_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Payload completo recibido
    raw_payload: Mapped[Optional[str]] = mapped_column(Text)

    # Timestamps
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
    )
    ready_at:   Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))

    # Soft-delete — se marca al aplicar o descartar la notificación
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True)

    # Cambios individuales
    changes: Mapped[List["OdmgrNotificationChange"]] = relationship(  # type: ignore[name-defined]
        "OdmgrNotificationChange",
        back_populates="notification",
        cascade="all, delete-orphan",
        lazy="noload",
    )

    def __repr__(self) -> str:
        return f"<OdmgrNotification {self.resource_name} v{self.dataset_version} status={self.status}>"
