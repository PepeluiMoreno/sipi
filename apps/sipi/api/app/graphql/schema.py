# app/graphql/schema.py - Schema GraphQL con soporte de relaciones ManyToOne
import strawberry
import logging
from typing import List, Optional
import importlib
import inspect
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Enum as SAEnum, select, or_, func
from sqlalchemy.orm import selectinload as _selectinload

from app.graphql.types import FilterInput, SortInput, PaginationInput
import re as _re

logger = logging.getLogger(__name__)

def _camel_to_snake(name: str) -> str:
    """Convierte camelCase a snake_case para resolver campos del modelo."""
    s = _re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', name)
    return _re.sub(r'([a-z\d])([A-Z])', r'\1_\2', s).lower()

# Registry global para evitar referencias circulares en tipos GQL
_GQL_TYPE_REGISTRY: dict = {}

# Plurales irregulares en español — el frontend y useAgenteBase esperan estas claves
_PLURAL_OVERRIDES: dict = {
    'Transmision': 'transmisiones',
    'TipoTransmision': 'tiposTransmision',
    'TipoInmueble': 'tiposInmueble',
    'TipoDocumento': 'tiposDocumento',
    'TipoLicencia': 'tiposLicencia',
    'TipoUsoInmueble': 'tiposUsoInmueble',
    'TipoEstadoConservacion': 'tiposEstadoConservacion',
    'TipoEstadoTratamiento': 'tiposEstadoTratamiento',
    'TipoRolTecnico': 'tiposRolTecnico',
    'TipoCertificacionPropiedad': 'tiposCertificacionPropiedad',
    'TipoTituloPropiedad': 'tiposTituloPropiedad',
    'TipoPerson': 'tiposPersona',
    'TipoVia': 'tiposVia',
    'TipoEntidadReligiosa': 'tiposEntidadReligiosa',
    'TipoMimeDocumento': 'tiposMimeDocumento',
    'Diocesis': 'diocesis',
    'ProvinciaEclesiastica': 'provinciasEclesiasticas',
    'EntidadReligiosa': 'entidadesReligiosas',
    'ComunidadAutonoma': 'comunidadesAutonomas',
    'RegistroPropiedad': 'registrosPropiedades',
    'FuenteDocumental': 'fuentesDocumentales',
    'FuenteHistoriografica': 'fuentesHistoriograficas',
    'FiguraProteccion': 'figurasProteccion',
    'NivelProteccion': 'nivelesProteccion',
    'ColegioProfesional': 'colegiosProfesionales',
    'DeteccionAnuncio': 'deteccionesAnuncio',
    'InmuebleDocumento': 'inmueblesDocumentos',
    'TransmisionAnunciante': 'transmisionAnunciantes',
    'IntervencionTecnico': 'intervencionesTecnico',
    'IntervencionSubvencion': 'intervencionesSubvencion',
    'SubvencionAdministracion': 'subvencionesAdministracion',
    'InmuebleNivelProteccion': 'inmueblesNivelProteccion',
    'EntidadLocalMenor': 'entidadesLocalesMenores',
    'NotariaTitular': 'notariasTitulares',
    'DiocesisTitular': 'diocesisTitulares',
    'AdministracionTitular': 'administracionesTitulares',
    'RegistroPropiedadTitular': 'registrosPropiedadesTitulares',
    'EntidadReligiosaTitular': 'entidadesReligiosaTitulares',
    'ProcesoVigilancia': 'procesosVigilancia',
    'ProcesoDestinatarioRol': 'procesoDestinatariosRol',
    'ProcesoDestinatarioUsuario': 'procesoDestinatariosUsuario',
}


def _pluralize(name: str) -> str:
    """Convierte el nombre de un modelo a su plural GQL en camelCase español."""
    if name in _PLURAL_OVERRIDES:
        return _PLURAL_OVERRIDES[name]
    lower = name[0].lower() + name[1:]
    # Palabras terminadas en consonante (excl. 's') → +es
    if lower and lower[-1] not in 'aeiouáéíóús':
        return lower + 'es'
    return lower + 's'


# ---------------------------------------------------------------------------
# Column → GraphQL type mapping
# ---------------------------------------------------------------------------

def _graphql_type_for_column(column):
    """Mapea una columna SQLAlchemy a un tipo Python compatible con Strawberry."""
    col_type_str = str(column.type).lower()
    if "geometry" in col_type_str or "geography" in col_type_str:
        return None  # Excluir columnas espaciales

    try:
        python_type = column.type.python_type
        nullable = column.nullable
        if python_type == int:
            return (Optional[int] if nullable else int) if column.name != "id" else strawberry.ID
        if python_type == str:
            return Optional[str] if nullable else str
        if python_type == bool:
            return Optional[bool] if nullable else bool
        if python_type == float:
            return Optional[float] if nullable else float
        if python_type in (datetime, date, Decimal):
            return Optional[str] if nullable else str
        if python_type == dict:  # JSONB (parametros, datos, payload…) → JSON scalar
            return Optional[strawberry.scalars.JSON] if nullable else strawberry.scalars.JSON
        return Optional[str] if nullable else str
    except NotImplementedError:
        return Optional[str]


# ---------------------------------------------------------------------------
# Carga de modelos
# ---------------------------------------------------------------------------

def load_all_models() -> list:
    import sipi_core.models as _models_pkg
    models_dict: dict = {}
    for attr_name in dir(_models_pkg):
        if attr_name.startswith("_"):
            continue
        try:
            attr = getattr(_models_pkg, attr_name)
        except Exception:
            continue
        if hasattr(attr, "__tablename__") and attr_name not in models_dict:
            models_dict[attr_name] = attr
    logger.info(f"{len(models_dict)} modelos cargados desde sipi_core")
    return list(models_dict.values())


# ---------------------------------------------------------------------------
# Creación de tipos GQL con soporte de relaciones
# ---------------------------------------------------------------------------

