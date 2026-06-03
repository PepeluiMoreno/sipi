"""fase1 integridad: NO-OP documentada (las FKs/índices viven en el modelo)

IMPORTANTE — lección aprendida. Un primer intento de esta migración añadía 332
FKs que `alembic check` reportaba como "faltantes". Resultó ser un **falso
positivo**: la BD YA tenía esas FKs, pero alembic no las casaba por **falta de
`naming_convention`** en el `MetaData` (las constraints autogeneradas por
PostgreSQL —`<tabla>_<col>_fkey`— no coinciden con lo que alembic espera). Al
aplicarla se crearon ~308 FKs DUPLICADAS (`..._fkey1`), que se eliminaron a mano.

Conclusión: **las FKs y los índices se definen en los modelos** (`sipi_core.models`)
y los crea `metadata.create_all` / la baseline. NO deben añadirse en una migración
de "integridad" aparte mientras el `MetaData` no tenga `naming_convention`.

Esta revisión queda como **NO-OP** para mantener la cadena coherente. El trabajo
pendiente real es:
  1. Añadir un `naming_convention` al `MetaData` en `db/registry.py` para que
     alembic compare FKs/constraints de forma determinista.
  2. Reconciliar entonces nombres de constraints (rename, no recreate).
  3. Cambios de tipo pendientes (29): `REAL→Float` (cosmético) y `VARCHAR→ENUM`
     (requiere `USING` + validar que los valores existentes encajan en el enum).

Revision ID: c1f64df9b284
Revises: 1c580aa87306
Create Date: 2026-06-03
"""
from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = 'c1f64df9b284'
down_revision: Union[str, None] = '1c580aa87306'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # No-op: ver docstring. FKs e índices provienen de los modelos.
    pass


def downgrade() -> None:
    pass
