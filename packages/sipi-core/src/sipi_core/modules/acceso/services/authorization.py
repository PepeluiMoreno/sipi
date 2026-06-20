# modules/acceso/services/authorization.py
"""
Autorización por transacción. API mínima para usar en resolvers/servicios.

    from sipi_core.modules.acceso.services import authorization as authz
    if not authz.puede(session, usuario, "hallazgo.verificar"):
        raise PermisoDenegado("hallazgo.verificar")
"""
from __future__ import annotations
from typing import Iterable, Optional, Set

from sqlalchemy.orm import Session

from sipi_core.modules.usuarios.users import Usuario
from sipi_core.modules.acceso.services.permission_matrix import get_matriz
from sipi_core.modules.acceso.auditoria import AuditoriaAcceso


class PermisoDenegado(Exception):
    def __init__(self, transaccion: str):
        self.transaccion = transaccion
        super().__init__(f"Permiso denegado para la transacción '{transaccion}'")


def _codigos_rol(usuario: Usuario) -> Set[str]:
    return {(r.codigo or r.id) for r in (usuario.roles or [])}


def puede(session: Session, usuario: Optional[Usuario], transaccion: str,
          *, ambito: Optional[str] = None, auditar: bool = False) -> bool:
    """¿El usuario puede ejecutar la transacción? (opcionalmente audita)."""
    permitido = False
    if usuario is not None:
        matriz = get_matriz(session)
        permitido = matriz.permite(_codigos_rol(usuario), transaccion)
    if auditar:
        session.add(AuditoriaAcceso(
            usuario_id=getattr(usuario, "id", None),
            transaccion=transaccion, permitido=permitido, ambito=ambito,
        ))
    return permitido


def exigir(session: Session, usuario: Optional[Usuario], transaccion: str,
           *, ambito: Optional[str] = None) -> None:
    """Lanza PermisoDenegado si no está permitido (y lo audita)."""
    if not puede(session, usuario, transaccion, ambito=ambito, auditar=True):
        raise PermisoDenegado(transaccion)


def transacciones_permitidas(session: Session, usuario: Optional[Usuario]) -> Set[str]:
    if usuario is None:
        return set()
    return get_matriz(session).transacciones_de(_codigos_rol(usuario))
