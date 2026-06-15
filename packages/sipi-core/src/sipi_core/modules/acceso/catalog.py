# modules/acceso/catalog.py
"""
Catálogo declarativo del RBAC de SIPI — **fuente de verdad**, versionada con el código.

Tres niveles, todos FIJOS (no editables por el usuario):
  - **Transacción**: acción atómica autorizable, atada a una operación del código
    (un resolver hace `exigir(info, db, "administracion.crear")`).
  - **Funcionalidad** (= "permiso"): paquete con nombre de transacciones. El mapeo
    funcionalidad→transacciones es declarativo aquí.
  - **Rol** base: concede funcionalidades (no transacciones sueltas).

Lo único editable en runtime: qué funcionalidades tiene cada rol (RolFuncionalidad)
y qué roles tiene cada usuario. El seed (`services/seed.py`) sincroniza la BD con esto.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class TransaccionDef:
    codigo: str
    nombre: str
    modulo: str
    tipo: str = "operacion"   # consulta | operacion | admin


@dataclass(frozen=True)
class FuncionalidadDef:
    codigo: str
    nombre: str
    modulo: str
    transacciones: List[str]
    orden: int = 0


@dataclass(frozen=True)
class RolDef:
    codigo: str
    nombre: str
    tipo: str                   # sistema | funcional | territorial
    funcionalidades: List[str]  # códigos de funcionalidad (o "*" = todas)
    descripcion: str = ""
    es_territorial: bool = False
    sistema: bool = False


# --- Áreas con CRUD completo (consultar/crear/editar/borrar) -------------------
_AREAS_CRUD = [
    ("inmueble", "inmuebles"),
    ("entidad_religiosa", "entidades religiosas"),
    ("administracion", "administraciones"),
    ("notaria", "notarías"),
    ("registro", "registros de la propiedad"),
    ("agente", "otros agentes (agencias, colegios, técnicos, privados)"),
    ("documento", "documentos"),
    ("transmision", "transmisiones"),
    ("intervencion", "intervenciones"),
]
_ACCIONES = [("consultar", "Consultar", "consulta"), ("crear", "Crear", "operacion"),
             ("editar", "Editar", "operacion"), ("borrar", "Borrar", "operacion")]


def _crud(modulo: str, etiqueta: str) -> List[TransaccionDef]:
    return [TransaccionDef(f"{modulo}.{a}", f"{verb} {etiqueta}", modulo, tipo)
            for a, verb, tipo in _ACCIONES]


# --- Transacciones especiales (no encajan en CRUD genérico) --------------------
_ESPECIALES: List[TransaccionDef] = [
    TransaccionDef("inmueble.geolocalizar", "Geolocalizar inmueble (manual)", "inmueble"),
    # Hallazgos (datos de watchers, comprobación humana)
    TransaccionDef("hallazgo.consultar", "Consultar hallazgos", "hallazgo", "consulta"),
    TransaccionDef("hallazgo.verificar", "Verificar hallazgo (→ abre/engrosa expediente)", "hallazgo"),
    TransaccionDef("hallazgo.descartar", "Descartar hallazgo", "hallazgo"),
    # Expedientes (dosier)
    TransaccionDef("expediente.consultar", "Consultar expedientes", "expediente", "consulta"),
    # Catálogos / tipologías y geografía (datos maestros)
    TransaccionDef("catalogo.consultar", "Consultar catálogos/tipologías", "catalogo", "consulta"),
    TransaccionDef("catalogo.editar", "Editar catálogos/tipologías", "catalogo", "admin"),
    TransaccionDef("geografia.consultar", "Consultar geografía", "geografia", "consulta"),
    TransaccionDef("geografia.editar", "Editar geografía", "geografia", "admin"),
    # Vigilancia (apps/sipi-survey)
    TransaccionDef("vigilancia.consultar", "Consultar dispositivos de vigilancia", "vigilancia", "consulta"),
    TransaccionDef("vigilancia.dispositivo.crear", "Crear dispositivo de vigilancia", "vigilancia"),
    TransaccionDef("vigilancia.dispositivo.activar", "Activar/pausar dispositivo", "vigilancia"),
    TransaccionDef("vigilancia.ejecutar", "Lanzar extracción/scoring", "vigilancia"),
    # Configuración
    TransaccionDef("config.consultar", "Consultar configuración", "configuracion", "consulta"),
    TransaccionDef("config.editar", "Editar parámetros", "configuracion", "admin"),
    # Acceso (administración de usuarios/roles/asociaciones)
    TransaccionDef("acceso.consultar", "Consultar usuarios/roles", "acceso", "consulta"),
    TransaccionDef("acceso.administrar", "Administrar usuarios/roles/permisos/asociaciones", "acceso", "admin"),
]

TRANSACCIONES: List[TransaccionDef] = (
    [t for modulo, etiqueta in _AREAS_CRUD for t in _crud(modulo, etiqueta)] + _ESPECIALES
)


# --- Funcionalidades (= permisos): paquetes de transacciones -------------------
def _consulta(modulos: List[str]) -> List[str]:
    return [f"{m}.consultar" for m in modulos]


def _gestion(modulos: List[str], extra=()) -> List[str]:
    return [f"{m}.{a}" for m in modulos for a in ("crear", "editar", "borrar")] + list(extra)


FUNCIONALIDADES: List[FuncionalidadDef] = [
    FuncionalidadDef("inmuebles.consulta", "Consultar inmuebles", "inmueble", _consulta(["inmueble"]), 10),
    FuncionalidadDef("inmuebles.gestion", "Gestionar inmuebles", "inmueble",
                     _gestion(["inmueble"], ["inmueble.geolocalizar"]), 11),
    FuncionalidadDef("hallazgos", "Comprobar hallazgos", "hallazgo",
                     ["hallazgo.consultar", "hallazgo.verificar", "hallazgo.descartar"], 20),
    FuncionalidadDef("expedientes.consulta", "Consultar expedientes", "expediente", ["expediente.consultar"], 30),
    FuncionalidadDef("entidades_religiosas.consulta", "Consultar entidades religiosas", "entidad_religiosa",
                     _consulta(["entidad_religiosa"]), 40),
    FuncionalidadDef("entidades_religiosas.gestion", "Gestionar entidades religiosas", "entidad_religiosa",
                     _gestion(["entidad_religiosa"]), 41),
    FuncionalidadDef("agentes.consulta", "Consultar agentes", "agente",
                     _consulta(["administracion", "notaria", "registro", "agente"]), 50),
    FuncionalidadDef("agentes.gestion", "Gestionar agentes", "agente",
                     _gestion(["administracion", "notaria", "registro", "agente"]), 51),
    FuncionalidadDef("documentos.consulta", "Consultar documentos", "documento", _consulta(["documento"]), 60),
    FuncionalidadDef("documentos.gestion", "Gestionar documentos", "documento", _gestion(["documento"]), 61),
    FuncionalidadDef("transmisiones.consulta", "Consultar transmisiones", "transmision", _consulta(["transmision"]), 70),
    FuncionalidadDef("transmisiones.gestion", "Gestionar transmisiones", "transmision", _gestion(["transmision"]), 71),
    FuncionalidadDef("intervenciones.consulta", "Consultar intervenciones", "intervencion", _consulta(["intervencion"]), 80),
    FuncionalidadDef("intervenciones.gestion", "Gestionar intervenciones", "intervencion", _gestion(["intervencion"]), 81),
    FuncionalidadDef("catalogos.consulta", "Consultar catálogos y geografía", "catalogo",
                     ["catalogo.consultar", "geografia.consultar"], 90),
    FuncionalidadDef("catalogos.gestion", "Editar catálogos y geografía", "catalogo",
                     ["catalogo.editar", "geografia.editar"], 91),
    FuncionalidadDef("vigilancia", "Operar vigilancia", "vigilancia",
                     ["vigilancia.consultar", "vigilancia.dispositivo.crear",
                      "vigilancia.dispositivo.activar", "vigilancia.ejecutar"], 100),
    FuncionalidadDef("configuracion.consulta", "Consultar configuración", "configuracion", ["config.consultar"], 110),
    FuncionalidadDef("configuracion.gestion", "Editar configuración", "configuracion", ["config.editar"], 111),
    FuncionalidadDef("acceso.administracion", "Administrar acceso (usuarios/roles/asociaciones)", "acceso",
                     ["acceso.consultar", "acceso.administrar"], 120),
]


# --- Roles base: conceden funcionalidades --------------------------------------
ROLES: List[RolDef] = [
    RolDef("admin", "Administrador", "sistema", ["*"], "Acceso total al sistema", sistema=True),
    RolDef("catalogador", "Catalogador", "funcional",
           ["inmuebles.consulta", "inmuebles.gestion", "entidades_religiosas.consulta", "entidades_religiosas.gestion",
            "agentes.consulta", "agentes.gestion", "documentos.consulta", "documentos.gestion",
            "transmisiones.consulta", "transmisiones.gestion", "intervenciones.consulta", "intervenciones.gestion",
            "catalogos.consulta", "catalogos.gestion", "expedientes.consulta"],
           "Mantenimiento de inmuebles, agentes, entidades y catálogos"),
    RolDef("validador", "Validador de hallazgos", "territorial",
           ["hallazgos", "expedientes.consulta", "inmuebles.consulta"],
           "Comprueba hallazgos en su ámbito; al verificarlos abre/engrosa expedientes",
           es_territorial=True),
    RolDef("operador_vigilancia", "Operador de vigilancia", "funcional",
           ["vigilancia", "configuracion.consulta"],
           "Establece y controla los dispositivos de vigilancia (apps/sipi-survey)"),
    RolDef("consulta", "Consulta", "funcional",
           ["inmuebles.consulta", "expedientes.consulta", "entidades_religiosas.consulta",
            "agentes.consulta", "documentos.consulta", "transmisiones.consulta",
            "intervenciones.consulta", "catalogos.consulta", "configuracion.consulta"],
           "Solo lectura"),
]


def todas_las_transacciones() -> List[str]:
    return [t.codigo for t in TRANSACCIONES]


def todas_las_funcionalidades() -> List[str]:
    return [f.codigo for f in FUNCIONALIDADES]
