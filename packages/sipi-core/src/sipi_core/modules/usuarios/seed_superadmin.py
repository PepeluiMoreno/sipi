"""Seed idempotente del superadministrador.

La contraseña **nunca** se codifica en el repo: se lee de `SIPI_SUPERADMIN_PASSWORD`.
Si no está, se **genera una aleatoria** y se imprime una sola vez (guárdala/cámbiala).
En la BD solo se almacena el hash (PBKDF2). El superadmin no pertenece a ninguna
asociación (`asociacion_id` NULL), es `is_sistema` y recibe el rol `admin` (acceso total).

CLI:  python -m sipi_core.modules.usuarios.seed_superadmin
"""
from __future__ import annotations

import os
import secrets
from typing import Dict, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from sipi_core.modules.usuarios.users import Usuario, Rol, UsuarioRol
from sipi_core.modules.usuarios.security import hash_password

DEFAULT_USERNAME = "superadmin"


def seed_superadmin(session: Session, *, username: Optional[str] = None,
                    password: Optional[str] = None) -> Dict[str, Optional[str]]:
    """Crea o actualiza el superadmin. Devuelve la contraseña SOLO si se generó."""
    username = username or os.getenv("SIPI_SUPERADMIN_USERNAME") or DEFAULT_USERNAME
    explicit = password or os.getenv("SIPI_SUPERADMIN_PASSWORD")

    u = session.execute(
        select(Usuario).where(Usuario.nombre_usuario == username)
    ).scalar_one_or_none()
    creado = u is None
    if u is None:
        u = Usuario(nombre_usuario=username, nombre="Super administrador")
        session.add(u)

    # Solo fija la contraseña al crear o si se aporta explícitamente (env/arg).
    # Si ya existe y no se da contraseña, NO la rota (re-ejecución segura).
    generada: Optional[str] = None
    nueva = explicit
    if nueva is None and creado:
        nueva = secrets.token_urlsafe(18)
        generada = nueva
    if nueva is not None:
        u.hashed_contrasena = hash_password(nueva)

    u.is_sistema = True
    u.asociacion_id = None
    u.email_verificado = True
    session.flush()

    # Rol admin (acceso total). El seed RBAC debe haberlo creado antes.
    rol_admin = session.execute(select(Rol).where(Rol.codigo == "admin")).scalar_one_or_none()
    if rol_admin is None:
        raise RuntimeError("No existe el rol 'admin'; ejecuta antes el seed RBAC "
                           "(python -m sipi_core.modules.acceso.services.seed)")
    ya = session.execute(
        select(UsuarioRol).where(UsuarioRol.usuario_id == u.id, UsuarioRol.rol_id == rol_admin.id)
    ).scalar_one_or_none()
    if ya is None:
        session.add(UsuarioRol(usuario_id=u.id, rol_id=rol_admin.id))

    session.commit()
    return {"username": username, "creado": str(creado),
            "password_generada": password if generada else None}


def main() -> None:
    import sipi_core.models  # noqa: F401  (registra todos los mappers)
    from sipi_core.modules.acceso.services.seed import _build_session

    session = _build_session()
    try:
        res = seed_superadmin(session)
        accion = "creado" if res["creado"] == "True" else "actualizado"
        print(f"Superadmin {accion}: usuario '{res['username']}'")
        if res["password_generada"]:
            print("=" * 60)
            print(f"  CONTRASEÑA GENERADA (guárdala, no se vuelve a mostrar):")
            print(f"  {res['password_generada']}")
            print("=" * 60)
        elif os.getenv("SIPI_SUPERADMIN_PASSWORD"):
            print("  Contraseña tomada de SIPI_SUPERADMIN_PASSWORD.")
        else:
            print("  Contraseña existente sin cambios.")
    finally:
        session.close()


if __name__ == "__main__":
    main()
