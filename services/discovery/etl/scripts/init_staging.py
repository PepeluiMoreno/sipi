#!/usr/bin/env python
"""Inicialización idempotente de la BD de SIPI en staging.

Crea esquemas + tablas (create_all desde los modelos, evitando el historial
alembic inconsistente), siembra RBAC/configuración/comunicación, y crea dos
usuarios:
  - superadmin (rol admin) — contraseña de SIPI_SUPERADMIN_PASSWORD o aleatoria.
  - visitante (rol 'consulta', SOLO LECTURA) — para navegar sin romper nada;
    usuario de SIPI_VIEWER_USERNAME (def. 'visitante'), contraseña de
    SIPI_VIEWER_PASSWORD o aleatoria (se imprime una vez).

Re-ejecutable: no recrea ni rota contraseñas existentes salvo que se aporten por env.
"""
from __future__ import annotations
import os
import re
import secrets

import sqlalchemy as sa
from sqlalchemy import select, text
from sqlalchemy.orm import Session

import sipi_core.models  # noqa: F401  (registra todos los modelos en la metadata)


def _sync_url() -> str:
    return re.sub(r"\+\w+", "", os.environ.get("DATABASE_URL", ""))


def main() -> None:
    schemas = (os.getenv("DEFINED_SCHEMAS") or os.getenv("APP_SCHEMA") or "app").split(",")
    engine = sa.create_engine(_sync_url())

    # 1) Esquemas + tablas
    with engine.begin() as conn:
        for s in (x.strip() for x in schemas):
            if s:
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{s}"'))
    from sipi_core.db.metadata import get_combined_metadata
    md = get_combined_metadata()
    md.create_all(engine)
    print(f"[init] create_all: {len(md.tables)} tablas en {schemas}")

    # 2) RBAC + configuración + comunicación
    from sipi_core.modules.acceso.services.seed import seed as seed_acceso
    from sipi_core.modules.configuracion.services.seed import seed as seed_config
    from sipi_core.modules.comunicacion.services.seed import seed as seed_comu
    with Session(engine) as s:
        seed_acceso(s)
        seed_config(s)
        seed_comu(s)
        s.commit()
    print("[init] RBAC/configuración/comunicación sembrados")

    # 3) superadmin (rol admin)
    from sipi_core.modules.usuarios.seed_superadmin import seed_superadmin
    with Session(engine) as s:
        info = seed_superadmin(s)
        print(f"[init] superadmin: {info}")

    # 4) visitante (rol 'consulta', solo lectura)
    from sipi_core.modules.usuarios.users import Usuario, Rol, UsuarioRol
    from sipi_core.modules.usuarios.security import hash_password
    vuser = os.getenv("SIPI_VIEWER_USERNAME", "visitante")
    vpass = os.getenv("SIPI_VIEWER_PASSWORD")
    with Session(engine) as s:
        u = s.execute(select(Usuario).where(Usuario.nombre_usuario == vuser)).scalar_one_or_none()
        creado = u is None
        if u is None:
            u = Usuario(nombre_usuario=vuser, nombre="Visitante (solo lectura)")
            s.add(u)
        generada = None
        nueva = vpass
        if nueva is None and creado:
            nueva = secrets.token_urlsafe(12)
            generada = nueva
        if nueva is not None:
            u.hashed_contrasena = hash_password(nueva)
        u.email_verificado = True
        u.asociacion_id = None
        s.flush()
        rol = s.execute(select(Rol).where(Rol.codigo == "consulta")).scalar_one_or_none()
        if rol is None:
            raise SystemExit("[init] falta el rol 'consulta' (RBAC no sembrado)")
        ya = s.execute(
            select(UsuarioRol).where(UsuarioRol.usuario_id == u.id, UsuarioRol.rol_id == rol.id)
        ).scalar_one_or_none()
        if ya is None:
            s.add(UsuarioRol(usuario_id=u.id, rol_id=rol.id))
        s.commit()
        extra = f" CONTRASEÑA_GENERADA={generada}" if generada else ""
        print(f"[init] visitante: usuario={vuser} creado={creado} rol=consulta{extra}")


if __name__ == "__main__":
    main()
