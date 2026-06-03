
# models/__init__.py
"""
SIPI Database Models

This module provides a unified import interface for all database models,
organized by domain and schema:

- APP Schema: Business domain models (actors, properties, documents, etc.)
- GIS Schema: Geographic and spatial models (administrative divisions, OSM data)
"""

# ============================================================================
# BASE CLASSES (Primero siempre)
# ============================================================================
from sipi_core.db.registry import Base
from sipi_core.mixins import UUIDPKMixin, AuditMixin

# ============================================================================
# USERS (DEBE IR PRIMERO - AuditMixin y muchos otros dependen de esto)
# ============================================================================
from sipi_core.modules.usuarios.users import Usuario, Rol

# ============================================================================
# TYPOLOGIES (APP Schema - Sin dependencias de actores)
# ============================================================================
from sipi_core.modules.catalogos.tipologias import (
    TipoEstadoConservacion, TipoEstadoTratamiento, TipoRolTecnico,
    TipoCertificacionPropiedad, TipoTituloPropiedad, TipoDocumento, 
    TipoInmueble, TipoMimeDocumento, TipoPersona, TipoTransmision, 
    TipoVia, TipoEntidadReligiosa, TipoLicencia, FuenteDocumental, 
    TipoUsoInmueble
)

# ============================================================================
# GEOGRAPHY (APP Schema - Sin dependencias de actores)
# ============================================================================
from sipi_core.modules.geografia.geografia import (
    ComunidadAutonoma, 
    Provincia, 
    Municipio
)

# ============================================================================
# ACTORS BASE (Clases base abstractas sin dependencias)
# ============================================================================
from sipi_core.modules.actores.actores_base import PersonaMixin, TitularBase

# ============================================================================
# ACTORS (APP Schema) - Ordenados por dependencias de Foreign Keys
# ============================================================================

# 1. Notarios (no tienen FK a otros actores)
from sipi_core.modules.actores.notarios import Notaria, NotariaTitular  

# 2. Registradores (no tienen FK a otros actores)
from sipi_core.modules.actores.registradores import RegistroPropiedad, RegistroPropiedadTitular

# 3. Administraciones (tienen updated_by_id -> usuarios.id, ya importado arriba)
from sipi_core.modules.actores.administraciones import Administracion, AdministracionTitular

# 4. Entidades Religiosas (ProvinciaEclesiastica → Diocesis → Parroquia por FKs)
from sipi_core.modules.entidades_religiosas.entidades_religiosas import ProvinciaEclesiastica, Diocesis, DiocesisTitular, Parroquia
from sipi_core.modules.entidades_religiosas.entidades_religiosas import EntidadReligiosa, EntidadReligiosaTitular

# 5. Técnicos (pueden tener FK a tipologías y usuarios)
from sipi_core.modules.actores.tecnicos import Tecnico, ColegioProfesional

# 6. Privados y Agencias (sin dependencias críticas)
from sipi_core.modules.actores.privados import Privado
from sipi_core.modules.actores.agencias import AgenciaInmobiliaria

# 7. Actores de transmisión (Transmitente y Adquiriente — polimórficos)
from sipi_core.modules.actores.actores_transmision import Transmitente, Adquiriente

# ============================================================================
# DOCUMENTS (APP Schema - Depende de actores)
# ============================================================================
from sipi_core.modules.documentos.documentos import (
    Documento, 
    InmuebleDocumento
)

# ============================================================================
# PROPERTIES (APP Schema - Depende de documentos, geografía y actores)
# ============================================================================
from sipi_core.modules.inmuebles.inmuebles import (
    Inmueble, 
    Inmatriculacion, 
    InmuebleDenominacion,
    InmuebleOSMExt, 
    InmuebleWDExt, 
    InmuebleCita, 
    InmuebleUso, 
    InmuebleNivelProteccion
)

# ============================================================================
# HISTORIOGRAPHY (APP Schema)
# ============================================================================
from sipi_core.modules.inmuebles.historiografia import (
    FuenteHistoriografica
)

# ============================================================================
# PROTECTION FIGURES (APP Schema)
# ============================================================================
from sipi_core.modules.inmuebles.figuras_proteccion import (
    FiguraProteccion, 
    NivelProteccion
)

