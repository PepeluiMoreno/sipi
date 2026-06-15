# modules/acceso/services/seed.py
"""
Seed idempotente del RBAC: sincroniza la BD con `catalog.py`.

Crea/actualiza transacciones y roles base y sus permisos (rol→transacción).
Re-ejecutable sin duplicar. No borra lo que no esté en el catálogo (conservador).
"""
from __future__ import annotations
from typing import Dict

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from sipi_core.modules.usuarios.users import Rol, TipoRol
from sipi_core.modules.acceso.transaccion import Transaccion, TipoTransaccion
from sipi_core.modules.acceso.funcionalidad import Funcionalidad, FuncionalidadTransaccion
from sipi_core.modules.acceso.permisos import RolTransaccion, RolFuncionalidad
from sipi_core.modules.acceso import catalog
from sipi_core.modules.acceso.services.permission_matrix import invalidar_cache


def seed(session: Session) -> Dict[str, int]:
    creadas_tx = creadas_func = creados_ft = creadas_rol = creados_rf = 0

    # 1) Transacciones
    tx_por_codigo: Dict[str, Transaccion] = {
        t.codigo: t for t in session.execute(select(Transaccion)).scalars()
    }
    for d in catalog.TRANSACCIONES:
        tx = tx_por_codigo.get(d.codigo)
        if tx is None:
            tx = Transaccion(codigo=d.codigo, nombre=d.nombre, modulo=d.modulo,
                             tipo=TipoTransaccion(d.tipo), activa=True, sistema=True)
            session.add(tx); tx_por_codigo[d.codigo] = tx; creadas_tx += 1
        else:
            tx.nombre, tx.modulo, tx.tipo = d.nombre, d.modulo, TipoTransaccion(d.tipo)
    session.flush()

    # 2) Funcionalidades (= permisos) + su mapeo fijo a transacciones
    func_por_codigo: Dict[str, Funcionalidad] = {
        f.codigo: f for f in session.execute(select(Funcionalidad)).scalars()
    }
    for d in catalog.FUNCIONALIDADES:
        f = func_por_codigo.get(d.codigo)
        if f is None:
            f = Funcionalidad(codigo=d.codigo, nombre=d.nombre, modulo=d.modulo, orden=d.orden, activa=True)
            session.add(f); func_por_codigo[d.codigo] = f; creadas_func += 1
        else:
            f.nombre, f.modulo, f.orden = d.nombre, d.modulo, d.orden
    session.flush()

    ft_existentes = {
        (ft.funcionalidad_id, ft.transaccion_id)
        for ft in session.execute(select(FuncionalidadTransaccion)).scalars()
    }
    for d in catalog.FUNCIONALIDADES:
        f = func_por_codigo[d.codigo]
        for cod in d.transacciones:
            tx = tx_por_codigo.get(cod)
            if tx is None:
                continue
            if (f.id, tx.id) not in ft_existentes:
                session.add(FuncionalidadTransaccion(funcionalidad_id=f.id, transaccion_id=tx.id))
                ft_existentes.add((f.id, tx.id)); creados_ft += 1
    session.flush()

    # 3) Roles base
    rol_por_codigo: Dict[str, Rol] = {
        (r.codigo or ""): r for r in session.execute(select(Rol)).scalars() if r.codigo
    }
    for d in catalog.ROLES:
        rol = rol_por_codigo.get(d.codigo)
        if rol is None:
            rol = Rol(nombre=d.nombre, codigo=d.codigo, descripcion=d.descripcion,
                      tipo=TipoRol(d.tipo), es_territorial=d.es_territorial,
                      sistema=d.sistema, activo=True)
            session.add(rol); rol_por_codigo[d.codigo] = rol; creadas_rol += 1
        else:
            rol.nombre, rol.descripcion = d.nombre, d.descripcion
            rol.tipo, rol.es_territorial, rol.sistema = TipoRol(d.tipo), d.es_territorial, d.sistema
    session.flush()

    # 4) Permisos rol→funcionalidad (RolFuncionalidad). Los grants directos
    #    rol→transacción (RolTransaccion) quedan obsoletos: se purgan.
    session.execute(delete(RolTransaccion))
    rf_existentes = {
        (rf.rol_id, rf.funcionalidad_id)
        for rf in session.execute(select(RolFuncionalidad)).scalars()
    }
    for d in catalog.ROLES:
        rol = rol_por_codigo[d.codigo]
        codigos = catalog.todas_las_funcionalidades() if d.funcionalidades == ["*"] else d.funcionalidades
        for cod in codigos:
            f = func_por_codigo.get(cod)
            if f is None:
                continue
            if (rol.id, f.id) not in rf_existentes:
                session.add(RolFuncionalidad(rol_id=rol.id, funcionalidad_id=f.id))
                rf_existentes.add((rol.id, f.id)); creados_rf += 1

    session.commit()
    invalidar_cache()
    return {"transacciones": creadas_tx, "funcionalidades": creadas_func,
            "func_transacciones": creados_ft, "roles": creadas_rol, "rol_funcionalidades": creados_rf}


def _build_session():
    """Sesión síncrona desde DATABASE_URL (psycopg2). Para uso por CLI."""
    import os
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    url = os.environ.get("DATABASE_URL")
    if not url:
        raise SystemExit("DATABASE_URL no definida")
    # Forzar driver síncrono (el de la app es asyncpg).
    url = url.replace("+asyncpg", "+psycopg2").replace("postgresql://", "postgresql+psycopg2://")
    return sessionmaker(bind=create_engine(url))()


def main() -> None:
    """Punto de entrada: `python -m sipi_core.modules.acceso.services.seed`.

    Sincroniza la BD con `catalog.py` (idempotente). Importa la fachada de modelos
    para que todos los mappers estén registrados antes de consultar.
    """
    import sipi_core.models  # noqa: F401  (registra todos los modelos/relaciones)

    session = _build_session()
    try:
        resultado = seed(session)
        print(f"Seed RBAC OK → creadas {resultado}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