def _make_gql_type(model, nested: bool = False):
    """
    Construye un @strawberry.type desde un modelo SQLAlchemy.

    nested=False (por defecto): tipo completo — incluye columnas, propiedades
                                 y relaciones ManyToOne como objetos anidados.
    nested=True: tipo plano — solo columnas y propiedades. Usado como tipo
                 de los campos anidados para evitar recursión infinita.
    """
    type_key = f"{model.__name__}{'Nested' if nested else ''}"

    if type_key in _GQL_TYPE_REGISTRY:
        return _GQL_TYPE_REGISTRY[type_key]

    # Registrar placeholder para romper referencias circulares durante recursión
    _GQL_TYPE_REGISTRY[type_key] = None

    fields = {}

    # 1. Mapear columnas
    for column in model.__table__.columns:
        gql_t = _graphql_type_for_column(column)
        if gql_t is not None:
            fields[column.name] = gql_t

    # 2. Mapear @property fields
    for attr_name in dir(model):
        if attr_name.startswith("_"):
            continue
        try:
            attr = getattr(model, attr_name)
        except Exception:
            continue
        if isinstance(attr, property) and attr.fget:
            try:
                ann = inspect.signature(attr.fget).return_annotation
            except (ValueError, TypeError):
                ann = inspect.Parameter.empty
            if ann == inspect.Parameter.empty:
                return_type = Optional[str]
            elif ann is int:
                return_type = Optional[int]
            elif ann is bool:
                return_type = Optional[bool]
            elif ann is float:
                return_type = Optional[float]
            else:
                return_type = Optional[str]
            fields[attr_name] = return_type

    # 3. Mapear relaciones ManyToOne (solo para tipos raíz, no para los anidados)
    if not nested:
        try:
            from sqlalchemy import inspect as sa_inspect
            mapper = sa_inspect(model)
            for rel in mapper.relationships:
                if rel.direction.name == "MANYTOONE":
                    related_model = rel.mapper.class_
                    related_type = _make_gql_type(related_model, nested=True)
                    if related_type is not None:
                        fields[rel.key] = Optional[related_type]
        except Exception as e:
            logger.debug(f"No se pudieron procesar relaciones de {model.__name__}: {e}")

    type_name = type_key  # "Transmision" o "InmuebleNested", etc.
    cls = type(type_name, (), {"__annotations__": fields, "_model_class": model})

    try:
        result = strawberry.type(cls)
        _GQL_TYPE_REGISTRY[type_key] = result
        return result
    except Exception as e:
        logger.warning(f"Error creando tipo GQL {type_key}: {e}")
        _GQL_TYPE_REGISTRY[type_key] = None
        return None


def _make_list_type(model_name: str, item_type):
    """Construye un @strawberry.type { items: [T], total: Int } para paginación."""
    cls = type(f"{model_name}List", (), {
        "__annotations__": {"items": List[item_type], "total": int}
    })
    return strawberry.type(cls)


# ---------------------------------------------------------------------------
# Conversión SQLAlchemy → instancia GQL
# ---------------------------------------------------------------------------

def _to_gql(instance, gql_type):
    """Convierte una instancia SQLAlchemy al tipo GQL correspondiente."""
    if instance is None:
        return None

    annotations = getattr(gql_type, "__annotations__", {})
    kwargs = {}

    for field_name, field_type in annotations.items():
        try:
            value = getattr(instance, field_name, None)
        except Exception:
            value = None

        if value is None:
            kwargs[field_name] = None
            continue

        # Detectar instancia SQLAlchemy por presencia de estado interno
        if hasattr(value, "_sa_instance_state"):
            actual_type = field_type
            # Desenvolver Optional[T] → T
            if hasattr(field_type, "__args__") and field_type.__args__:
                actual_type = field_type.__args__[0]
            kwargs[field_name] = _to_gql(value, actual_type)
        elif isinstance(value, (datetime, date)):
            kwargs[field_name] = value.isoformat()
        elif isinstance(value, Decimal):
            kwargs[field_name] = float(value)
        elif hasattr(value, "__geo_interface__"):
            kwargs[field_name] = str(value)  # PostGIS fallback
        else:
            kwargs[field_name] = value

    try:
        return gql_type(**kwargs)
    except Exception as e:
        logger.warning(f"Error instanciando {gql_type}: {e}")
        return None


# ---------------------------------------------------------------------------
# Helper: obtener relaciones ManyToOne para eager-loading
# ---------------------------------------------------------------------------

def _get_manytoone_rel_attrs(model):
    """Retorna lista de atributos de relación ManyToOne para usar en selectinload."""
    attrs = []
    try:
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(model)
        for rel in mapper.relationships:
            if rel.direction.name == "MANYTOONE":
                rel_attr = getattr(model, rel.key, None)
                if rel_attr is not None:
                    attrs.append(rel_attr)
    except Exception:
        pass
    return attrs


# ---------------------------------------------------------------------------
# Resolvers
# ---------------------------------------------------------------------------

