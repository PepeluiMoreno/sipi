"""
load/utils/etl_audit.py — constantes y helpers de auditoría para scripts ETL

Todos los scripts de carga usan ETL_USER_ID como valor de created_by_id
y updated_by_id al insertar o actualizar registros en la base de datos.

TEST_USER_ID se reserva para operaciones interactivas del UI mientras la
gestión real de usuarios (post-MVP) no esté implementada.
"""

ETL_USER_ID  = "00000000-0000-0000-0000-000000000001"
TEST_USER_ID = "00000000-0000-0000-0000-000000000002"


async def verificar_etluser(conn) -> None:
    """Aborta el proceso si etluser no existe en la BD (migración no aplicada)."""
    row = await conn.fetchrow(
        "SELECT id FROM sipi.usuarios WHERE id = $1", ETL_USER_ID
    )
    if row is None:
        raise RuntimeError(
            f"etluser ({ETL_USER_ID}) no encontrado en sipi.usuarios. "
            "Aplica la migración m1n2o3p4q5r6 antes de ejecutar este script."
        )
