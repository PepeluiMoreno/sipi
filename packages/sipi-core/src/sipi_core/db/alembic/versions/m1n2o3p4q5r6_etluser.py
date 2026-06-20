"""Añade is_sistema a usuarios y crea etluser + testuser

Revision ID: m1n2o3p4q5r6
Revises: l0m1n2o3p4q5
Create Date: 2026-03-23

Cambios:
  1. Columna `is_sistema` BOOLEAN NOT NULL DEFAULT FALSE en sipi.usuarios
     — marca usuarios de sistema que no pueden borrarse.
  2. Seed de dos usuarios de sistema con UUID fijo:
       00000000-0000-0000-0000-000000000001  etluser
         Autor de todos los registros creados por pipelines ETL.
       00000000-0000-0000-0000-000000000002  testuser
         Autor de operaciones interactivas mientras la gestión de
         usuarios (post-MVP) no esté implementada.
  Ambos tienen hashed_contrasena = '!' (contraseña imposible).
"""

from alembic import op
import sqlalchemy as sa

revision      = 'm1n2o3p4q5r6'
down_revision = 'l0m1n2o3p4q5'
branch_labels = None
depends_on    = None

S = 'sipi'

ETL_USER_ID  = '00000000-0000-0000-0000-000000000001'
TEST_USER_ID = '00000000-0000-0000-0000-000000000002'


def upgrade() -> None:
    # 1. Nueva columna
    op.add_column(
        'usuarios',
        sa.Column('is_sistema', sa.Boolean, nullable=False, server_default='false'),
        schema=S,
    )

    # 2. Seed: usuarios de sistema
    op.execute(f"""
        INSERT INTO {S}.usuarios
          (id, nombre, nombre_usuario, hashed_contrasena, email_verificado,
           is_sistema, created_at)
        VALUES
          ('{ETL_USER_ID}',  'Sistema ETL',      'etluser',  '!', false, true, NOW()),
          ('{TEST_USER_ID}', 'Usuario de Prueba', 'testuser', '!', false, true, NOW())
        ON CONFLICT (id) DO NOTHING
    """)


def downgrade() -> None:
    op.execute(f"""
        DELETE FROM {S}.usuarios
        WHERE id IN ('{ETL_USER_ID}', '{TEST_USER_ID}')
    """)
    op.drop_column('usuarios', 'is_sistema', schema=S)
