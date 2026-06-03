"""Añadir agencia_inmobiliaria_id directo a transmisiones

Revision ID: c3d4e5f6a7b8
Revises: f3e9a1b7c2d8
Create Date: 2026-03-18

Añade FK directa app.transmisiones → app.agencias_inmobiliarias para
asociar rápidamente la agencia anunciante principal sin pasar por
la tabla de unión transmision_anunciantes.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'f3e9a1b7c2d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

SCHEMA = 'app'


def upgrade() -> None:
    op.add_column('transmisiones',
        sa.Column('agencia_inmobiliaria_id', sa.String(36), nullable=True),
        schema=SCHEMA,
    )
    op.create_index(
        'ix_transmisiones_agencia_inmobiliaria_id',
        'transmisiones', ['agencia_inmobiliaria_id'],
        schema=SCHEMA,
    )
    op.create_foreign_key(
        'fk_transmisiones_agencia_inmobiliaria',
        'transmisiones', 'agencias_inmobiliarias',
        ['agencia_inmobiliaria_id'], ['id'],
        source_schema=SCHEMA, referent_schema=SCHEMA,
    )


def downgrade() -> None:
    op.drop_constraint('fk_transmisiones_agencia_inmobiliaria', 'transmisiones', schema=SCHEMA, type_='foreignkey')
    op.drop_index('ix_transmisiones_agencia_inmobiliaria_id', table_name='transmisiones', schema=SCHEMA)
    op.drop_column('transmisiones', 'agencia_inmobiliaria_id', schema=SCHEMA)
