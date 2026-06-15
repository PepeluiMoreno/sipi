# models/geografia.py

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sipi_core.modules.actores.administraciones import Administracion
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, Float, ForeignKey, Index

from sipi_core.db.registry import Base
from sipi_core.mixins import UUIDPKMixin, AuditMixin
#from models import Inmueble, FiguraProteccion, Administracion

if TYPE_CHECKING:
    from sipi_core.modules.inmuebles.inmuebles import Inmueble
    from sipi_core.modules.inmuebles.figuras_proteccion import FiguraProteccion
    from sipi_core.modules.actores.administraciones import Administracion
    from sipi_core.modules.actores.privados import Privado
    from sipi_core.modules.actores.tecnicos import Tecnico
    from notarios import Notaria
    from sipi_core.modules.actores.registradores import RegistroPropiedad, ColegioProfesional
    from sipi_core.modules.actores.privados  import AgenciaInmobiliaria
    from sipi_core.modules.entidades_religiosas.entidades_religiosas import Diocesis, EntidadReligiosa
  

class ComunidadAutonoma(UUIDPKMixin, AuditMixin, Base):
    """Comunidad Autónoma de España"""
    __tablename__ = "comunidades_autonomas"

    codigo: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False)
    codigo_ine: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    nombre_oficial: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre_cooficial: Mapped[Optional[str]] = mapped_column(String(100))
    nombre_alternativo: Mapped[Optional[str]] = mapped_column(String(100))
    capital: Mapped[Optional[str]] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


    # Relaciones
    provincias: Mapped[list["Provincia"]] = relationship("Provincia", back_populates="comunidad_autonoma", cascade="all, delete-orphan")
    inmuebles: Mapped[list["Inmueble"]] = relationship("Inmueble", back_populates="comunidad_autonoma")
    figuras_proteccion: Mapped[list["FiguraProteccion"]] = relationship("FiguraProteccion", back_populates="comunidad_autonoma")
    administraciones: Mapped[list["Administracion"]] = relationship("Administracion", back_populates="comunidad_autonoma")

    __table_args__ = (
        Index('ix_ccaa_codigo_ine', 'codigo_ine'),
        Index('ix_ccaa_codigo', 'codigo'),
        Index('ix_ccaa_nombre', 'nombre'),
    )

    def __repr__(self) -> str:
        return f"<ComunidadAutonoma {self.codigo_ine} - {self.nombre_oficial}>"


