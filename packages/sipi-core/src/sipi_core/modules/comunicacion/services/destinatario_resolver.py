# modules/comunicacion/services/destinatario_resolver.py
"""
Resuelve destinatarios (usuarios) por rol y, opcionalmente, ámbito territorial.
Se apoya en el módulo `acceso` (roles). El ámbito territorial es fase 2.
"""
from __future__ import annotations
from typing import List, Optional, Iterable

from sqlalchemy import select
from sqlalchemy.orm import Session

from sipi_core.modules.usuarios.users import Usuario, Rol


def usuarios_por_rol(session: Session, codigos_rol: Iterable[str],
                     *, ambito: Optional[str] = None) -> List[Usuario]:
    """Usuarios activos que tienen alguno de los roles indicados (por código).

    `ambito` (p. ej. provincia_id) se reservará para roles territoriales (fase 2):
    de momento no filtra por territorio.
    """
    codigos = set(codigos_rol)
    if not codigos:
        return []
    roles = session.execute(
        select(Rol).where(Rol.codigo.in_(codigos))
    ).scalars().all()
    destinatarios = {}
    for rol in roles:
        for u in rol.usuarios:
            destinatarios[u.id] = u
    return list(destinatarios.values())
