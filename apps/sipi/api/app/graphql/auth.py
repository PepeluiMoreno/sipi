# app/graphql/auth.py
"""
Contexto GraphQL: resuelve el usuario actual a partir de la petición.

NOTA: aún no hay autenticación real (JWT). Como gancho de desarrollo, el usuario
se identifica por cabecera `X-Usuario-Id` (o `Authorization: Bearer <usuario_id>`).
Sustituir por verificación de token real cuando exista login. La lógica de
autorización (RBAC) NO depende de cómo se identifique el usuario.
"""
from __future__ import annotations
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from sipi_core.modules.usuarios.users import Usuario


def _extraer_usuario_id(request: Request) -> Optional[str]:
    uid = request.headers.get("x-usuario-id")
    if uid:
        return uid.strip()
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        return auth[7:].strip() or None
    return None


async def cargar_usuario(usuario_id: Optional[str]) -> Optional[Usuario]:
    if not usuario_id:
        return None
    from app.db.sessions.async_session import async_session_maker
    async with async_session_maker() as db:
        res = await db.execute(
            select(Usuario).options(selectinload(Usuario.roles)).where(Usuario.id == usuario_id)
        )
        return res.scalar_one_or_none()


async def get_context(request: Request) -> Dict[str, Any]:
    usuario = await cargar_usuario(_extraer_usuario_id(request))
    return {"request": request, "usuario": usuario}
