# Integridad de esquema — estado y pendiente (Fase 1)

## Hecho (migraciones aditivas validadas contra la BD viva, datos intactos)

- `a25b36811be2` — crea las 16 tablas del modelo que faltaban (incl. `expedientes`)
  + columnas de ciclo de vida en `inmuebles`.
- `1c580aa87306` — añade columnas del modelo ausentes en tablas existentes
  (NULLABLE, sin FK).

Tras estas dos, la BD coincide **estructuralmente** con el modelo (todas las
tablas y columnas) y la API GraphQL arranca y sirve datos reales.

Además, durante la sesión se añadieron a mano ~21 FKs que faltaban realmente y se
crearon los índices del modelo. Estado actual: **360 FKs, 0 duplicados**, datos
intactos (16.906 ER, 47.786 toponimos).

## LECCIÓN: el "drift de 332 FKs" era un FALSO POSITIVO

`alembic check` reportaba 332 FKs "faltantes" que **ya existían** en la BD. Causa:
el `MetaData` **no tiene `naming_convention`**, así que alembic no casa las
constraints autogeneradas por PostgreSQL (`<tabla>_<col>_fkey`) con las del
modelo. Un intento de "añadirlas" creó ~308 FKs DUPLICADAS (`..._fkey1`) que hubo
que eliminar. La migración `c1f64df9b284` quedó como **NO-OP documentada**.

## PENDIENTE real (no urgente; no bloquea el ORM ni la API)

1. **`naming_convention` en `db/registry.py`** (raíz del problema):
   ```python
   convention = {
     "ix": "ix_%(column_0_label)s",
     "uq": "uq_%(table_name)s_%(column_0_name)s",
     "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
     "pk": "pk_%(table_name)s",
   }
   metadata = MetaData(schema=DEFAULT_SCHEMA, naming_convention=convention)
   ```
   Tras esto, alembic comparará FKs/índices de forma determinista. Habrá que
   **renombrar** (no recrear) las constraints existentes para alinearlas.

2. **Cambios de tipo (29)**: `REAL→Float` (cosmético) y `VARCHAR→ENUM` (requiere
   `ALTER ... TYPE ... USING` + validar que los valores existentes encajan en el
   enum, p. ej. `tipo_identificacion`).

> Entorno de validación: venv con `alembic`+`psycopg2`, `DATABASE_URL` al
> contenedor local `localhost:5433`, `DEFINED_SCHEMAS=APP_SCHEMA=GIS_SCHEMA=DEFAULT_SCHEMA=sipi`.
