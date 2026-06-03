# modules/acceso/services/permission_matrix.py
"""
Matriz de permisos en memoria (rol → transacciones), estilo SIGA.

Se construye desde la BD una vez y se cachea; se regenera cuando cambian roles o
permisos. Resuelve la autorización en O(1) sin tocar la BD en cada chequeo.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, FrozenSet, Set, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from sipi_core.modules.usuarios.users import Rol
from sipi_core.modules.acceso.transaccion import Transaccion
from sipi_core.modules.acceso.permisos import RolTransaccion


@dataclass(frozen=True)
class PermissionMatrix:
    """Snapshot inmutable: codigo_rol → {codigos de transacción}."""
    rol_a_transacciones: Dict[str, FrozenSet[str]]
    roles_totales: FrozenSet[str]  # roles con acceso total ("*")

    def permite(self, codigos_rol: Set[str], transaccion: str) -> bool:
        if codigos_rol & self.roles_totales:
            return True
        for r in codigos_rol:
            if transaccion in self.rol_a_transacciones.get(r, frozenset()):
                return True
        return False

    def transacciones_de(self, codigos_rol: Set[str]) -> Set[str]:
        out: Set[str] = set()
        for r in codigos_rol:
            out |= set(self.rol_a_transacciones.get(r, frozenset()))
        return out


def construir_matriz(session: Session) -> PermissionMatrix:
    """Construye la matriz desde la BD (síncrono)."""
    # rol_id -> codigo_rol
    roles = {r.id: r for r in session.execute(select(Rol)).scalars()}
    # transaccion_id -> codigo
    txs = {t.id: t.codigo for t in session.execute(select(Transaccion)).scalars()}

    rol_a_tx: Dict[str, Set[str]] = {}
    for rt in session.execute(select(RolTransaccion)).scalars():
        rol = roles.get(rt.rol_id)
        cod_tx = txs.get(rt.transaccion_id)
        if rol is None or cod_tx is None:
            continue
        rol_a_tx.setdefault(rol.codigo or rol.id, set()).add(cod_tx)

    totales = frozenset(
        (r.codigo or r.id) for r in roles.values()
        if (r.codigo == "admin" or (r.sistema and (r.nivel or 0) >= 100))
    )
    return PermissionMatrix(
        rol_a_transacciones={k: frozenset(v) for k, v in rol_a_tx.items()},
        roles_totales=totales,
    )


# Caché de proceso (regenerable). En producción: invalidar por evento.
_CACHE: Optional[PermissionMatrix] = None


def get_matriz(session: Session, *, refrescar: bool = False) -> PermissionMatrix:
    global _CACHE
    if _CACHE is None or refrescar:
        _CACHE = construir_matriz(session)
    return _CACHE


def invalidar_cache() -> None:
    global _CACHE
    _CACHE = None
