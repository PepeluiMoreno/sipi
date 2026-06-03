"""Añade deleted_at a odmgr_notifications para soft-delete al aplicar/descartar

Revision ID: q5r6s7t8u9v0
Revises: p4q5r6s7t8u9
Create Date: 2026-04-09
"""

from alembic import op
import sqlalchemy as sa

revision      = 'q5r6s7t8u9v0'
down_revision = 'p4q5r6s7t8u9'
branch_labels = None
depends_on    = None

S = 'sipi'


def upgrade():
    op.add_column('odmgr_notifications',
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        schema=S)
    op.create_index('ix_odmgr_notifications_deleted_at',
                    'odmgr_notifications', ['deleted_at'], schema=S)


def downgrade():
    op.drop_index('ix_odmgr_notifications_deleted_at',
                  table_name='odmgr_notifications', schema=S)
    op.drop_column('odmgr_notifications', 'deleted_at', schema=S)
