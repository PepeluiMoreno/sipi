# models/geografia.py

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from sipi_core.models.administraciones import Administracion
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, ForeignKey, Index
from geoalchemy2 import Geometry

from sipi_core.db.registry import Base
from sipi_core.mixins import UUIDPKMixin, AuditMixin
#from models import Inmueble, FiguraProteccion, Administracion

if TYPE_CHECKING:
    from sipi_core.models.inmuebles import Inmueble
    from sipi_core.models.figuras_proteccion import FiguraProteccion
    from sipi_core.models.administraciones import Administracion
    from sipi_core.models.privados import Privado
    from sipi_core.models.tecnicos import Tecnico
    from notarios import Notaria
    from registradores import RegistroPropiedad, ColegioProfesional
    from sipi_core.models.privados  import AgenciaInmobiliaria
    from sipi_core.models.entidades_religiosas import Diocesis, EntidadReligiosa
  

class ComunidadAutonoma(UUIDPKMixin, AuditMixin, Base):
    """Comunidad Autónoma de España"""
    __tablename__ = "comunidades_autonomas"
 

    codigo_ine: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False)
    nombre_oficial: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    nombre_cooficial: Mapped[Optional[str]] = mapped_column(String(100))
    nombre_alternativo: Mapped[Optional[str]] = mapped_column(String(100))


    # Relaciones
    provincias: Mapped[list["Provincia"]] = relationship("Provincia", back_populates="comunidad_autonoma", cascade="all, delete-orphan")
    inmuebles: Mapped[list["Inmueble"]] = relationship("Inmueble", back_populates="comunidad_autonoma")
    figuras_proteccion: Mapped[list["FiguraProteccion"]] = relationship("FiguraProteccion", back_populates="comunidad_autonoma")
    administraciones: Mapped[list["Administracion"]] = relationship("Administracion", back_populates="comunidad_autonoma")

    __table_args__ = (
        Index('ix_ccaa_codigo_ine', 'codigo_ine'),
        Index('ix_ccaa_nombre', 'nombre_oficial'),
        
    )

    def __repr__(self) -> str:
        return f"<ComunidadAutonoma {self.codigo_ine} - {self.nombre_oficial}>"


class Provincia(UUIDPKMixin, AuditMixin, Base):
    """Provincia española"""
    __tablename__ = "provincias"

    codigo_ine: Mapped[str] = mapped_column(String(2), unique=True, index=True, nullable=False)
    nombre_oficial: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    nombre_cooficial: Mapped[Optional[str]] = mapped_column(String(100))
    nombre_alternativo: Mapped[Optional[str]] = mapped_column(String(100))
    comunidad_autonoma_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.comunidades_autonomas.id"), index=True, nullable=False)
  

    # Relaciones
    comunidad_autonoma: Mapped["ComunidadAutonoma"] = relationship("ComunidadAutonoma", back_populates="provincias")
    municipios: Mapped[list["Municipio"]] = relationship("Municipio", back_populates="provincia", cascade="all, delete-orphan")
    inmuebles: Mapped[list["Inmueble"]] = relationship("Inmueble", back_populates="provincia")
    administraciones: Mapped[list["Administracion"]] = relationship("Administracion", back_populates="provincia")

    __table_args__ = (
        Index('ix_provincia_codigo_ine', 'codigo_ine'),
        Index('ix_provincia_nombre', 'nombre_oficial'),
        Index('ix_provincia_ccaa', 'comunidad_autonoma_id'),
       
     )

    def __repr__(self) -> str:
        return f"<Provincia {self.codigo_ine} - {self.nombre_oficial}>"


