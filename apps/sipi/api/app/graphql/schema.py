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
    ) -> list_type:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                stmt = select(model)
                count_stmt = select(func.count()).select_from(model)

                # Soft-delete: excluir registros con deleted_at IS NOT NULL
                if hasattr(model, 'deleted_at'):
                    stmt = stmt.where(model.deleted_at.is_(None))
                    count_stmt = count_stmt.where(model.deleted_at.is_(None))

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
        type(f"{model.__name__}CreateInput", (), {"__annotations__": create_fields})
    )

    async def resolver(info: strawberry.Info, data: CreateInput) -> Optional[gql_type]:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                import uuid
                from datetime import datetime, timezone
                row_data = {k: v for k, v in vars(data).items() if v is not None}
                row_data.setdefault("id", str(uuid.uuid4()))
                row_data.setdefault("created_at", datetime.now(timezone.utc))
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
        type(f"{model.__name__}UpdateInput", (), {"__annotations__": update_fields})
    )

    async def resolver(info: strawberry.Info, data: UpdateInput) -> Optional[gql_type]:
        from app.db.sessions.async_session import async_session_maker
        async with async_session_maker() as db:
            try:
                from datetime import datetime, timezone
                row = (await db.execute(select(model).where(model.id == data.id))).scalar_one_or_none()
                if row is None:
                    return None
                for k, v in vars(data).items():
                    if k != "id" and v is not None:
                        setattr(row, k, v)
                if hasattr(row, "updated_at"):
                    row.updated_at = datetime.now(timezone.utc)
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
                row = (await db.execute(select(model).where(model.id == id))).scalar_one_or_none()
                if row is None:
                    return False
                if hasattr(row, "deleted_at"):
                    from datetime import datetime, timezone
                    row.deleted_at = datetime.now(timezone.utc)
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


# ---------------------------------------------------------------------------
# Factory del schema
# ---------------------------------------------------------------------------

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

    if not queries:
        raise ValueError("No se generaron queries")

    Query = strawberry.type(type("Query", (), queries))
    Mutation = strawberry.type(type("Mutation", (), mutations)) if mutations else None

    schema = strawberry.Schema(query=Query, mutation=Mutation)
    logger.info(f"Schema listo: {len(queries)} queries, {len(mutations)} mutations")
    return schema
