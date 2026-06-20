# Consolidación de modelos: `sipi-api` → `sipi-core`

Estado: **plan / pendiente de ejecutar con base de datos**. Este documento
describe la migración para que `sipi-api` deje de mantener sus propios modelos
en `app/db/models/` y consuma los de [`sipi-core`](https://github.com/PepeluiMoreno/sipi-core)
como dependencia, eliminando la duplicación (la misma clase definida dos veces
fue origen de bugs anteriores en otros proyectos).

> **No es un repoint mecánico.** Implica un cambio de esquema y la regeneración
> de la línea base de Alembic. Debe hacerse de forma deliberada y validarse
> contra una base de datos. Por eso aquí solo se deja el plan y el cableado de
> la dependencia; el intercambio efectivo de modelos **no** se ha aplicado.

## Prerrequisito (ya resuelto)

`sipi-core` no era instalable como paquete (imports flotantes, `pyproject`
apuntando a un paquete inexistente, `__init__` roto). Corregido en la rama
`refactor/paquete-instalable` de `sipi-core`: ahora `pip install -e .` e
`import sipi_core.models` funcionan (61 símbolos, 56 tablas, esquemas
`app`/`gis`). **Mergear esa rama antes de continuar.**

## Divergencia real entre ambos conjuntos de modelos

`sipi-core` es la evolución del modelo de `sipi-api`, no una copia. Diferencias
detectadas (inventario de clases):

**Solo en `sipi-api` (modelo antiguo, a retirar/mapear):**
`Actuacion`, `ActuacionDocumento`, `ActuacionSubvencion`, `ActuacionTecnico`,
`Adquiriente`, `Transmitente`, `TransmisionDocumento`.

**Solo en `sipi-core` (modelo nuevo, gana):**
`Intervencion`, `IntervencionTecnico`, `IntervencionSubvencion` (sustituyen a
`Actuacion*`); `EntidadReligiosa`, `EntidadReligiosaTitular`,
`TipoEntidadReligiosa`; `InmuebleRaw`, `DeteccionAnuncio` (discovery);
`OSMPlace`; `Privado`; `NotariaTitular`; `InmuebleUso`,
`InmuebleNivelProteccion`, `TipoUsoInmueble`, `TipoTituloPropiedad`.

**Comunes (~44 clases):** `Inmueble`, `Inmatriculacion`, actores
(`Administracion`, `Notaria`, `RegistroPropiedad`, `Diocesis`, `Tecnico`,
`AgenciaInmobiliaria`...), geografía, tipologías base, `Usuario`/`Rol`, etc.

**Mapeo conceptual clave:**

| `sipi-api` (antiguo) | `sipi-core` (nuevo) |
|----------------------|---------------------|
| `Actuacion` | `Intervencion` |
| `ActuacionTecnico` | `IntervencionTecnico` |
| `ActuacionSubvencion` | `IntervencionSubvencion` |
| `ActuacionDocumento` | (revisar: ¿documento de intervención?) |
| `Adquiriente` / `Transmitente` | refactorizados (ver `TransmisionAnunciante`) |
| `TransmisionDocumento` | (revisar equivalencia) |

## Decisión de arquitectura a tomar (bloqueante)

Las dos bases declarativas usan **estrategias de esquema distintas**:

- `sipi-api`: **un esquema único** `sipi` (`app/db/base.py`,
  `MetaData(schema=os.getenv("DB_SCHEMA", "sipi"))`).
- `sipi-core`: **doble esquema** `app` + `gis` (`sipi_core/db/registry.py`,
  con `GISMetadata` aparte).

Consolidar en `sipi-core` implica adoptar `app`/`gis`. Eso **cambia el layout
físico de la base de datos** e **invalida las migraciones Alembic actuales** de
`sipi-api`. Hay que decidir:

- **(A)** Adoptar `app`/`gis` de `sipi-core` (recomendado a futuro) →
  regenerar línea base de Alembic y migrar datos del esquema `sipi`.
- **(B)** Mantener un único esquema en `sipi-core` (vía
  `DEFAULT_SCHEMA`/`APP_SCHEMA`/`GIS_SCHEMA` = `sipi`) para minimizar el cambio
  de BD. `registry.py` ya lee estos valores de entorno, así que es viable
  forzar `APP_SCHEMA=sipi` y `GIS_SCHEMA=sipi` y conservar un solo esquema.

> La opción (B) es la de menor riesgo para una BD existente: se conserva el
> esquema `sipi` y solo cambia el *origen* de los modelos, no su ubicación.

## Plan de migración (orden sugerido)

1. **Mergear** `sipi-core@refactor/paquete-instalable`.
2. **Dependencia**: añadir `sipi-core` a `requirements.txt` (ver línea
   comentada ya incluida). Para desarrollo local: `pip install -e ../sipi-core`.
3. **Esquema**: decidir (A) o (B). Para (B), exportar en el entorno
   `APP_SCHEMA=sipi`, `GIS_SCHEMA=sipi`, `DEFAULT_SCHEMA=sipi`.
4. **Repointar imports** en `sipi-api`:
   - `from app.db.base import Base` → `from sipi_core.db.registry import Base`.
   - `from app.db.mixins import ...` → `from sipi_core.mixins import ...`.
   - `from app.db.models.X import ...` → `from sipi_core.models.X import ...`
     (atención a los renombrados `Actuacion*`→`Intervencion*`).
5. **Eliminar** `app/db/models/` y `app/db/mixins/` de `sipi-api` (ya viven en
   `sipi-core`). Mantener solo lo específico de la API (`graphql/`, `core/`,
   `sessions/` si difieren).
6. **GraphQL**: el esquema se autogenera desde la lista de modelos
   (`app/graphql/schema.py`), por lo que la **API pública cambiará**: aparecen
   tipos nuevos (`Intervencion`, `EntidadReligiosa`, `OSMPlace`,
   `InmuebleUso`...) y desaparecen los retirados (`Actuacion`, `Adquiriente`,
   `Transmitente`). Revisar y comunicar el cambio de contrato al frontend.
7. **Alembic**: regenerar la línea base contra los modelos de `sipi-core`:
   ```bash
   alembic revision --autogenerate -m "baseline sobre sipi-core"
   alembic upgrade head   # en un entorno de pruebas primero
   ```
8. **Validar** end-to-end con una BD de pruebas: arranque del servidor GraphQL,
   introspección del esquema y migraciones aplicadas sin diffs pendientes.

## Riesgos

- Cambio de contrato GraphQL (paso 6) → coordinar con `sipi-frontend`.
- Regeneración de migraciones (paso 7) → no aplicar sobre producción sin
  respaldo y plan de migración de datos del esquema `sipi`.
- `ActuacionDocumento` / `TransmisionDocumento` no tienen equivalente directo
  evidente en `sipi-core`; confirmar antes de eliminarlos.
