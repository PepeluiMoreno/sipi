# app/graphql/auth.py
"""
Contexto GraphQL: resuelve el usuario actual a partir de la petición.

El usuario se identifica por un **JWT** firmado (`Authorization: Bearer <token>`),
emitido por la mutation `login` y verificado aquí (firma + expiración). El `sub`
del token es el id de usuario. La autorización (RBAC) opera sobre ese usuario.

Escape de desarrollo: con `SIPI_DEV_AUTH=1` se admite la cabecera `X-Usuario-Id`
(sin verificación) para pruebas locales. Desactivado por defecto.
"""
from __future__ import annotations
import os
from typing import Any, Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from starlette.requests import Request

from sipi_core.modules.usuarios.users import Usuario
from sipi_core.modules.usuarios.security import decode_access_token, get_jwt_secret


def _extraer_usuario_id(request: Request) -> Optional[str]:
    auth = request.headers.get("authorization", "")
    if auth.lower().startswith("bearer "):
        token = auth[7:].strip()
        payload = decode_access_token(token, get_jwt_secret()) if token else None
        return payload.get("sub") if payload else None
    # Escape de desarrollo (no usar en producción)
    if os.getenv("SIPI_DEV_AUTH") == "1":
        uid = request.headers.get("x-usuario-id")
        if uid:
            return uid.strip()
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
