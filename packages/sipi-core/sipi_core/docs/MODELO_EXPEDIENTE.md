# Modelo `Expediente` — ciclo de vida del inmueble

`Expediente` generaliza las antiguas tablas-evento en un único episodio del
ciclo de vida del inmueble, parametrizado por catálogo (`TipoExpediente`). El
historial de un inmueble es el conjunto de sus expedientes ordenados por fecha;
`Inmueble.estado_actual` se deriva del último expediente relevante.

## Entidades (en `sipi_core.models.expedientes`)

- **`TipoExpediente`** (catálogo): `codigo`, `nombre`, `descripcion`,
  `estado_resultante` (a qué estado del ciclo de vida lleva), `notificable`,
  `esquema_datos` (JSON con los campos esperados del tipo), `activo`.
  *Alta de un tipo nuevo = alta en catálogo, no migración.*
- **`Expediente`**: `inmueble_id`, `tipo_expediente_id`, `fecha_inicio`,
  `fecha_fin`, `estado` (del propio expediente), `titulo`, `descripcion`,
  `importe`, `fuente_id`, `referencia_externa`, `enlace`, `confianza`,
  `datos` (JSONB, carga específica del tipo).
- **`ExpedienteActor`**: parte interviniente — `tipo_actor` + `actor_id`
  (polimórfico) + `rol`.
- **`ExpedienteDocumento`**: documentos adjuntos.
- **`Inmueble.estado_actual`** (nuevo campo, indexado): estado del ciclo de vida
  derivado y materializado.

## Estados del ciclo de vida (`Inmueble.estado_actual`)

`EN_USO_RELIGIOSO → DESAFECTADO → ENAJENADO → USO_CIVIL → EN_RUINA → DESAPARECIDO`
(no necesariamente lineal). Se deriva del `estado_resultante` del último
expediente relevante.

## Tipos de expediente iniciales (catálogo)

| código | sustituye a | fuente típica | notificable |
|--------|-------------|---------------|-------------|
| `inmatriculacion` | `Inmatriculacion` | listado CEE | no |
| `actuacion` | `Intervencion`(+`IntervencionTecnico`) | — | no |
| `subvencion` | `IntervencionSubvencion`+`SubvencionAdministracion` | BDNS | sí |
| `enajenacion` | `Transmision`(+`TransmisionAnunciante`) | registro/portales/contratación | sí |
| `cambio_uso` | `InmuebleUso` | Catastro/licencias | sí |
| `proteccion` | `InmuebleNivelProteccion` | BIC/patrimonio | no |
| `secularizacion` | *(nuevo)* | boletines diocesanos | sí |
| `declaracion_ruina` | *(nuevo)* | ayuntamientos/prensa | sí |
| `deteccion` | `DeteccionAnuncio` | OSM/Wikidata/portales | sí |

## Mapa de migración (tabla antigua → expediente)

| Origen | → Expediente |
|--------|--------------|
| `Inmatriculacion.fecha_inmatriculacion` | `fecha_inicio`; `tipo_certificacion_propiedad_id`, registro → `datos`/`referencia_externa`; `Titular` → `ExpedienteActor(rol=titular)` |
| `Transmision.fecha_transmision` | `fecha_inicio`; `precio_venta` → `importe`; `tipo_transmision_id` → `datos`; `notaria_id`/`registro_propiedad_id` → `ExpedienteActor`; `TransmisionAnunciante` → `ExpedienteActor(rol=anunciante)` |
| `Intervencion.fecha_inicio/fin` | `fecha_inicio`/`fecha_fin`; `descripcion`; `IntervencionTecnico` → `ExpedienteActor(rol=tecnico)` |
| `IntervencionSubvencion.importe_aplicado` / `SubvencionAdministracion.importe_aportado` | `importe`; administración → `ExpedienteActor(rol=concedente)`; código BDNS → `referencia_externa` |
| `InmuebleUso` (fecha_desde/hasta, tipo_uso) | `fecha_inicio`/`fecha_fin`; tipo → `datos`; uso actual → deriva `estado_actual` |
| `InmuebleNivelProteccion` | fechas; nivel/figura → `datos` |
| `DeteccionAnuncio` | `confianza`; fuente → `fuente_id`/`datos`; coords candidatas → `datos` |
| `InmuebleCita` | `fuente_id` + cita en `datos` del expediente |

## Fases (aditivo, sin romper)

1. **(hecho)** Añadir modelos `Expediente`/`TipoExpediente`/`ExpedienteActor`/
   `ExpedienteDocumento` y `Inmueble.estado_actual` — sin tocar las tablas
   antiguas. Migración Alembic: `alembic revision --autogenerate` (validar BD).
2. **Backfill**: volcar las filas de las tablas-evento a `expedientes` (script de
   datos) y recalcular `estado_actual`.
3. **Repoint**: API GraphQL y frontend pasan a consumir `Expediente`.
4. **Retirar** las tablas-evento una vez validado.

## Arquitectura de descubrimiento y validación

Los servicios de **descubrimiento** corren **fuera del frontend** y se alimentan
de **suscripciones a datasets de OpenDataManager**
(github.com/PepeluiMoreno/OpenDataManager): BDNS (subvenciones), Plataforma de
Contratación del Sector Público (contratos), portales inmobiliarios (anuncios de
venta), OSM/Wikidata, Catastro, listado CEE…

Flujo:

```
OpenDataManager (datasets)  ──suscripción──▶  servicio de descubrimiento (backend)
                                                   │  (matching/scoring/fusión)
                                                   ▼
                                            HALLAZGO (Expediente en estado "propuesto")
                                                   │
                              ┌────────────────────┼────────────────────┐
                              ▼                                          ▼
                    Notificación al destinatario            Cola de validación en el UI
                    (módulo comunicación, SIGA)                       │
                                                                      ▼
                                              usuario autorizado RATIFICA / VALIDA
                                              (transacción RBAC, módulo acceso)
                                                                      │
                                                                      ▼
                                              Expediente confirmado en el inmueble
```

- El hallazgo entra como `Expediente` con `estado="propuesto"` y su `confianza`.
- Se notifica (tipos notificables del catálogo) y aparece en la **bandeja de
  validación**.
- La **ratificación** es una transacción del módulo de acceso (RBAC); al validar,
  el expediente pasa a `estado="confirmado"` y, si su tipo tiene
  `estado_resultante`, actualiza `Inmueble.estado_actual`.

Ejemplos de origen (todos vía suscripción OpenDataManager): anuncios de venta de
portales → expediente `deteccion`/`enajenacion`; contratos del Estado →
`actuacion`/`subvencion`; BDNS → `subvencion`.
