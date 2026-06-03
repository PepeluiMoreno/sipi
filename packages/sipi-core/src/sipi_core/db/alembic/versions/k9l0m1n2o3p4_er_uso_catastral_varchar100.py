"""er_uso_catastral_varchar100

Amplía uso_catastral de varchar(50) a varchar(100) en entidades_religiosas.
El Catastro devuelve descripciones de uso que superan los 50 caracteres.

Revision ID: k9l0m1n2o3p4
Revises: j8k9l0m1n2o3
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision    = 'k9l0m1n2o3p4'
down_revision = 'j8k9l0m1n2o3'
branch_labels = None
depends_on    = None

S = 'sipi'


def upgrade() -> None:
    op.alter_column(
        'entidades_religiosas', 'uso_catastral',
        type_=sa.String(100),
        schema=S,
    )


def downgrade() -> None:
    op.alter_column(
        'entidades_religiosas', 'uso_catastral',
        type_=sa.String(50),
        schema=S,
    )
