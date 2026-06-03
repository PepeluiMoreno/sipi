# Migración de integridad DIFERIDA (Fase 1)

**Contexto.** La Fase 1 (modelo único en sipi-core, esquema B = `sipi`) se cerró
con migraciones **aditivas** validadas contra la BD viva (271 MB, 16.906
entidades_religiosas) sin tocar datos:

- `a25b36811be2` — crea las 16 tablas del modelo que la BD no tenía (incl.
  `expedientes`, `intervenciones*`, `inmuebles_usos`, `portals_*`, `osm_places`…)
  + columnas de ciclo de vida (`estado_ciclo_vida`, `geo_quality`) en `inmuebles`.
- `1c580aa87306` — añade las columnas del modelo que faltaban en tablas
  preexistentes, como **NULLABLE y sin FK** (aditivo, no falla con datos).

Tras esas dos migraciones, la BD coincide **estructuralmente** con el modelo
(todas las tablas y columnas existen) y la API GraphQL arranca y sirve datos
reales.

## Lo que queda PENDIENTE (drift preexistente, no introducido por la Fase 1)

`alembic check` reporta todavía, sobre tablas preexistentes:

- **332 foreign keys** que el modelo declara y la BD (creada laxa con
  `create_all`) no tiene.
- **145 índices** faltantes.
- **29 cambios de tipo** (mayormente `REAL → Float`/`Numeric` en lat/long; bajo
  riesgo) y `server_default`.

Estos son de **integridad/rendimiento**, no bloquean lectura/inserción del ORM.
Se difirieron a una migración dedicada porque:

1. Las 332 FKs pueden fallar si hay **datos huérfanos**; hay que validar tabla a
   tabla antes de añadirlas (las de muestra —inmuebles→municipios,
   ER→diócesis— estaban limpias).
2. Las columnas añadidas en `1c580aa87306` son `NULLABLE`; varias deberían pasar
   a `NOT NULL` tras **backfill**.

## Cómo ejecutar la migración de integridad (cuando se aborde)

1. Para cada FK detectada: `SELECT count(*) FROM hijo h WHERE h.fk IS NOT NULL
   AND NOT EXISTS (SELECT 1 FROM padre p WHERE p.id = h.fk)`. Si >0, decidir
   (limpiar huérfanos / poner a NULL / no añadir la FK).
2. Generar la migración con `alembic revision --autogenerate` y **curarla**:
   quitar el ruido cosmético, agrupar `create_foreign_key` / `create_index`.
3. Backfill + `ALTER COLUMN ... SET NOT NULL` donde el modelo lo exija.
4. Aplicar en transacción y `alembic check` hasta 0 diffs.

> Entorno de validación usado: venv con `alembic`+`psycopg2`, `DATABASE_URL`
> apuntando al contenedor local en `localhost:5433`, `DEFINED_SCHEMAS=sipi`,
> `APP_SCHEMA=GIS_SCHEMA=DEFAULT_SCHEMA=sipi`.
