# modules/acceso/catalog.py
"""
Catálogo declarativo de transacciones y roles base de SIPI.

Es la **fuente de verdad** del RBAC: el seed (`services/seed.py`) sincroniza la BD
con estas definiciones de forma idempotente. Las transacciones son acciones
atómicas autorizables; los roles base agrupan transacciones por perfil de uso.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class TransaccionDef:
    codigo: str
    nombre: str
    modulo: str
    tipo: str = "operacion"   # consulta | operacion | admin


@dataclass(frozen=True)
class RolDef:
    codigo: str
    nombre: str
    tipo: str                  # sistema | funcional | territorial
    transacciones: List[str]   # códigos de transacción (o "*" = todas)
    descripcion: str = ""
    es_territorial: bool = False
    sistema: bool = False


# --- Transacciones por módulo --------------------------------------------------
TRANSACCIONES: List[TransaccionDef] = [
    # Inmuebles
    TransaccionDef("inmueble.consultar", "Consultar inmuebles", "inmueble", "consulta"),
    TransaccionDef("inmueble.crear", "Crear inmueble", "inmueble"),
    TransaccionDef("inmueble.editar", "Editar inmueble", "inmueble"),
    TransaccionDef("inmueble.geolocalizar", "Geolocalizar inmueble (manual)", "inmueble"),
    # Expedientes (ciclo de vida)
    TransaccionDef("expediente.consultar", "Consultar expedientes", "expediente", "consulta"),
    TransaccionDef("expediente.ratificar", "Ratificar hallazgo (expediente)", "expediente"),
    TransaccionDef("expediente.descartar", "Descartar hallazgo (expediente)", "expediente"),
    # Entidades religiosas
    TransaccionDef("entidad_religiosa.consultar", "Consultar entidades religiosas", "entidad_religiosa", "consulta"),
    TransaccionDef("entidad_religiosa.editar", "Editar entidad religiosa", "entidad_religiosa"),
    # Vigilancia (apps/sipi-survey)
    TransaccionDef("vigilancia.consultar", "Consultar dispositivos de vigilancia", "vigilancia", "consulta"),
    TransaccionDef("vigilancia.dispositivo.crear", "Crear dispositivo de vigilancia", "vigilancia"),
    TransaccionDef("vigilancia.dispositivo.activar", "Activar/pausar dispositivo", "vigilancia"),
    TransaccionDef("vigilancia.ejecutar", "Lanzar extracción/scoring", "vigilancia"),
    # Configuración
    TransaccionDef("config.consultar", "Consultar configuración", "configuracion", "consulta"),
    TransaccionDef("config.editar", "Editar parámetros", "configuracion", "admin"),
    # Acceso (administración)
    TransaccionDef("acceso.consultar", "Consultar usuarios/roles", "acceso", "consulta"),
    TransaccionDef("acceso.administrar", "Administrar usuarios/roles/permisos", "acceso", "admin"),
]

# --- Roles base ----------------------------------------------------------------
ROLES: List[RolDef] = [
    RolDef("admin", "Administrador", "sistema", ["*"],
           "Acceso total al sistema", sistema=True),
    RolDef("catalogador", "Catalogador", "funcional",
           ["inmueble.consultar", "inmueble.crear", "inmueble.editar", "inmueble.geolocalizar",
            "entidad_religiosa.consultar", "entidad_religiosa.editar", "expediente.consultar"],
           "Mantenimiento de inmuebles y entidades"),
    RolDef("validador", "Validador de hallazgos", "territorial",
           ["expediente.consultar", "expediente.ratificar", "expediente.descartar",
            "inmueble.consultar"],
           "Valida/ratifica hallazgos en su ámbito", es_territorial=True),
    RolDef("operador_vigilancia", "Operador de vigilancia", "funcional",
           ["vigilancia.consultar", "vigilancia.dispositivo.crear", "vigilancia.dispositivo.activar",
            "vigilancia.ejecutar", "config.consultar"],
           "Establece y controla los dispositivos de vigilancia (apps/sipi-survey)"),
    RolDef("consulta", "Consulta", "funcional",
           ["inmueble.consultar", "expediente.consultar", "entidad_religiosa.consultar",
            "vigilancia.consultar", "config.consultar"],
           "Solo lectura"),
]


def todas_las_transacciones() -> List[str]:
    return [t.codigo for t in TRANSACCIONES]
