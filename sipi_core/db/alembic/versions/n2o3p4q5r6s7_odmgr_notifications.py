"""Crea tabla odmgr_notifications para notificaciones de actualización de datasets ODMGR

Revision ID: n2o3p4q5r6s7
Revises: m1n2o3p4q5r6
Create Date: 2026-04-09

Cambios:
  1. Tabla `sipi.odmgr_notifications`
     — almacena webhooks recibidos desde OpenDataManager cuando un dataset
       al que SIPI está suscrito publica una nueva versión.
     — usado por la campanita de notificaciones del panel de administración.
"""

from alembic import op
import sqlalchemy as sa

revision      = 'n2o3p4q5r6s7'
down_revision = 'm1n2o3p4q5r6'
branch_labels = None
depends_on    = None

S = 'sipi'


def upgrade():
    op.create_table(
        'odmgr_notifications',
        sa.Column('id',               sa.String(36),  nullable=False, primary_key=True),
        sa.Column('resource_id',      sa.String(36),  nullable=False),
        sa.Column('resource_name',    sa.String(200), nullable=False),
        sa.Column('dataset_version',  sa.String(20),  nullable=False),
        sa.Column('version_type',     sa.String(20),  nullable=False),
        sa.Column('record_count',     sa.Integer,     nullable=True),
        sa.Column('consumption_mode', sa.String(20),  nullable=True),
        sa.Column('read',             sa.Boolean,     nullable=False, server_default='false'),
        sa.Column('read_at',          sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_payload',      sa.Text,        nullable=True),
        sa.Column('received_at',      sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.text('now()')),
        schema=S,
    )
    op.create_index('ix_odmgr_notifications_resource_id', 'odmgr_notifications',
                    ['resource_id'], schema=S)
    op.create_index('ix_odmgr_notifications_read',        'odmgr_notifications',
                    ['read'], schema=S)
    op.create_index('ix_odmgr_notifications_received_at', 'odmgr_notifications',
                    ['received_at'], schema=S)


def downgrade():
    op.drop_index('ix_odmgr_notifications_received_at', table_name='odmgr_notifications', schema=S)
    op.drop_index('ix_odmgr_notifications_read',        table_name='odmgr_notifications', schema=S)
    op.drop_index('ix_odmgr_notifications_resource_id', table_name='odmgr_notifications', schema=S)
    op.drop_table('odmgr_notifications', schema=S)
