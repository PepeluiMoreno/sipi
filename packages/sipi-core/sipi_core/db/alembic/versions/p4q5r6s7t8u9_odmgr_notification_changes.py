"""Crea tabla odmgr_notification_changes para diff a nivel de registro

Revision ID: p4q5r6s7t8u9
Revises: o3p4q5r6s7t8
Create Date: 2026-04-09

Cambios:
  - Nueva tabla sipi.odmgr_notification_changes
    Almacena cada cambio individual (alta/baja/modificacion) de una notificación,
    con estado de revisión (pending/accepted/rejected/applied/failed).
"""

from alembic import op
import sqlalchemy as sa

revision      = 'p4q5r6s7t8u9'
down_revision = 'o3p4q5r6s7t8'
branch_labels = None
depends_on    = None

S = 'sipi'


def upgrade():
    op.create_table(
        'odmgr_notification_changes',
        sa.Column('id',              sa.String(36),  nullable=False, primary_key=True),
        sa.Column('notification_id', sa.String(36),  nullable=False),
        sa.Column('change_type',     sa.String(20),  nullable=False),   # alta | baja | modificacion
        sa.Column('entity_id',       sa.String(200), nullable=True),
        sa.Column('entity_name',     sa.String(500), nullable=True),
        sa.Column('field_name',      sa.String(100), nullable=True),
        sa.Column('old_value',       sa.Text,        nullable=True),
        sa.Column('new_value',       sa.Text,        nullable=True),
        sa.Column('raw_record',      sa.Text,        nullable=True),
        sa.Column('sort_order',      sa.Integer,     nullable=True),
        sa.Column('status',          sa.String(20),  nullable=False, server_default='pending'),
        sa.Column('reviewed_at',     sa.DateTime(timezone=True), nullable=True),
        sa.Column('applied_at',      sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message',   sa.Text,        nullable=True),
        sa.ForeignKeyConstraint(
            ['notification_id'], ['sipi.odmgr_notifications.id'],
            ondelete='CASCADE',
        ),
        schema=S,
    )

    op.create_index('ix_odmgr_notification_changes_notification_id',
                    'odmgr_notification_changes', ['notification_id'], schema=S)
    op.create_index('ix_odmgr_notification_changes_change_type',
                    'odmgr_notification_changes', ['change_type'], schema=S)
    op.create_index('ix_odmgr_notification_changes_status',
                    'odmgr_notification_changes', ['status'], schema=S)


def downgrade():
    op.drop_index('ix_odmgr_notification_changes_status',
                  table_name='odmgr_notification_changes', schema=S)
    op.drop_index('ix_odmgr_notification_changes_change_type',
                  table_name='odmgr_notification_changes', schema=S)
    op.drop_index('ix_odmgr_notification_changes_notification_id',
                  table_name='odmgr_notification_changes', schema=S)
    op.drop_table('odmgr_notification_changes', schema=S)
