# models/expedientes.py
"""
Expediente — ciclo de vida y bitácora del inmueble.

Reconstruye el modelo de ciclo de vida (antes `EventoHistorial` +
`estado_ciclo_vida`, perdido en el refactor de aplanado) y lo unifica con el
flujo de validación del destino de la refactorización: las detecciones
automáticas (discovery/survey) se escriben como `Expediente` en estado
`PROPUESTO`; la ratificación humana (RBAC) lo pasa a `RATIFICADO` y actualiza el
`estado_ciclo_vida` del inmueble. No se usan tablas ad-hoc `portals.detecciones`
para el dominio: el hallazgo vive como Expediente.
"""
from __future__ import annotations
import enum
from datetime import datetime, date
from typing import TYPE_CHECKING, Optional
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, ForeignKey, Date, DateTime, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
import strawberry

from sipi_core.db.registry import Base, APP_SCHEMA
from sipi_core.mixins import UUIDPKMixin, AuditMixin

if TYPE_CHECKING:
    from sipi_core.models.inmuebles import Inmueble
    from sipi_core.models.users import Usuario


@strawberry.enum
class EstadoCicloVida(str, enum.Enum):
    """Estado actual del inmueble en su ciclo de vida."""
    INMATRICULADO = "inmatriculado"
    EN_VENTA = "en_venta"
    VENDIDO = "vendido"
    CAMBIO_DE_USO = "cambio_de_uso"
    REHABILITACION = "rehabilitacion"


@strawberry.enum
class GeoQuality(str, enum.Enum):
    """Calidad/origen de la geolocalización del inmueble."""
    MANUAL = "manual"    # validado por humano
    AUTO = "auto"        # asignado por script
    MISSING = "missing"  # sin coordenadas


@strawberry.enum
class TipoEventoExpediente(str, enum.Enum):
    """Tipo de evento del ciclo de vida detectado o registrado."""
    ALTA_INMATRICULACION = "alta_inmatriculacion"
    PUESTA_EN_VENTA = "puesta_en_venta"
    VENDIDO = "vendido"
    CAMBIO_DE_USO = "cambio_de_uso"
    REHABILITACION = "rehabilitacion"
    REHABILITACION_SUBVENCIONADA = "rehabilitacion_subvencionada"
    DECLARACION_BIC = "declaracion_bic"
    CAMBIO_VISITABILIDAD = "cambio_visitabilidad"


@strawberry.enum
class EstadoExpediente(str, enum.Enum):
    """Estado del flujo de validación del expediente."""
    PROPUESTO = "propuesto"      # detectado automáticamente, pendiente de ratificar
    RATIFICADO = "ratificado"    # validado por un humano (RBAC)
    DESCARTADO = "descartado"    # rechazado en la validación


class Expediente(UUIDPKMixin, AuditMixin, Base):
    """
    Expediente/bitácora: un evento del ciclo de vida de un inmueble con flujo de
    validación. Las detecciones nacen `PROPUESTO`; la ratificación las pasa a
    `RATIFICADO` y actualiza `Inmueble.estado_ciclo_vida`.
    """
    __tablename__ = "expedientes"

    # Inmueble al que concierne. Nullable: una propuesta puede preceder al alta
    # del inmueble confirmado (hallazgo de discovery sobre un anuncio).
    inmueble_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey(f"{APP_SCHEMA}.inmuebles.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
        comment="Inmueble afectado (NULL mientras es solo una propuesta sin inmueble confirmado)",
    )

    tipo_evento: Mapped[TipoEventoExpediente] = mapped_column(
        SQLEnum(
            TipoEventoExpediente,
            name="tipo_evento_expediente",
            values_callable=lambda x: [e.value for e in x],
        ),
        index=True,
        nullable=False,
    )

    estado: Mapped[EstadoExpediente] = mapped_column(
        SQLEnum(
            EstadoExpediente,
            name="estado_expediente",
            values_callable=lambda x: [e.value for e in x],
        ),
        default=EstadoExpediente.PROPUESTO,
        index=True,
        nullable=False,
    )

    titulo: Mapped[Optional[str]] = mapped_column(String(255))
    descripcion: Mapped[Optional[str]] = mapped_column(Text)

    fecha_evento: Mapped[Optional[date]] = mapped_column(
        Date, index=True, comment="Fecha del evento en el mundo real"
    )
    fecha_deteccion: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False,
        comment="Cuándo se detectó/registró el expediente",
    )

    fuente: Mapped[Optional[str]] = mapped_column(
        String(100), index=True,
        comment="Origen: 'manual', 'scraper-idealista', 'scraper-fotocasa', 'BOE'...",
    )
    url_evidencia: Mapped[Optional[str]] = mapped_column(String(500))
    detalles: Mapped[Optional[dict]] = mapped_column(
        JSONB, comment="Datos estructurados específicos del evento"
    )

    # --- Validación (RBAC) ---
    validado_por_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey(f"{APP_SCHEMA}.usuarios.id"), index=True, nullable=True,
    )
    validado_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # --- Relaciones ---
    inmueble: Mapped[Optional["Inmueble"]] = relationship(
        "Inmueble", back_populates="expedientes", foreign_keys=[inmueble_id]
    )
    validado_por: Mapped[Optional["Usuario"]] = relationship(
        "Usuario", foreign_keys=[validado_por_id], viewonly=True
    )

    __table_args__ = (
        Index("ix_expedientes_inmueble_estado", "inmueble_id", "estado"),
        Index("ix_expedientes_tipo_fecha", "tipo_evento", "fecha_evento"),
    )

    @property
    def es_propuesta(self) -> bool:
        return self.estado == EstadoExpediente.PROPUESTO

    def __repr__(self) -> str:
        return f"<Expediente {self.tipo_evento} inmueble={self.inmueble_id} estado={self.estado}>"