# ============================================================================
# TRANSMISSIONS (APP Schema - Depende de inmuebles y actores)
# ============================================================================
from sipi_core.modules.transmisiones.transmisiones import (
    Transmision, 
    TransmisionAnunciante
)

# ============================================================================
# INTERVENTIONS (APP Schema - Depende de inmuebles y técnicos)
# ============================================================================
from sipi_core.modules.intervenciones.intervenciones import (
    Intervencion, 
    IntervencionTecnico
)

# ============================================================================
# SUBSIDIES (APP Schema - Depende de intervenciones y administraciones)
# ============================================================================
from sipi_core.modules.intervenciones.subvenciones import (
    IntervencionSubvencion, 
    SubvencionAdministracion
)

# ============================================================================
# EXPEDIENTES (APP Schema - ciclo de vida del inmueble + validación)
# ============================================================================
from sipi_core.modules.expedientes.expedientes import (
    Expediente,
    EstadoCicloVida,
    GeoQuality,
    TipoEventoExpediente,
    EstadoExpediente,
)

# ============================================================================
# DISCOVERY (APP Schema)
# ============================================================================
from sipi_core.modules.discovery.discovery import (
    InmuebleRaw,
    DeteccionAnuncio
)

# ============================================================================
# OSM (GIS Schema - could be moved to geografia package)
# ============================================================================
from sipi_core.modules.discovery.osm import (
    OSMPlace
)

# ============================================================================
# ODMGR NOTIFICATIONS (notificaciones de actualización de datasets ODMGR)
# ============================================================================
from sipi_core.modules.notificaciones.odmgr_notifications import OdmgrNotification
from sipi_core.modules.notificaciones.odmgr_notification_changes import OdmgrNotificationChange

# ============================================================================
# EXPORTS
# ============================================================================

__all__ = [
    # Base classes
    'Base',
    'UUIDPKMixin', 'AuditMixin',

    # User
    'Usuario', 'Rol',

    # Typologies
    'TipoEstadoConservacion', 'TipoEstadoTratamiento', 'TipoRolTecnico',
    'TipoCertificacionPropiedad', 'TipoTituloPropiedad', 'TipoDocumento', 
    'TipoInmueble', 'TipoMimeDocumento', 'TipoPersona', 'TipoTransmision', 
    'TipoVia', 'TipoEntidadReligiosa', 'TipoLicencia', 'FuenteDocumental', 
    'TipoUsoInmueble',

    # Geography (GIS Schema)
    'ComunidadAutonoma', 'Provincia', 'Municipio',

    # Actor base classes
    'PersonaMixin', 'TitularBase',
    
    # Notaries
    'Notaria', 'NotariaTitular',
    
    # Property Registrars
    'RegistroPropiedad', 'RegistroPropiedadTitular',
    
    # Public Administrations
    'Administracion', 'AdministracionTitular',
    
    # Religious Entities
    'ProvinciaEclesiastica', 'Diocesis', 'DiocesisTitular', 'Parroquia',
    'EntidadReligiosa', 'EntidadReligiosaTitular',
    
    # Technical Professionals
    'Tecnico', 'ColegioProfesional',
    
    # Private Actors
    'Privado', 'AgenciaInmobiliaria',

    # Transmission Actors
    'Transmitente', 'Adquiriente',
    
    # Documents
    'Documento', 'InmuebleDocumento',
    
    # Properties
    'Inmueble', 'Inmatriculacion', 'InmuebleDenominacion',
    'InmuebleOSMExt', 'InmuebleWDExt', 'InmuebleCita', 'InmuebleUso', 
    'InmuebleNivelProteccion',
    
    # Historiography
    'FuenteHistoriografica',
    
    # Protection Figures
    'FiguraProteccion', 'NivelProteccion',
    
    # Transmissions
    'Transmision', 'TransmisionAnunciante',
    
    # Interventions
    'Intervencion', 'IntervencionTecnico',
    
    # Subsidies
    'IntervencionSubvencion', 'SubvencionAdministracion',
    
    # Expedientes (ciclo de vida)
    'Expediente', 'EstadoCicloVida', 'GeoQuality',
    'TipoEventoExpediente', 'EstadoExpediente',

    # Discovery
    'InmuebleRaw', 'DeteccionAnuncio',
    
    # OSM
    'OSMPlace',

    # ODMGR Notifications
    'OdmgrNotification',
    'OdmgrNotificationChange',
]