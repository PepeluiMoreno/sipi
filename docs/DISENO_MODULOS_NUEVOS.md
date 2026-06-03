# Diseño de los 3 módulos nuevos (acceso · comunicación · configuración)

Referencia: la app **SIGA** (`/opt/docker/apps/SIGA/backend/app/modules/`). Aquí se
adapta su patrón a SIPI: esquema único `sipi` (opción B), PK `String(36)` (UUID),
`UUIDPKMixin`/`AuditMixin` propios, y ubicación en
`packages/sipi-core/sipi_core/modules/<dominio>/`. Las dos apps (`apps/sipi`,
`apps/sipi-survey`) consumen estos módulos vía el core compartido.

> **Pendiente de tu visto bueno antes de codificar.** Nada de esto está implementado aún.

---

## 1. Módulo `acceso` (RBAC por perfiles/roles) — estilo SIGA

**Concepto** (igual que SIGA): el permiso es por **transacción** (acción atómica).
Los **roles** agrupan transacciones; los **usuarios** tienen roles; una **matriz de
permisos** precalculada (rol→transacciones) resuelve la autorización en runtime.
Las **funcionalidades** agrupan transacciones para la UI.

### Modelos (`modules/acceso/models/`)
| Modelo | Tabla | Campos clave |
|---|---|---|
| `Usuario` *(ya existe en `modules/usuarios`)* | `usuarios` | + `password_hash`, `activo`, `ultimo_acceso`, `intentos_login`, `bloqueado_hasta`, `reset_token*` (migración aditiva) |
| `Rol` *(ya existe, a extender)* | `roles` | `codigo`(uq), `nombre`, `tipo`, `nivel`, `es_territorial`, `nivel_territorial`, `sistema`, `activo` |
| `Transaccion` | `transacciones` | `codigo`(uq), `nombre`, `modulo`, `tipo`, `activa`, `sistema` |
| `Funcionalidad` | `funcionalidades` | `codigo`(uq), `nombre`, `modulo`, `orden`, `activa` |
| `RolTransaccion` | `roles_transacciones` | `rol_id`→roles, `transaccion_id`→transacciones |
| `RolFuncionalidad` | `roles_funcionalidades` | `rol_id`, `funcionalidad_id` |
| `FuncionalidadTransaccion` | `funcionalidades_transacciones` | `funcionalidad_id`, `transaccion_id` |
| `UsuarioRol` | `usuarios_roles` | `usuario_id`, `rol_id`, (+ `ambito_territorial_id` opcional) |
| `AuditoriaAcceso` | `auditoria_acceso` | `usuario_id`, `transaccion`, `resultado`, `ts`, `detalle` |

**Ámbito territorial** (fase 2 del módulo): `UsuarioRol.ambito_territorial_id` →
`provincias`/`comunidades_autonomas` del core, para roles territoriales
(p. ej. validador por provincia).

### Servicios (`modules/acceso/services/`)
- `permission_matrix.py` — `PermissionMatrixBuilder`/`Snapshot` (rol→transacciones
  precalculado, cacheable; regenera por evento). Igual que SIGA.
- `acceso_service.py` — login, hash/verify password, reset, bloqueo por intentos.
- `authorization.py` — `requiere(transaccion: str)` (decorador/guard para resolvers
  GraphQL) y `puede(usuario, transaccion, ambito=None) -> bool`.
- `catalog.py` / `diccionario_transacciones.py` — catálogo declarativo de
  transacciones por módulo (fuente de verdad para el seed).

### Integración con el dominio
- **Ratificación de hallazgos = transacción RBAC.** `expediente.ratificar` y
  `expediente.descartar` son transacciones; al ejecutarlas (con permiso) se
  actualiza `Expediente.estado` y, si procede, `Inmueble.estado_ciclo_vida`.
- Catálogo inicial de transacciones SIPI: `inmueble.crear/editar`,
  `expediente.ratificar/descartar`, `entidad_religiosa.editar`,
  `vigilancia.dispositivo.crear/activar/pausar` (para `apps/sipi-survey`), etc.

### GraphQL (`apps/sipi/api`)
Tipos y queries/mutations para usuarios/roles/transacciones; `me { permisos }`;
guards en mutations sensibles. Seeds de roles base (admin, catalogador, validador,
operador-vigilancia, consulta).

---

## 2. Módulo `comunicacion` (comunicación interna) — estilo SIGA

**Concepto**: notificaciones de **dominio al usuario** (distintas de las
`odmgr_notifications` del ETL, que son monitorización). Catálogo de tipos +
instancias por usuario, multi-canal (in-app primero; email después).