def _make_list_resolver(model, gql_type, list_type):
    eager_attrs = _get_manytoone_rel_attrs(model)

    async def resolver(
        info: strawberry.Info,
        limit: int = 20,
        offset: int = 0,
        search: Optional[str] = None,
        filters: Optional[List[FilterInput]] = None,
        sort: Optional[List[SortInput]] = None,
        eliminados: bool = False,
    ) -> list_type:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                if not await _exigir_crud(info, db, model.__name__, "consultar"):
                    return list_type(items=[], total=0)
                stmt = select(model)
                count_stmt = select(func.count()).select_from(model)

                # Soft-delete: por defecto excluye eliminados; `eliminados:true` → papelera.
                if 'deleted_at' in model.__table__.columns:
                    cond = model.deleted_at.is_not(None) if eliminados else model.deleted_at.is_(None)
                    stmt = stmt.where(cond)
                    count_stmt = count_stmt.where(cond)

                # Eager-load relaciones ManyToOne para evitar lazy-loading en async
                for rel_attr in eager_attrs:
                    try:
                        stmt = stmt.options(_selectinload(rel_attr))
                    except Exception:
                        pass

                # Búsqueda de texto libre en columnas String
                if search:
                    conditions = []
                    for col in model.__table__.columns:
                        if isinstance(col.type, String) and not isinstance(col.type, SAEnum):
                            conditions.append(col.ilike(f"%{search}%"))
                    if conditions:
                        stmt = stmt.where(or_(*conditions))
                        count_stmt = count_stmt.where(or_(*conditions))

                # Filtros estructurados
                if filters:
                    for f in filters:
                        field_snake = _camel_to_snake(f.field)
                        col_attr = getattr(model, field_snake, None) or getattr(model, f.field, None)
                        if col_attr is None:
                            logger.warning(f"Filter field '{f.field}' ('{field_snake}') not found on {model.__name__}")
                            continue
                        op = f.operator.value if hasattr(f.operator, "value") else f.operator
                        v, vs = f.value, f.values or []
                        # Coerción de tipos: FilterInput.value/values llegan como String,
                        # pero las columnas boolean/int necesitan el valor en su tipo Python.
                        try:
                            _pytype = col_attr.type.python_type
                        except Exception:
                            _pytype = str
                        def _coerce(_raw, _t=_pytype):
                            if _raw is None:
                                return None
                            if _t is bool:
                                return str(_raw).strip().lower() in ("true", "1", "yes", "t", "si", "sí")
                            if _t is int:
                                try:
                                    return int(_raw)
                                except (TypeError, ValueError):
                                    return _raw
                            return _raw
                        v = _coerce(v)
                        vs = [_coerce(x) for x in vs]
                        cond = None
                        if op == "eq":       cond = col_attr == v
                        elif op == "ne":     cond = col_attr != v
                        elif op == "gt":     cond = col_attr > v
                        elif op == "gte":    cond = col_attr >= v
                        elif op == "lt":     cond = col_attr < v
                        elif op == "lte":    cond = col_attr <= v
                        elif op == "like":   cond = col_attr.like(f"%{v}%")
                        elif op == "ilike":  cond = col_attr.ilike(f"%{v}%")
                        elif op == "in":     cond = col_attr.in_(vs)
                        elif op == "not_in": cond = col_attr.not_in(vs)
                        elif op == "is_null":
                            cond = col_attr.is_(None) if v else col_attr.is_not(None)
                        elif op == "between" and len(vs) == 2:
                            cond = col_attr.between(vs[0], vs[1])
                        if cond is not None:
                            stmt = stmt.where(cond)
                            count_stmt = count_stmt.where(cond)

                # Ordenación — soporta paths de hasta 2 niveles:
                # "diocesis.nombre"                       → JOIN diocesis, ORDER BY diocesis.nombre
                # "diocesis.provinciaEclesiastica.nombre" → JOIN diocesis JOIN provincias_eclesiasticas
                if sort:
                    from sqlalchemy import asc as _asc, desc as _desc
                    from sqlalchemy import inspect as _sa_inspect
                    _joined = set()  # modelos ya unidos (evita JOINs duplicados)
                    for s in sort:
                        _dir = _desc if s.direction.lower() == "desc" else _asc
                        _parts = [_camel_to_snake(p) for p in s.field.split(".")]
                        try:
                            _cur_model = model
                            for _part in _parts[:-1]:
                                _mapper = _sa_inspect(_cur_model)
                                _rel = next((r for r in _mapper.relationships if r.key == _part), None)
                                if _rel is None:
                                    break
                                _next_model = _rel.mapper.class_
                                if _next_model not in _joined:
                                    stmt = stmt.outerjoin(getattr(_cur_model, _part))
                                    _joined.add(_next_model)
                                _cur_model = _next_model
                            else:
                                _col = getattr(_cur_model, _parts[-1], None)
                                if _col is not None:
                                    stmt = stmt.order_by(_dir(_col))
                        except Exception as _e:
                            logger.debug(f"Sort join error '{s.field}': {_e}")

                # Orden por defecto: nombre ASC si no se especifica sort
                if not sort and hasattr(model, 'nombre'):
                    stmt = stmt.order_by(model.nombre.asc())

                total = (await db.execute(count_stmt)).scalar() or 0
                rows = (await db.execute(stmt.offset(offset).limit(limit))).scalars().all()
                return list_type(items=[_to_gql(r, gql_type) for r in rows], total=total)
            except Exception as e:
                logger.error(f"Error listando {model.__name__}: {e}", exc_info=True)
                return list_type(items=[], total=0)

    resolver.__annotations__["return"] = list_type
    return resolver


def _make_get_resolver(model, gql_type):
    eager_attrs = _get_manytoone_rel_attrs(model)

    async def resolver(
        info: strawberry.Info,
        id: strawberry.ID,
    ) -> Optional[gql_type]:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                if not await _exigir_crud(info, db, model.__name__, "consultar"):
                    return None
                stmt = select(model).where(model.id == id)
                if hasattr(model, 'deleted_at'):
                    stmt = stmt.where(model.deleted_at.is_(None))
                for rel_attr in eager_attrs:
                    try:
                        stmt = stmt.options(_selectinload(rel_attr))
                    except Exception:
                        pass
                row = (await db.execute(stmt)).scalar_one_or_none()
                return _to_gql(row, gql_type)
            except Exception as e:
                logger.error(f"Error obteniendo {model.__name__} {id}: {e}", exc_info=True)
                return None

    resolver.__annotations__["return"] = Optional[gql_type]
    return resolver


# ---------------------------------------------------------------------------
# Enforcement RBAC del CRUD autogenerado: entidad → prefijo de transacción.
# Solo se exige si la transacción `{prefijo}.{accion}` existe en el catálogo;
# si no, la operación queda abierta (entidades internas, acciones no definidas).
# ---------------------------------------------------------------------------
from sipi_core.modules.acceso import catalog as _acc_catalog  # noqa: E402
_TX_CODES = set(_acc_catalog.todas_las_transacciones())

_ENTITY_TX_PREFIX = {
    "Inmueble": "inmueble", "Inmatriculacion": "inmueble", "InmuebleDenominacion": "inmueble",
    "InmuebleCita": "inmueble", "InmuebleUso": "inmueble", "InmuebleNivelProteccion": "inmueble",
    "InmuebleOSMExt": "inmueble", "InmuebleWDExt": "inmueble",
    "EntidadReligiosa": "entidad_religiosa", "EntidadReligiosaTitular": "entidad_religiosa",
    "Diocesis": "entidad_religiosa", "DiocesisTitular": "entidad_religiosa",
    "ProvinciaEclesiastica": "entidad_religiosa", "Parroquia": "entidad_religiosa",
    "Administracion": "administracion", "AdministracionTitular": "administracion",
    "Notaria": "notaria", "NotariaTitular": "notaria",
    "RegistroPropiedad": "registro", "RegistroPropiedadTitular": "registro",
    "AgenciaInmobiliaria": "agente", "ColegioProfesional": "agente", "Tecnico": "agente", "Privado": "agente",
    "Documento": "documento", "InmuebleDocumento": "documento",
    "Transmision": "transmision", "TransmisionAnunciante": "transmision",
    "Transmitente": "transmision", "Adquiriente": "transmision",
    "Intervencion": "intervencion", "IntervencionTecnico": "intervencion",
    "IntervencionSubvencion": "intervencion", "SubvencionAdministracion": "intervencion",
    "ComunidadAutonoma": "geografia", "Provincia": "geografia", "Municipio": "geografia",
    "Configuracion": "config", "HistorialConfiguracion": "config",
    "Asociacion": "acceso", "Usuario": "acceso", "UsuarioRol": "acceso", "Rol": "acceso",
    "RolTransaccion": "acceso", "RolFuncionalidad": "acceso", "Funcionalidad": "acceso",
    "FuncionalidadTransaccion": "acceso", "Transaccion": "acceso",
}
_CATALOGO_EXTRA = {"FiguraProteccion", "NivelProteccion", "FuenteDocumental", "FuenteHistoriografica"}


