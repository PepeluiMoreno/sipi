# modules/acceso/services/seed.py
"""
Seed idempotente del RBAC: sincroniza la BD con `catalog.py`.

Crea/actualiza transacciones y roles base y sus permisos (rol→transacción).
Re-ejecutable sin duplicar. No borra lo que no esté en el catálogo (conservador).
"""
from __future__ import annotations
from typing import Dict

from sqlalchemy import select
from sqlalchemy.orm import Session

from sipi_core.modules.usuarios.users import Rol, TipoRol
from sipi_core.modules.acceso.transaccion import Transaccion, TipoTransaccion
from sipi_core.modules.acceso.permisos import RolTransaccion
from sipi_core.modules.acceso import catalog
from sipi_core.modules.acceso.services.permission_matrix import invalidar_cache


def seed(session: Session) -> Dict[str, int]:
    creadas_tx = creadas_rol = creados_permisos = 0

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

    # 2) Roles base
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

    # 3) Permisos rol→transacción
    existentes = {
        (rt.rol_id, rt.transaccion_id)
        for rt in session.execute(select(RolTransaccion)).scalars()
    }
    for d in catalog.ROLES:
        rol = rol_por_codigo[d.codigo]
        codigos = catalog.todas_las_transacciones() if d.transacciones == ["*"] else d.transacciones
        for cod in codigos:
            tx = tx_por_codigo.get(cod)
            if tx is None:
                continue
            if (rol.id, tx.id) not in existentes:
                session.add(RolTransaccion(rol_id=rol.id, transaccion_id=tx.id))
                existentes.add((rol.id, tx.id)); creados_permisos += 1

    session.commit()
    invalidar_cache()
    return {"transacciones": creadas_tx, "roles": creadas_rol, "permisos": creados_permisos}
