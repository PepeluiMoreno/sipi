"""Añade notification_type, status, diff_summary, error_message y ready_at a odmgr_notifications

Revision ID: o3p4q5r6s7t8
Revises: n2o3p4q5r6s7
Create Date: 2026-04-09

Cambios:
  - notification_type VARCHAR(40) NOT NULL DEFAULT 'data_update'
  - status VARCHAR(20) NOT NULL DEFAULT 'ready'  (las existentes se marcan ready)
  - diff_summary TEXT (JSON con altas/modificaciones/bajas)
  - error_message TEXT
  - ready_at TIMESTAMPTZ
  - resource_id, resource_name, dataset_version, version_type → nullable
    (para acomodar otros tipos de notificación sin estos campos)
"""

from alembic import op
import sqlalchemy as sa

revision      = 'o3p4q5r6s7t8'
down_revision = 'n2o3p4q5r6s7'
branch_labels = None
depends_on    = None

S = 'sipi'


def upgrade():
    op.add_column('odmgr_notifications',
        sa.Column('notification_type', sa.String(40), nullable=False, server_default='data_update'),
        schema=S)
    op.add_column('odmgr_notifications',
        sa.Column('status', sa.String(20), nullable=False, server_default='ready'),
        schema=S)
    op.add_column('odmgr_notifications',
        sa.Column('diff_summary', sa.Text, nullable=True),
        schema=S)
    op.add_column('odmgr_notifications',
        sa.Column('error_message', sa.Text, nullable=True),
        schema=S)
    op.add_column('odmgr_notifications',
        sa.Column('ready_at', sa.DateTime(timezone=True), nullable=True),
        schema=S)

    # Hacer nullable las columnas específicas de data_update
    op.alter_column('odmgr_notifications', 'resource_id',   nullable=True, schema=S)
    op.alter_column('odmgr_notifications', 'resource_name', nullable=True, schema=S)
    op.alter_column('odmgr_notifications', 'dataset_version', nullable=True, schema=S)
    op.alter_column('odmgr_notifications', 'version_type', nullable=True, schema=S)

    op.create_index('ix_odmgr_notifications_status',            'odmgr_notifications', ['status'],            schema=S)
    op.create_index('ix_odmgr_notifications_notification_type', 'odmgr_notifications', ['notification_type'], schema=S)


def downgrade():
    op.drop_index('ix_odmgr_notifications_notification_type', table_name='odmgr_notifications', schema=S)
    op.drop_index('ix_odmgr_notifications_status',            table_name='odmgr_notifications', schema=S)
    op.alter_column('odmgr_notifications', 'version_type',     nullable=False, schema=S)
    op.alter_column('odmgr_notifications', 'dataset_version',  nullable=False, schema=S)
    op.alter_column('odmgr_notifications', 'resource_name',    nullable=False, schema=S)
    op.alter_column('odmgr_notifications', 'resource_id',      nullable=False, schema=S)
    op.drop_column('odmgr_notifications', 'ready_at',          schema=S)
    op.drop_column('odmgr_notifications', 'error_message',     schema=S)
    op.drop_column('odmgr_notifications', 'diff_summary',      schema=S)
    op.drop_column('odmgr_notifications', 'status',            schema=S)
    op.drop_column('odmgr_notifications', 'notification_type', schema=S)