def _tx_prefix(model_name: str) -> Optional[str]:
    if model_name in _ENTITY_TX_PREFIX:
        return _ENTITY_TX_PREFIX[model_name]
    if model_name.startswith("Tipo") or model_name in _CATALOGO_EXTRA:
        return "catalogo"
    return None


# Módulos sin CRUD por acción: cualquier escritura usa su transacción única.
_ESCRITURA_UNICA = {"config": "editar", "catalogo": "editar", "geografia": "editar", "acceso": "administrar"}


async def _exigir_crud(info, db, model_name: str, accion: str) -> bool:
    """True si autorizado (o no aplica); False si denegado (audita el intento)."""
    prefix = _tx_prefix(model_name)
    if not prefix:
        return True
    # Lectura → siempre `{prefix}.consultar`; escritura → acción única del módulo si aplica.
    accion_tx = accion if accion == "consultar" else _ESCRITURA_UNICA.get(prefix, accion)
    codigo = f"{prefix}.{accion_tx}"
    if codigo not in _TX_CODES:
        return True
    from app.graphql.authz import exigir, PermisoDenegado
    try:
        await exigir(info, db, codigo)
        return True
    except PermisoDenegado:
        await db.commit()  # persistir la auditoría del intento denegado
        return False


def _make_create_resolver(model, gql_type):
    """Crea el input type y resolver para crear una entidad."""
    create_fields = {}
    for col in model.__table__.columns:
        if col.name in (
            "id", "created_at", "updated_at", "deleted_at",
            "created_by_id", "updated_by_id", "deleted_by_id",
            "created_from_ip", "updated_from_ip",
        ):
            continue
        gql_t = _graphql_type_for_column(col)
        if gql_t is not None:
            create_fields[col.name] = Optional[gql_t]

    if not create_fields:
        return None, None

    CreateInput = strawberry.input(
        type(f"{model.__name__}CreateInput", (),
             {"__annotations__": create_fields, **{k: None for k in create_fields}})
    )

    async def resolver(info: strawberry.Info, data: CreateInput) -> Optional[gql_type]:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                if not await _exigir_crud(info, db, model.__name__, "crear"):
                    return None
                import uuid
                from datetime import datetime, timezone
                row_data = {k: v for k, v in vars(data).items() if v is not None}
                row_data.setdefault("id", str(uuid.uuid4()))
                # Columnas TIMESTAMP WITHOUT TIME ZONE → naive (asyncpg rechaza aware)
                row_data.setdefault("created_at", datetime.now(timezone.utc).replace(tzinfo=None))
                instance = model(**row_data)
                db.add(instance)
                await db.commit()
                await db.refresh(instance)
                return _to_gql(instance, gql_type)
            except Exception as e:
                logger.error(f"Error creando {model.__name__}: {e}", exc_info=True)
                await db.rollback()
                return None

    resolver.__annotations__["return"] = Optional[gql_type]
    return CreateInput, resolver


def _make_update_resolver(model, gql_type):
    """Crea el input type y resolver para actualizar una entidad (PUT parcial)."""
    update_fields: dict = {"id": strawberry.ID}
    for col in model.__table__.columns:
        if col.name in (
            "id", "created_at", "updated_at", "deleted_at",
            "created_by_id", "updated_by_id", "deleted_by_id",
            "created_from_ip", "updated_from_ip",
        ):
            continue
        gql_t = _graphql_type_for_column(col)
        if gql_t is not None:
            update_fields[col.name] = Optional[gql_t]

    if len(update_fields) <= 1:  # Solo id
        return None, None

    UpdateInput = strawberry.input(
        type(f"{model.__name__}UpdateInput", (),
             {"__annotations__": update_fields, **{k: None for k in update_fields if k != "id"}})
    )

    async def resolver(info: strawberry.Info, data: UpdateInput) -> Optional[gql_type]:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                if not await _exigir_crud(info, db, model.__name__, "editar"):
                    return None
                from datetime import datetime, timezone
                row = (await db.execute(select(model).where(model.id == data.id))).scalar_one_or_none()
                if row is None:
                    return None
                for k, v in vars(data).items():
                    if k != "id" and v is not None:
                        setattr(row, k, v)
                if hasattr(row, "updated_at"):
                    row.updated_at = datetime.now(timezone.utc).replace(tzinfo=None)
                await db.commit()
                await db.refresh(row)
                return _to_gql(row, gql_type)
            except Exception as e:
                logger.error(f"Error actualizando {model.__name__}: {e}", exc_info=True)
                await db.rollback()
                return None

    resolver.__annotations__["return"] = Optional[gql_type]
    return UpdateInput, resolver


def _make_delete_resolver(model):
    async def resolver(info: strawberry.Info, id: strawberry.ID) -> bool:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                if not await _exigir_crud(info, db, model.__name__, "borrar"):
                    return False
                row = (await db.execute(select(model).where(model.id == id))).scalar_one_or_none()
                if row is None:
                    return False
                if hasattr(row, "deleted_at"):
                    from datetime import datetime, timezone
                    row.deleted_at = datetime.now(timezone.utc).replace(tzinfo=None)
                else:
                    await db.delete(row)
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error eliminando {model.__name__} {id}: {e}", exc_info=True)
                await db.rollback()
                return False

    resolver.__annotations__["return"] = bool
    return resolver


def _make_restore_resolver(model):
    """Papelera: restaura un registro soft-deleted (deleted_at → NULL). Permiso: editar."""
    async def resolver(info: strawberry.Info, id: strawberry.ID) -> bool:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                if not await _exigir_crud(info, db, model.__name__, "editar"):
                    return False
                row = (await db.execute(select(model).where(model.id == id))).scalar_one_or_none()
                if row is None:
                    return False
                row.deleted_at = None
                if hasattr(row, "deleted_by_id"):
                    row.deleted_by_id = None
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error restaurando {model.__name__} {id}: {e}", exc_info=True)
                await db.rollback()
                return False
    return resolver