class Municipio(UUIDPKMixin, AuditMixin, Base):
    """Municipio español"""
    __tablename__ = "municipios"
    
    codigo_ine: Mapped[str] = mapped_column(String(5), unique=True, index=True, nullable=False)
    codigo_ine_7: Mapped[Optional[str]] = mapped_column(String(7), unique=True, index=True)
    nombre_oficial: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    nombre_cooficial: Mapped[Optional[str]] = mapped_column(String(100))
    nombre_alternativo: Mapped[Optional[str]] = mapped_column(String(100)) 
    provincia_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.provincias.id"), index=True, nullable=False)
 
    
    # Relaciones
    provincia: Mapped["Provincia"] = relationship("Provincia", back_populates="municipios")
        
    # Relaciones 1:M con nombres descriptivos específicos
    inmuebles: Mapped[list["Inmueble"]] = relationship("Inmueble", back_populates="municipio")
    administraciones: Mapped[list["Administracion"]] = relationship("Administracion", back_populates="municipio_sede")
    privados: Mapped[list["Privado"]] = relationship("Privado", back_populates="municipio_residencia")
    entidades_poblacion: Mapped[list["EntidadPoblacion"]] = relationship("EntidadPoblacion", back_populates="municipio", cascade="all, delete-orphan")
    tecnicos: Mapped[list["Tecnico"]] = relationship("Tecnico", back_populates="municipio_trabajo")
    notarias: Mapped[list["Notaria"]] = relationship("Notaria", back_populates="municipio_ubicacion")
    registros_propiedad: Mapped[list["RegistroPropiedad"]] = relationship("RegistroPropiedad", back_populates="municipio_ubicacion")
    colegios_profesionales: Mapped[list["ColegioProfesional"]] = relationship("ColegioProfesional", back_populates="municipio_sede")
    agencias_inmobiliarias: Mapped[list["AgenciaInmobiliaria"]] = relationship("AgenciaInmobiliaria", back_populates="municipio_oficina")
    diocesis: Mapped[list["Diocesis"]] = relationship("Diocesis", back_populates="municipio_sede")
    entidades_religiosas: Mapped[list["EntidadReligiosa"]] = relationship("EntidadReligiosa", back_populates="municipio_sede")
    
    __table_args__ = (
        Index('ix_municipio_codigo_ine', 'codigo_ine'),
        Index('ix_municipio_nombre', 'nombre_oficial'),
        Index('ix_municipio_provincia', 'provincia_id'),
       
     )


    def __repr__(self) -> str:
        return f"<Municipio {self.codigo_ine} - {self.nombre_oficial}>"

class EntidadPoblacion(UUIDPKMixin, AuditMixin, Base):
    """Entidad de población sub-municipal: pedanía, núcleo, EATIM/entidad local
    menor, entidad singular o diseminado.

    Permite localizar inmuebles (ermitas, capillas rurales) con más finura que el
    municipio y afinar el reverse-geocoding de la fusión. Se alimenta del dataset
    Geonames/Entidades Locales de OpenDataManager
    (ver docs/INTEGRACION_OPENDATAMANAGER.md).
    """
    __tablename__ = "entidades_poblacion"

    codigo: Mapped[Optional[str]] = mapped_column(String(20), index=True)  # INE / Geonames
    nombre_oficial: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    nombre_cooficial: Mapped[Optional[str]] = mapped_column(String(150))
    nombre_alternativo: Mapped[Optional[str]] = mapped_column(String(150))
    tipo: Mapped[Optional[str]] = mapped_column(String(30), index=True)  # PEDANIA|NUCLEO|EATIM|ENTIDAD_SINGULAR|DISEMINADO
    municipio_id: Mapped[str] = mapped_column(String(36), ForeignKey("app.municipios.id"), index=True, nullable=False)
    coordenadas: Mapped[Optional[Geometry]] = mapped_column(Geometry(geometry_type="POINT", srid=4326))
    fuente: Mapped[Optional[str]] = mapped_column(String(50))  # GEONAMES|INE|MINHAC_EL

    municipio: Mapped["Municipio"] = relationship("Municipio", back_populates="entidades_poblacion")
    inmuebles: Mapped[list["Inmueble"]] = relationship("Inmueble", back_populates="entidad_poblacion")
