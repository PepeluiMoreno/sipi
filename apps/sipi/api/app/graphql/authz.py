# app/graphql/authz.py
"""
Autorización RBAC (async) para los resolvers GraphQL.

Comprueba si el usuario del contexto tiene permiso para una transacción, según los
permisos rol→transacción de `modules/acceso`. Audita el intento.

    await exigir(info, db, "hallazgo.verificar")
"""
from __future__ import annotations
from typing import Optional, Set

import strawberry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sipi_core.modules.usuarios.users import Usuario, Rol
from sipi_core.modules.acceso.transaccion import Transaccion
from sipi_core.modules.acceso.funcionalidad import FuncionalidadTransaccion
from sipi_core.modules.acceso.permisos import RolTransaccion, RolFuncionalidad
from sipi_core.modules.acceso.auditoria import AuditoriaAcceso

ROLES_TOTALES = {"admin"}


class PermisoDenegado(Exception):
    def __init__(self, transaccion: str):
        self.transaccion = transaccion
        super().__init__(f"Permiso denegado para la transacción '{transaccion}'")


def usuario_de(info: strawberry.Info) -> Optional[Usuario]:
    ctx = info.context or {}
    return ctx.get("usuario") if isinstance(ctx, dict) else getattr(ctx, "usuario", None)


async def transacciones_de(db: AsyncSession, usuario: Usuario) -> Set[str]:
    """Códigos de transacción permitidos para los roles del usuario."""
    codigos_rol = {(r.codigo or r.id) for r in (usuario.roles or [])}
    if not codigos_rol:
        return set()
    if codigos_rol & ROLES_TOTALES:
        # admin → todas
        res = await db.execute(select(Transaccion.codigo))
        return set(res.scalars())
    rol_ids = [r.id for r in usuario.roles]
    # Vía directa rol→transacción (legacy) ∪ vía permiso rol→funcionalidad→transacción
    res1 = await db.execute(
        select(Transaccion.codigo)
        .join(RolTransaccion, RolTransaccion.transaccion_id == Transaccion.id)
        .where(RolTransaccion.rol_id.in_(rol_ids))
    )
    res2 = await db.execute(
        select(Transaccion.codigo)
        .join(FuncionalidadTransaccion, FuncionalidadTransaccion.transaccion_id == Transaccion.id)
        .join(RolFuncionalidad, RolFuncionalidad.funcionalidad_id == FuncionalidadTransaccion.funcionalidad_id)
        .where(RolFuncionalidad.rol_id.in_(rol_ids))
    )
    return set(res1.scalars()) | set(res2.scalars())


async def puede(db: AsyncSession, usuario: Optional[Usuario], transaccion: str) -> bool:
    if usuario is None:
        return False
    if {(r.codigo or r.id) for r in (usuario.roles or [])} & ROLES_TOTALES:
        return True
    return transaccion in await transacciones_de(db, usuario)


async def exigir(info: strawberry.Info, db: AsyncSession, transaccion: str) -> Usuario:
    """Lanza PermisoDenegado si el usuario del contexto no puede. Audita el intento."""
    usuario = usuario_de(info)
    permitido = await puede(db, usuario, transaccion)
    db.add(AuditoriaAcceso(
        usuario_id=getattr(usuario, "id", None),
        transaccion=transaccion, permitido=permitido,
    ))
    if not permitido:
        raise PermisoDenegado(transaccion)
    return usuario
