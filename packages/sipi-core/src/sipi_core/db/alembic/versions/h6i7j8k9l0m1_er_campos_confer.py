"""er_campos_confer

Añade campos de enriquecimiento CONFER a entidades_religiosas:
  - nombre_confer   (nombre oficial en el directorio CONFER)
  - afiliada_confer (boolean: True si figura en CONFER)

Revision ID: h6i7j8k9l0m1
Revises: g5h6i7j8k9l0
Create Date: 2026-03-22
"""

from alembic import op
import sqlalchemy as sa

revision    = 'h6i7j8k9l0m1'
down_revision = 'g5h6i7j8k9l0'
branch_labels = None
depends_on    = None

S = 'sipi'


def _col_exists(table: str, col: str) -> bool:
    conn = op.get_bind()
    r = conn.execute(sa.text(
        "SELECT 1 FROM information_schema.columns "
        "WHERE table_schema=:s AND table_name=:t AND column_name=:c"
    ), {"s": S, "t": table, "c": col}).fetchone()
    return r is not None


def upgrade() -> None:
    t = 'entidades_religiosas'
    nuevas = [
        ('nombre_confer',   sa.String(255)),
        ('afiliada_confer', sa.Boolean()),
    ]
    for col, typ in nuevas:
        if not _col_exists(t, col):
            op.add_column(t, sa.Column(col, typ, nullable=True), schema=S)


def downgrade() -> None:
    t = 'entidades_religiosas'
    for col in ('nombre_confer', 'afiliada_confer'):
        try:
            op.drop_column(t, col, schema=S)
        except Exception:
            pass
