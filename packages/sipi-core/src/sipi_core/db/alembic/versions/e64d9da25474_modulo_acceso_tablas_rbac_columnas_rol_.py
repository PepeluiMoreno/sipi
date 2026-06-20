"""modulo acceso: tablas RBAC + columnas rol (aditivo)

Crea las tablas del módulo `acceso` (transacciones, funcionalidades,
funcionalidades_transacciones, roles_transacciones, roles_funcionalidades,
auditoria_acceso) y añade las columnas RBAC aditivas a `roles` (codigo, tipo,
nivel, es_territorial, nivel_territorial, sistema, activo). Esquema B (sipi).

Patrón dinámico ya probado: crea SOLO lo que falta (tablas y columnas del modelo
ausentes en la BD), respetando enums existentes (create_all checkfirst). Aditivo:
columnas nuevas como NULLABLE/con default; no toca datos.

Revision ID: e64d9da25474
Revises: c1f64df9b284
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'e64d9da25474'
down_revision: Union[str, None] = 'c1f64df9b284'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def upgrade() -> None:
    bind = op.get_bind()
    from sipi_core.models import Base
    insp = sa.inspect(bind)
    existing = set(insp.get_table_names(schema=SCHEMA))

    # 1) crear tablas del modelo que faltan (orden de dependencias), enums checkfirst
    to_create = [t for t in Base.metadata.sorted_tables
                 if (t.schema or SCHEMA) == SCHEMA and t.name not in existing]
    if to_create:
        Base.metadata.create_all(bind=bind, tables=to_create, checkfirst=True)

    # 2) columnas del modelo ausentes en tablas existentes (aditivo, nullable)
    insp = sa.inspect(bind)
    for table in Base.metadata.tables.values():
        if (table.schema or SCHEMA) != SCHEMA or table.name not in existing:
            continue
        db_cols = {c["name"] for c in insp.get_columns(table.name, schema=SCHEMA)}
        for col in table.columns:
            if col.name in db_cols:
                continue
            coltype = col.type
            if isinstance(coltype, sa.Enum):
                postgresql.ENUM(*coltype.enums, name=coltype.name).create(bind, checkfirst=True)
                newtype = postgresql.ENUM(name=coltype.name, create_type=False)
            else:
                newtype = coltype.copy() if hasattr(coltype, "copy") else coltype
            server_default = None
            if col.name == "tipo":
                server_default = "funcional"
            elif col.name == "nivel":
                server_default = "0"
            elif col.name in ("es_territorial", "sistema"):
                server_default = sa.text("false")
            elif col.name == "activo":
                server_default = sa.text("true")
            op.add_column(table.name, sa.Column(col.name, newtype, nullable=True,
                                                server_default=server_default), schema=SCHEMA)


def downgrade() -> None:
    for t in ["auditoria_acceso", "roles_funcionalidades", "roles_transacciones",
              "funcionalidades_transacciones", "funcionalidades", "transacciones"]:
        op.execute(f"DROP TABLE IF EXISTS {SCHEMA}.{t} CASCADE")
    for c in ["activo", "sistema", "nivel_territorial", "es_territorial", "nivel", "tipo", "codigo"]:
        op.execute(f"ALTER TABLE {SCHEMA}.roles DROP COLUMN IF EXISTS {c}")
    op.execute("DROP TYPE IF EXISTS tipo_transaccion")
    op.execute("DROP TYPE IF EXISTS tipo_rol")