def _make_purge_resolver(model):
    """Papelera: borrado físico definitivo. Permiso: borrar."""
    async def resolver(info: strawberry.Info, id: strawberry.ID) -> bool:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                if not await _exigir_crud(info, db, model.__name__, "borrar"):
                    return False
                row = (await db.execute(select(model).where(model.id == id))).scalar_one_or_none()
                if row is None:
                    return False
                await db.delete(row)
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Error purgando {model.__name__} {id}: {e}", exc_info=True)
                await db.rollback()
                return False
    return resolver


# ---------------------------------------------------------------------------
# Factory del schema
# ---------------------------------------------------------------------------

@strawberry.type
class HallazgoAccionResult:
    """Resultado de comprobar un hallazgo (verificar/descartar)."""
    ok: bool
    id: strawberry.ID
    estado: Optional[str] = None
    expediente_id: Optional[str] = None
    mensaje: Optional[str] = None


@strawberry.type
class UsuarioAccionResult:
    """Resultado de registrar un usuario o fijar su contraseña."""
    ok: bool
    id: Optional[strawberry.ID] = None
    mensaje: Optional[str] = None


@strawberry.type
class AuthResult:
    """Resultado de autenticación: token de acceso (JWT) si las credenciales valen."""
    ok: bool
    token: Optional[str] = None
    usuario_id: Optional[strawberry.ID] = None
    nombre_usuario: Optional[str] = None
    mensaje: Optional[str] = None


@strawberry.type
class MuestraProbar:
    """Una muestra obtenida al probar una fuente de vigilancia."""
    fuente: Optional[str] = None
    titulo: Optional[str] = None
    url: Optional[str] = None
    precio: Optional[str] = None
    score: Optional[float] = None


@strawberry.type
class ProbarResult:
    """Resultado de probar/ejecutar un proceso de vigilancia."""
    ok: bool
    mensaje: Optional[str] = None
    muestras: List[MuestraProbar] = strawberry.field(default_factory=list)
    creados: int = 0  # nº de Hallazgo creados (solo en ejecutar)


def _vig_score(texto: str, incl: list, excl: list):
    """Confianza 0..1 por densidad de keywords (inclusión suma, exclusión resta)."""
    low = (texto or "").lower()
    ni = sum(low.count(k) for k in incl)
    ne = sum(low.count(k) for k in excl)
    if not incl and not excl:
        return 0.5, ni, ne
    conf = 0.5 + 0.15 * ni - 0.25 * ne
    return max(0.0, min(1.0, conf)), ni, ne


def _vig_tipo_evento(tipo_proceso: str):
    from sipi_core.models import TipoEventoExpediente as _T
    return {"portal_inmobiliario": _T.PUESTA_EN_VENTA,
            "desacralizacion": _T.CAMBIO_DE_USO,
            "prensa": _T.CAMBIO_VISITABILIDAD}.get(tipo_proceso, _T.PUESTA_EN_VENTA)


def _probar_construir_request(fetcher: str, fp: dict):
    """(url, metodo, query) para una fuente según su fetcher. url=None si no aplica."""
    if fetcher == "api_rest":
        base = (fp.get("url_base") or "").rstrip("/")
        if not base:
            return None, "GET", {}
        return base + (fp.get("endpoint") or ""), (fp.get("metodo") or "GET").upper(), (fp.get("query") or {})
    if fetcher in ("html_paginated", "html_searchloop"):
        return fp.get("url_busqueda") or None, "GET", {}
    if fetcher == "rss_atom":
        return fp.get("feed_url") or None, "GET", {}
    return None, "GET", {}


def _probar_items_json(resp) -> list:
    """Best-effort: extrae una lista de ítems {titulo,url,precio} de una respuesta JSON."""
    try:
        data = resp.json()
    except Exception:
        return []
    items = data if isinstance(data, list) else None
    if items is None and isinstance(data, dict):
        for k in ("elementList", "items", "results", "data", "elements", "anuncios"):
            if isinstance(data.get(k), list):
                items = data[k]; break
    out = []
    for it in (items or []):
        if not isinstance(it, dict):
            continue
        def g(*ks):
            for k in ks:
                if it.get(k) not in (None, ""):
                    return str(it[k])
            return None
        out.append({"titulo": g("titulo", "title", "name", "address", "direccion"),
                    "url": g("url", "link", "href", "permalink"),
                    "precio": g("precio", "price", "priceInfo")})
    return out


