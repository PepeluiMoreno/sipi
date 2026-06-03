"""fase1: columnas del modelo que faltan en tablas existentes (aditivo, nullable)

Añade las columnas que el modelo sipi-core define y la BD viva no tiene, en las
tablas preexistentes. Se añaden como NULLABLE y SIN constraint FK, para que sea
estrictamente aditivo y no falle con datos existentes (p. ej. toponimos, 47k
filas). La nullabilidad NOT NULL del modelo y las FKs se reconcilian después en
la migración de integridad dedicada (junto con índices y tipos).

Los tipos ENUM se crean con checkfirst (no se recrean si ya existen).

Revision ID: 1c580aa87306
Revises: a25b36811be2
Create Date: 2026-06-03
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '1c580aa87306'
down_revision: Union[str, None] = 'a25b36811be2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = "sipi"


def _added(bind):
    """Devuelve [(tabla, columna_clonada)] para columnas del modelo ausentes en BD."""
    from sipi_core.models import Base
    insp = sa.inspect(bind)
    existing_tables = set(insp.get_table_names(schema=SCHEMA))
    result = []
    for table in Base.metadata.tables.values():
        if (table.schema or SCHEMA) != SCHEMA:
            continue
        if table.name not in existing_tables:
            continue  # tablas nuevas ya se crearon completas en la migración previa
        db_cols = {c["name"] for c in insp.get_columns(table.name, schema=SCHEMA)}
        for col in table.columns:
            if col.name in db_cols:
                continue
            coltype = col.type
            # Asegurar el tipo ENUM en la BD (sin recrearlo si ya existe)
            if isinstance(coltype, sa.Enum):
                postgresql.ENUM(
                    *coltype.enums, name=coltype.name,
                ).create(bind, checkfirst=True)
                newtype = postgresql.ENUM(name=coltype.name, create_type=False)
            else:
                newtype = coltype.copy() if hasattr(coltype, "copy") else coltype
            # Aditivo y seguro: nullable, sin server_default, sin FK
            result.append((table.name, sa.Column(col.name, newtype, nullable=True)))
    return result


def upgrade() -> None:
    bind = op.get_bind()
    for table_name, column in _added(bind):
        op.add_column(table_name, column, schema=SCHEMA)


def downgrade() -> None:
    # Best-effort: no se eliminan columnas en downgrade para no perder datos que
    # se hubieran cargado tras la migración.
    pass