### Modelos (`modules/comunicacion/models/`)
| Modelo | Tabla | Campos clave |
|---|---|---|
| `TipoNotificacion` | `tipos_notificacion` | `codigo`(uq), `nombre`, `categoria`, `permite_email/inapp/...`, `prioridad`, `requiere_accion`, `template_asunto`, `template_cuerpo`, `icono`, `color` |
| `Notificacion` | `notificaciones` | `tipo_id`, `usuario_id`, `titulo`, `cuerpo`, `leida_at`, `accion_url`, `entidad_tipo`/`entidad_id` (polimórfico: p.ej. Expediente), `prioridad`, `created_at` |
| *(fase 2)* `Mensaje`/`Conversacion` | `mensajes` | mensajería directa entre usuarios (SIGA usa XMPP/ejabberd; en SIPI v1 lo dejamos fuera) |

### Servicios (`modules/comunicacion/services/`)
- `notificacion_service.py` — `notificar(tipo_codigo, usuario_ids|roles, contexto)`;
  renderiza plantilla, crea `Notificacion`, marca leída, lista no leídas.
- `destinatario_resolver.py` — resuelve destinatarios por **rol/ámbito** (apoyado
  en `acceso`): p. ej. "validadores de la provincia X".
- `plantilla_email.py` — render de plantillas (fase email).

### Integración con el dominio
- Al crear un `Expediente` en estado `propuesto` (detección de
  `apps/sipi-survey`/discovery) → `notificar('hallazgo.propuesto', rol='validador',
  ambito=provincia_inmueble, contexto={expediente})`.
- Al ratificar/descartar → notificar al proponente/responsable.

### GraphQL
`notificaciones(soloNoLeidas)`, `marcarLeida`, contador no leídas; suscripción
(fase 2). La **bandeja de validación** del frontend se alimenta de
`expedientes(estado: PROPUESTO)` + estas notificaciones.

---

## 3. Módulo `configuracion` (parametrización) — estilo SIGA

**Concepto**: parámetros tipados del sistema, por **ámbito** (global / app-sipi /
app-survey), con validación e historial. Centraliza lo que hoy está disperso en
`.env`/constantes.

### Modelos (`modules/configuracion/models/`)
| Modelo | Tabla | Campos clave |
|---|---|---|
| `Configuracion` | `configuraciones` | `clave`(uq por ámbito), `valor`, `tipo_dato`(str/int/bool/json), `ambito`(global/sipi/survey), `descripcion`, `categoria`, `editable`, `sistema` |
| `ReglaValidacionConfig` | `reglas_validacion_config` | `configuracion_id`, `tipo_regla`, `parametros`(JSONB) |
| `HistorialConfiguracion` | `historial_configuracion` | `configuracion_id`, `valor_anterior`, `valor_nuevo`, `usuario_id`, `ts` |
| `TemaUI` *(opcional)* | `temas_ui` | branding/colores por app |

### Servicios (`modules/configuracion/services/`)
- `configuracion_service.py` — `get(clave, ambito, default)` con **caché** y
  casteo por `tipo_dato`; `set(...)` con validación + `HistorialConfiguracion`.
- `catalog.py` — catálogo declarativo de parámetros (seed).

### Ejemplos de parámetros SIPI
- `survey.idealista.intervalo_min`, `survey.portales.activos` (app-survey)
- `expediente.auto_descartar_dias`, `notif.email.activo` (app-sipi)
- `geo.geocoder.preferente`, `bdns.api_url` (global)

---

## Ubicación, dependencias y seeds
```
packages/sipi-core/sipi_core/modules/
├── acceso/        {models/, services/, catalog.py, docs/}
├── comunicacion/  {models/, services/}
└── configuracion/ {models/, services/, catalog.py}
```
- Se registran en la **fachada** `sipi_core/models/__init__.py` (la API los expone
  por introspección, igual que el resto).
- Migración **aditiva** (esquema `sipi`): tablas nuevas + columnas aditivas en
  `usuarios`/`roles`. Sin tocar datos existentes.
- Seeds idempotentes (transacciones, roles base, tipos de notificación, parámetros).
- **Quién usa qué**: `apps/sipi` usa los 3; `apps/sipi-survey` usa `acceso`
  (operadores) + `configuracion` (parámetros de los dispositivos) + emite eventos
  que `comunicacion` convierte en notificaciones.

## Orden de implementación sugerido
1. `acceso` núcleo (Transaccion/Funcionalidad/RolTransaccion/UsuarioRol + matriz +
   guard) y catálogo/seed de transacciones del dominio.
2. `configuracion` (rápido, desbloquea parametrizar survey).
3. `comunicacion` (notificaciones de hallazgo/ratificación) enganchado a Expediente.
4. Ámbito territorial y email/mensajería (fase 2).