async def _vig_run(info: "strawberry.Info", proceso_id: strawberry.ID,
                   fuente_id: Optional[str], persistir: bool) -> ProbarResult:
    """Motor de vigilancia: descarga las fuentes activas de un proceso (httpx),
    muestrea ítems (JSON para API REST), puntúa por keywords y —si `persistir`—
    crea `Hallazgo` (PENDIENTE, con certeza/confianza, dedupe por url). La extracción
    HTML fina por selectores es del motor de survey (bs4); aquí va lo verificable."""
    import time as _time
    import httpx as _httpx
    from app.db.sessions.async_session import async_session_maker
    from sqlalchemy import select as _select
    from sipi_core.models import ProcesoVigilancia as _PV, Hallazgo as _H
    from sipi_core.models import EstadoHallazgo as _EH, CertezaHallazgo as _CH

    async with async_session_maker() as db:
        proc = (await db.execute(_select(_PV).where(_PV.id == str(proceso_id)))).scalar_one_or_none()
        if proc is None:
            return ProbarResult(ok=False, mensaje="Proceso no encontrado.")
        params = proc.parametros or {}
        fuentes = params.get("fuentes") or []
        if fuente_id:
            fuentes = [f for f in fuentes if f.get("id") == fuente_id]
        fuentes = [f for f in fuentes if f.get("activa", True)]
        if not fuentes:
            return ProbarResult(ok=False, mensaje="El proceso no tiene fuentes activas. "
                                                  "Añade una fuente con su fetcher (API/HTML/RSS).")
        incl = [k.lower() for k in (params.get("keywords_inclusion") or []) if k]
        excl = [k.lower() for k in (params.get("keywords_exclusion") or []) if k]
        umbral = float(params.get("umbral_score") or 60)
        tipo_evento = _vig_tipo_evento(proc.tipo)

        muestras: List[MuestraProbar] = []
        lineas: list = []
        ok_any = False
        creados = 0
        for f in fuentes[:5]:
            nombre = f.get("nombre") or "(fuente)"
            fetcher = f.get("fetcher") or "?"
            fp = f.get("params") or {}
            url, metodo, query = _probar_construir_request(fetcher, fp)
            if not url:
                lineas.append(f"• {nombre} [{fetcher}]: sin URL configurada.")
                continue
            try:
                t0 = _time.time()
                # AsyncClient: NO bloquea el event loop durante la descarga (si fuese
                # síncrono, una ejecución lenta congelaría toda la API, login incluido).
                async with _httpx.AsyncClient(timeout=12, follow_redirects=True,
                                              headers={"User-Agent": "sipi-vigilancia/run"}) as cli:
                    resp = await (cli.post(url, data=query or None) if metodo == "POST"
                                  else cli.get(url, params=query or None))
                ms = int((_time.time() - t0) * 1000)
                texto = resp.text or ""
                _, ninc, nexc = _vig_score(texto, incl, excl)
                items = _probar_items_json(resp) if (fetcher == "api_rest" and "json" in resp.headers.get("content-type", "").lower()) else []
                for it in items[:25]:
                    titulo = it.get("titulo"); iurl = it.get("url")
                    conf, _, _ = _vig_score(f"{titulo or ''} {it.get('precio') or ''}", incl, excl)
                    muestras.append(MuestraProbar(fuente=nombre, titulo=titulo, url=iurl,
                                                  precio=it.get("precio"), score=round(conf * 100, 1)))
                    if persistir and iurl:
                        ya = (await db.execute(_select(_H).where(
                            _H.proceso_id == proc.id, _H.url_evidencia == iurl))).scalar_one_or_none()
                        if ya is None:
                            db.add(_H(proceso_id=proc.id, fuente=nombre, tipo_evento=tipo_evento,
                                      estado=_EH.PENDIENTE,
                                      certeza=_CH.CIERTO if conf * 100 >= umbral else _CH.DUDOSO,
                                      confianza=round(conf, 3), titulo=(titulo or "")[:255] or None,
                                      url_evidencia=iurl, datos=it))
                            creados += 1
                if 200 <= resp.status_code < 400:
                    ok_any = True
                extra = f", {len(items)} ítems" + (f", {creados} hallazgos" if persistir else "")
                lineas.append(f"• {nombre} [{fetcher}]: HTTP {resp.status_code} "
                              f"({len(texto)//1024} KB, {ms} ms){extra}. "
                              f"Keywords inclusión: {ninc}, exclusión: {nexc}.")
            except Exception as e:  # noqa: BLE001
                lineas.append(f"• {nombre} [{fetcher}]: ERROR — {e}")
        if persistir:
            from datetime import datetime as _dt, timezone as _tz
            proc.ultima_ejecucion = _dt.now(_tz.utc)
            await db.commit()
        return ProbarResult(ok=ok_any, mensaje="\n".join(lineas), muestras=muestras, creados=creados)


async def _probar_proceso_vigilancia(info: "strawberry.Info", proceso_id: strawberry.ID,
                                     fuente_id: Optional[str] = None) -> ProbarResult:
    return await _vig_run(info, proceso_id, fuente_id, persistir=False)


async def _ejecutar_proceso_vigilancia(info: "strawberry.Info", proceso_id: strawberry.ID,
                                       fuente_id: Optional[str] = None) -> ProbarResult:
    return await _vig_run(info, proceso_id, fuente_id, persistir=True)


@strawberry.type
class UsuarioActual:
    """Usuario autenticado del contexto (query `me`)."""
    id: strawberry.ID
    nombre_usuario: str
    nombre: Optional[str] = None
    apellidos: Optional[str] = None
    is_sistema: bool = False
    asociacion_id: Optional[str] = None
    cargo: Optional[str] = None
    email_corporativo: Optional[str] = None
    email_personal: Optional[str] = None
    telefono: Optional[str] = None
    telefono_movil: Optional[str] = None
    acepta_notificaciones: bool = False
    roles: list[str] = strawberry.field(default_factory=list)


# tipo_evento del hallazgo → estado de ciclo de vida que fija en el expediente
_EVENTO_A_CICLO = {
    "puesta_en_venta": "en_venta",
    "vendido": "vendido",
    "cambio_de_uso": "cambio_de_uso",
    "rehabilitacion": "rehabilitacion",
    "rehabilitacion_subvencionada": "rehabilitacion",
}


def _make_hallazgo_transicion_resolvers():
    """Mutations RBAC: el humano COMPRUEBA un hallazgo (dato de un watcher).

    - `verificarHallazgo`: transacción `hallazgo.verificar`. Marca VERIFICADO y lo
      incorpora a un Expediente del inmueble candidato (lo abre si no existe),
      actualizando el estado de ciclo de vida del expediente según el tipo de evento.
    - `descartarHallazgo`: transacción `hallazgo.descartar`. Marca DESCARTADO.
    """
    from datetime import datetime, timezone

    async def verificar_hallazgo(info: strawberry.Info, id: strawberry.ID) -> HallazgoAccionResult:
        from app.db.sessions.async_session import async_session_maker
        from app.graphql.authz import exigir, PermisoDenegado
        from sipi_core.modules.expedientes.expedientes import (
            Hallazgo, Expediente, EstadoHallazgo, EstadoCicloVida,
        )
        from sqlalchemy import select
        async with async_session_maker() as db:
            try:
                usuario = await exigir(info, db, "hallazgo.verificar")
            except PermisoDenegado as e:
                await db.commit()
                return HallazgoAccionResult(ok=False, id=id, mensaje=str(e))
            h = await db.get(Hallazgo, str(id))
            if h is None:
                return HallazgoAccionResult(ok=False, id=id, mensaje="Hallazgo no encontrado")
            if h.inmueble_candidato_id is None:
                return HallazgoAccionResult(ok=False, id=id,
                    mensaje="El hallazgo no tiene inmueble candidato; asígnalo antes de verificar")
            # Expediente del inmueble: abrir si no existe
            exp = (await db.execute(
                select(Expediente).where(
                    Expediente.inmueble_id == h.inmueble_candidato_id,
                    Expediente.activo.is_(True),
                ).limit(1)
            )).scalar_one_or_none()
            if exp is None:
                exp = Expediente(inmueble_id=h.inmueble_candidato_id,
                                 abierto_por_id=getattr(usuario, "id", None))
                db.add(exp); await db.flush()
            # Incorporar hallazgo y actualizar ciclo de vida del expediente
            ciclo = _EVENTO_A_CICLO.get(h.tipo_evento.value)
            if ciclo is not None:
                exp.estado_actual = EstadoCicloVida(ciclo)
            h.estado = EstadoHallazgo.VERIFICADO
            h.verificado_por_id = getattr(usuario, "id", None)
            h.verificado_at = datetime.now(timezone.utc)
            h.expediente_id = exp.id
            await db.commit()
            return HallazgoAccionResult(ok=True, id=id, estado=h.estado.value, expediente_id=exp.id)

    async def descartar_hallazgo(info: strawberry.Info, id: strawberry.ID) -> HallazgoAccionResult:
        from app.db.sessions.async_session import async_session_maker
        from app.graphql.authz import exigir, PermisoDenegado
        from sipi_core.modules.expedientes.expedientes import Hallazgo, EstadoHallazgo
        async with async_session_maker() as db:
            try:
                usuario = await exigir(info, db, "hallazgo.descartar")
            except PermisoDenegado as e:
                await db.commit()
                return HallazgoAccionResult(ok=False, id=id, mensaje=str(e))
            h = await db.get(Hallazgo, str(id))
            if h is None:
                return HallazgoAccionResult(ok=False, id=id, mensaje="Hallazgo no encontrado")
            h.estado = EstadoHallazgo.DESCARTADO
            h.verificado_por_id = getattr(usuario, "id", None)
            h.verificado_at = datetime.now(timezone.utc)
            await db.commit()
            return HallazgoAccionResult(ok=True, id=id, estado=h.estado.value)

    return verificar_hallazgo, descartar_hallazgo