class Provincia(UUIDPKMixin, AuditMixin, Base):
    """Provincia española"""
    __tablename__ = "provincias"

    codigo: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False)
    codigo_iso: Mapped[str] = mapped_column(String(3), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    nombre_oficial: Mapped[Optional[str]] = mapped_column(String(150))
    nombre_cooficial: Mapped[Optional[str]] = mapped_column(String(100))
    nombre_alternativo: Mapped[Optional[str]] = mapped_column(String(100))
    capital: Mapped[Optional[str]] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    comunidad_autonoma_id: Mapped[str] = mapped_column(String(36), ForeignKey("sipi.comunidades_autonomas.id"), index=True, nullable=False)
  

    # Relaciones
    comunidad_autonoma: Mapped["ComunidadAutonoma"] = relationship("ComunidadAutonoma", back_populates="provincias")
    municipios: Mapped[list["Municipio"]] = relationship("Municipio", back_populates="provincia", cascade="all, delete-orphan")
    inmuebles: Mapped[list["Inmueble"]] = relationship("Inmueble", back_populates="provincia")
    administraciones: Mapped[list["Administracion"]] = relationship("Administracion", back_populates="provincia")

    __table_args__ = (
        Index('ix_provincia_codigo', 'codigo'),
        Index('ix_provincia_nombre', 'nombre'),
        Index('ix_provincia_ccaa', 'comunidad_autonoma_id'),
    )

    def __repr__(self) -> str:
        return f"<Provincia {self.codigo} - {self.nombre}>"


class Municipio(UUIDPKMixin, AuditMixin, Base):
    """Municipio español"""
    __tablename__ = "municipios"

    codigo_ine: Mapped[str] = mapped_column(String(5), unique=True, index=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    nombre_oficial: Mapped[Optional[str]] = mapped_column(String(200))
    nombre_cooficial: Mapped[Optional[str]] = mapped_column(String(100))
    nombre_alternativo: Mapped[Optional[str]] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    provincia_id: Mapped[str] = mapped_column(String(36), ForeignKey("sipi.provincias.id"), index=True, nullable=False)
    comunidad_autonoma_id: Mapped[str] = mapped_column(String(36), ForeignKey("sipi.comunidades_autonomas.id"), index=True, nullable=False)
 
    
    # Relaciones
    provincia: Mapped["Provincia"] = relationship("Provincia", back_populates="municipios")
        
    # Relaciones 1:M con nombres descriptivos específicos
    inmuebles: Mapped[list["Inmueble"]] = relationship("Inmueble", back_populates="municipio")
    administraciones: Mapped[list["Administracion"]] = relationship("Administracion", back_populates="municipio_sede")
    privados: Mapped[list["Privado"]] = relationship("Privado", back_populates="municipio_residencia")
    tecnicos: Mapped[list["Tecnico"]] = relationship("Tecnico", back_populates="municipio_trabajo")
    notarias: Mapped[list["Notaria"]] = relationship("Notaria", back_populates="municipio_ubicacion")
    registros_propiedad: Mapped[list["RegistroPropiedad"]] = relationship("RegistroPropiedad", back_populates="municipio_ubicacion")
    colegios_profesionales: Mapped[list["ColegioProfesional"]] = relationship("ColegioProfesional", back_populates="municipio_sede")
    agencias_inmobiliarias: Mapped[list["AgenciaInmobiliaria"]] = relationship("AgenciaInmobiliaria", back_populates="municipio_oficina")
    diocesis: Mapped[list["Diocesis"]] = relationship("Diocesis", back_populates="municipio_sede")
    entidades_religiosas: Mapped[list["EntidadReligiosa"]] = relationship("EntidadReligiosa", back_populates="municipio_sede")
    entidades_locales_menores: Mapped[list["EntidadLocalMenor"]] = relationship("EntidadLocalMenor", back_populates="municipio")

    __table_args__ = (
        Index('ix_municipio_codigo_ine', 'codigo_ine'),
        Index('ix_municipio_nombre', 'nombre'),
        Index('ix_municipio_provincia', 'provincia_id'),
        Index('ix_municipio_ccaa', 'comunidad_autonoma_id'),
    )


    def __repr__(self) -> str:
        return f"<Municipio {self.codigo_ine} - {self.nombre_oficial}>"


class Toponimo(UUIDPKMixin, AuditMixin, Base):
    """
    Denominación alternativa de cualquier entidad geográfica.

    Almacena nombres en lenguas cooficiales, variantes históricas,
    abreviaciones y aliases de matching, sin límite de longitud.

    Cubre todos los niveles de la jerarquía administrativa:
      nivel='comunidad_autonoma'  → entidad_id apunta a sipi.comunidades_autonomas
      nivel='provincia'           → entidad_id apunta a sipi.provincias
      nivel='municipio'           → entidad_id apunta a sipi.municipios
      nivel='entidad_local_menor' → entidad_id apunta a sipi.entidades_locales_menores

    Se usa discriminador (nivel + entidad_id) en vez de FKs duras para mantener
    una sola tabla polimórfica. La integridad referencial se garantiza a nivel
    de aplicación/ETL.
    """
    __tablename__ = "toponimos"

    nombre: Mapped[str] = mapped_column(String(300), nullable=False)
    idioma: Mapped[Optional[str]] = mapped_column(String(10))
    # Fuente del nombre: 'geonames', 'ine', 'cee', 'manual'…
    fuente: Mapped[Optional[str]] = mapped_column(String(50))
    # Nivel jerárquico de la entidad referenciada:
    #   'comunidad_autonoma' | 'provincia' | 'municipio' | 'entidad_local_menor'
    nivel: Mapped[str] = mapped_column(String(50), nullable=False)
    # UUID de la entidad referenciada (sin FK dura para que sirva a cualquier nivel)
    entidad_id: Mapped[str] = mapped_column(String(36), nullable=False)
    # Cutover (Fase 2): referencia al modelo territorial recursivo unificado.
    # Sustituirá a (nivel, entidad_id), que se deprecan.
    entidad_territorial_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sipi.entidades_territoriales.id", ondelete="SET NULL"), index=True)

    __table_args__ = (
        Index("ix_toponimo_nivel_entidad", "nivel", "entidad_id"),
        Index("ix_toponimo_nombre", "nombre"),
    )

    def __repr__(self) -> str:
        return f"<Toponimo {self.nombre!r} ({self.nivel}/{self.idioma}/{self.fuente})>"


class EntidadLocalMenor(UUIDPKMixin, AuditMixin, Base):
    """
    Entidad local menor sub-municipal: pedanía, aldea, barrio, núcleo rural…
    Fuente: Geonames ES (feature_class=P, feature_code=PPL/PPLA3/PPLX/…)
    """
    __tablename__ = "entidades_locales_menores"

    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    # Tipo Geonames: PPL, PPLA3, PPLX, PPLL, PPLF…
    tipo_geonames: Mapped[Optional[str]] = mapped_column(String(10))
    codigo_geonames: Mapped[Optional[int]] = mapped_column(index=True)
    # Código INE del municipio padre (CPRO+CMUN, 5 dígitos) para referencia
    codigo_ine_municipio: Mapped[Optional[str]] = mapped_column(String(5), index=True)
    latitud: Mapped[Optional[float]] = mapped_column(Float)
    longitud: Mapped[Optional[float]] = mapped_column(Float)
    poblacion: Mapped[Optional[int]] = mapped_column()

    municipio_id: Mapped[Optional[str]] = mapped_column(
        String(36), ForeignKey("sipi.municipios.id"), index=True, nullable=True
    )

    # Relaciones
    municipio: Mapped[Optional["Municipio"]] = relationship("Municipio", back_populates="entidades_locales_menores")

    __table_args__ = (
        Index("ix_entidad_local_nombre", "nombre"),
        Index("ix_entidad_local_municipio", "municipio_id"),
        Index("ix_entidad_local_geonames", "codigo_geonames"),
    )

    def __repr__(self) -> str:
        return f"<EntidadLocalMenor {self.nombre} ({self.tipo_geonames})>"