def _make_usuario_credencial_resolvers():
    """Mutations de credenciales (el hashing ocurre en el servidor):

    - `registrarUsuario`: da de alta un usuario (= miembro de una asociación, o
      especial si no se indica asociación) con su contraseña. Los roles se asignan
      aparte (`createUsuarioRol`).
    - `establecerContrasena`: fija/resetea la contraseña de un usuario.
    """
    import uuid
    from datetime import datetime, timezone

    async def registrar_usuario(
        info: strawberry.Info,
        nombre_usuario: str,
        contrasena: str,
        nombre: str,
        asociacion_id: Optional[str] = None,
        apellidos: Optional[str] = None,
        identificacion: Optional[str] = None,
        email_corporativo: Optional[str] = None,
        email_personal: Optional[str] = None,
        telefono: Optional[str] = None,
        telefono_movil: Optional[str] = None,
        cargo: Optional[str] = None,
        acepta_notificaciones: bool = False,
        is_sistema: bool = False,
    ) -> UsuarioAccionResult:
        from app.db.sessions.async_session import async_session_maker
        from sipi_core.modules.usuarios.users import Usuario
        from sipi_core.modules.usuarios.security import hash_password
        from sqlalchemy import select
        async with async_session_maker() as db:
            try:
                from app.graphql.authz import exigir, PermisoDenegado as _PD
                try:
                    await exigir(info, db, "acceso.administrar")
                except _PD as e:
                    await db.commit()
                    return UsuarioAccionResult(ok=False, mensaje=str(e))
                dup = (await db.execute(
                    select(Usuario).where(Usuario.nombre_usuario == nombre_usuario).limit(1)
                )).scalar_one_or_none()
                if dup is not None:
                    return UsuarioAccionResult(ok=False, mensaje="El nombre de usuario ya existe")
                u = Usuario(
                    id=str(uuid.uuid4()),
                    nombre_usuario=nombre_usuario,
                    hashed_contrasena=hash_password(contrasena),
                    nombre=nombre,
                    apellidos=apellidos,
                    identificacion=identificacion,
                    email_corporativo=email_corporativo,
                    email_personal=email_personal,
                    telefono=telefono,
                    telefono_movil=telefono_movil,
                    asociacion_id=asociacion_id,
                    cargo=cargo,
                    acepta_notificaciones=acepta_notificaciones,
                    is_sistema=is_sistema,
                    email_verificado=False,
                    created_at=datetime.now(timezone.utc).replace(tzinfo=None),
                )
                db.add(u)
                await db.commit()
                return UsuarioAccionResult(ok=True, id=u.id)
            except Exception as e:
                logger.error(f"Error registrando usuario: {e}", exc_info=True)
                await db.rollback()
                return UsuarioAccionResult(ok=False, mensaje=str(e))

    async def establecer_contrasena(
        info: strawberry.Info, usuario_id: strawberry.ID, contrasena: str
    ) -> UsuarioAccionResult:
        from app.db.sessions.async_session import async_session_maker
        from sipi_core.modules.usuarios.users import Usuario
        from sipi_core.modules.usuarios.security import hash_password
        async with async_session_maker() as db:
            try:
                from app.graphql.authz import exigir, PermisoDenegado as _PD
                try:
                    await exigir(info, db, "acceso.administrar")
                except _PD as e:
                    await db.commit()
                    return UsuarioAccionResult(ok=False, mensaje=str(e))
                u = await db.get(Usuario, str(usuario_id))
                if u is None:
                    return UsuarioAccionResult(ok=False, mensaje="Usuario no encontrado")
                u.hashed_contrasena = hash_password(contrasena)
                await db.commit()
                return UsuarioAccionResult(ok=True, id=usuario_id)
            except Exception as e:
                logger.error(f"Error fijando contraseña: {e}", exc_info=True)
                await db.rollback()
                return UsuarioAccionResult(ok=False, mensaje=str(e))

    async def login(info: strawberry.Info, nombre_usuario: str, contrasena: str) -> AuthResult:
        from app.db.sessions.async_session import async_session_maker
        from sipi_core.modules.usuarios.users import Usuario
        from sipi_core.modules.usuarios.security import (
            verify_password, create_access_token, get_jwt_secret,
        )
        from sqlalchemy import select
        async with async_session_maker() as db:
            u = (await db.execute(
                select(Usuario).where(Usuario.nombre_usuario == nombre_usuario).limit(1)
            )).scalar_one_or_none()
            if u is None or not u.hashed_contrasena or not verify_password(contrasena, u.hashed_contrasena):
                return AuthResult(ok=False, mensaje="Usuario o contraseña incorrectos")
            token = create_access_token(u.id, get_jwt_secret())
            return AuthResult(ok=True, token=token, usuario_id=u.id, nombre_usuario=u.nombre_usuario)

    async def actualizar_mis_datos(
        info: strawberry.Info,
        nombre: Optional[str] = None,
        apellidos: Optional[str] = None,
        email_corporativo: Optional[str] = None,
        email_personal: Optional[str] = None,
        telefono: Optional[str] = None,
        telefono_movil: Optional[str] = None,
        cargo: Optional[str] = None,
        acepta_notificaciones: Optional[bool] = None,
    ) -> UsuarioAccionResult:
        """Autoservicio: el usuario autenticado actualiza sus propios datos personales."""
        from app.db.sessions.async_session import async_session_maker
        from app.graphql.authz import usuario_de
        from sipi_core.modules.usuarios.users import Usuario
        ctx = usuario_de(info)
        if ctx is None:
            return UsuarioAccionResult(ok=False, mensaje="No autenticado")
        async with async_session_maker() as db:
            try:
                u = await db.get(Usuario, ctx.id)
                if u is None:
                    return UsuarioAccionResult(ok=False, mensaje="Usuario no encontrado")
                if nombre is not None: u.nombre = nombre
                if apellidos is not None: u.apellidos = apellidos
                if email_corporativo is not None: u.email_corporativo = email_corporativo
                if email_personal is not None: u.email_personal = email_personal
                if telefono is not None: u.telefono = telefono
                if telefono_movil is not None: u.telefono_movil = telefono_movil
                if cargo is not None: u.cargo = cargo
                if acepta_notificaciones is not None: u.acepta_notificaciones = acepta_notificaciones
                await db.commit()
                return UsuarioAccionResult(ok=True, id=u.id)
            except Exception as e:
                logger.error(f"Error en actualizar_mis_datos: {e}", exc_info=True)
                await db.rollback()
                return UsuarioAccionResult(ok=False, mensaje=str(e))

    return registrar_usuario, establecer_contrasena, login, actualizar_mis_datos


def create_schema() -> strawberry.Schema:
    logger.info("Construyendo schema GraphQL...")
    # Limpiar registry al iniciar para evitar artefactos de recargas en desarrollo
    _GQL_TYPE_REGISTRY.clear()

    models = load_all_models()

    queries: dict = {}
    mutations: dict = {}

    for model in models:
        name = model.__name__

        try:
            gql_type = _make_gql_type(model)
            if gql_type is None:
                continue
            list_type = _make_list_type(name, gql_type)
        except Exception as e:
            logger.warning(f"Omitiendo {name}: {e}")
            continue

        # Nombres GQL: plural con pluralización española, singular en camelCase
        q_plural = _pluralize(name)
        q_single = name[0].lower() + name[1:]
        # Evitar colisión cuando plural == singular (ej. Diocesis → diocesis)
        if q_plural == q_single:
            q_single = q_single + "ById"

        queries[q_plural] = strawberry.field(_make_list_resolver(model, gql_type, list_type))
        queries[q_single] = strawberry.field(_make_get_resolver(model, gql_type))

        try:
            CreateInput, create_resolver = _make_create_resolver(model, gql_type)
            if CreateInput and create_resolver:
                create_resolver.__annotations__["data"] = CreateInput
                mutations[f"create{name}"] = strawberry.mutation(create_resolver)
        except Exception as e:
            logger.warning(f"Omitiendo mutación create para {name}: {e}")

        try:
            UpdateInput, update_resolver = _make_update_resolver(model, gql_type)
            if UpdateInput and update_resolver:
                update_resolver.__annotations__["data"] = UpdateInput
                mutations[f"update{name}"] = strawberry.mutation(update_resolver)
        except Exception as e:
            logger.warning(f"Omitiendo mutación update para {name}: {e}")

        try:
            mutations[f"delete{name}"] = strawberry.mutation(_make_delete_resolver(model))
        except Exception as e:
            logger.warning(f"Omitiendo mutación delete para {name}: {e}")

        # Papelera: restaurar/purgar (solo entidades con soft-delete)
        try:
            if "deleted_at" in model.__table__.columns:
                mutations[f"restaurar{name}"] = strawberry.mutation(_make_restore_resolver(model))
                mutations[f"purgar{name}"] = strawberry.mutation(_make_purge_resolver(model))
        except Exception as e:
            logger.warning(f"Omitiendo restaurar/purgar para {name}: {e}")

    if not queries:
        raise ValueError("No se generaron queries")

    # --- Mutations de dominio sujetas a RBAC (transacciones) ---
    try:
        verificar, descartar = _make_hallazgo_transicion_resolvers()
        mutations["verificarHallazgo"] = strawberry.mutation(verificar)
        mutations["descartarHallazgo"] = strawberry.mutation(descartar)
    except Exception as e:
        logger.warning(f"Omitiendo mutaciones de hallazgo (RBAC): {e}")

    # --- Mutations de credenciales (login/registro/contraseña) ---
    try:
        registrar, establecer, login, mis_datos = _make_usuario_credencial_resolvers()
        mutations["registrarUsuario"] = strawberry.mutation(registrar)
        mutations["establecerContrasena"] = strawberry.mutation(establecer)
        mutations["login"] = strawberry.mutation(login)
        mutations["actualizarMisDatos"] = strawberry.mutation(mis_datos)
    except Exception as e:
        logger.warning(f"Omitiendo mutaciones de credenciales: {e}")

    # --- Mutations: probar (dry-run) / ejecutar (crea Hallazgo) un proceso de vigilancia ---
    mutations["probarProcesoVigilancia"] = strawberry.mutation(_probar_proceso_vigilancia)
    mutations["ejecutarProcesoVigilancia"] = strawberry.mutation(_ejecutar_proceso_vigilancia)

    # --- Query `me`: usuario autenticado del contexto ---
    async def _me(info: strawberry.Info) -> Optional[UsuarioActual]:
        ctx = info.context or {}
        u = ctx.get("usuario") if isinstance(ctx, dict) else getattr(ctx, "usuario", None)
        if u is None:
            return None
        return UsuarioActual(
            id=u.id, nombre_usuario=u.nombre_usuario, nombre=u.nombre, apellidos=u.apellidos,
            is_sistema=bool(u.is_sistema), asociacion_id=u.asociacion_id, cargo=u.cargo,
            email_corporativo=u.email_corporativo, email_personal=u.email_personal,
            telefono=u.telefono, telefono_movil=u.telefono_movil,
            acepta_notificaciones=bool(u.acepta_notificaciones),
            roles=[(r.codigo or r.id) for r in (u.roles or [])],
        )
    queries["me"] = strawberry.field(_me)

    Query = strawberry.type(type("Query", (), queries))
    Mutation = strawberry.type(type("Mutation", (), mutations)) if mutations else None

    schema = strawberry.Schema(query=Query, mutation=Mutation)
    logger.info(f"Schema listo: {len(queries)} queries, {len(mutations)} mutations")
    return schema
