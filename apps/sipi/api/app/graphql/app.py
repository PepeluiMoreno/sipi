# app/graphql/app.py - VERSIÓN OPTIMIZADA
from typing import Any, Dict
import threading
import traceback
import json
import uuid
from datetime import datetime, timezone

from starlette.applications import Starlette
from starlette.responses import PlainTextResponse, JSONResponse, HTMLResponse, Response
from starlette.routing import Route, Mount
from starlette.requests import Request
from sqlalchemy import select, func, update

from app.db.sessions.async_session import async_session_maker

# Variables globales para la app GraphQL (creación lazy)
_schema = None
_graphql_asgi = None
_schema_lock = threading.Lock()
_schema_created = False


def _create_graphql_assets():
    """
    Crea schema y GraphQL ASGI app de forma atómica (con lock).
    """
    global _schema, _graphql_asgi, _schema_created

    if _schema_created and _graphql_asgi is not None:
        return _schema, _graphql_asgi

    with _schema_lock:
        if _schema_created and _graphql_asgi is not None:
            return _schema, _graphql_asgi

        try:
            from app.graphql.schema import create_schema
            from strawberry.asgi import GraphQL

            print("[FIX] Creating schema GraphQL (lazy)...")
            _schema = create_schema()
            _graphql_asgi = GraphQL(_schema, graphiql=True)
            _schema_created = True
            print("OK Schema GraphQL created")
            return _schema, _graphql_asgi
        except Exception as e:
            print("ERROR Error creando schema GraphQL:", e)
            print(traceback.format_exc())
            raise


# Rutas
async def docs_page(request: Request):
    return HTMLResponse("""
    <html>
    <head><title>SIPI GraphQL API</title></head>
    <body style="font-family: sans-serif; max-width: 800px; margin: 50px auto;">
        <h1>[API] SIPI GraphQL API</h1>
        <ul>
            <li><a href="/graphql">GraphiQL GraphiQL</a></li>
            <li><a href="/schema.graphql">Schema Schema SDL</a></li>
            <li><a href="/stats">Stats Stats</a></li>
        </ul>
    </body>
    </html>
    """)


async def health(request: Request):
    return JSONResponse({"status": "ok", "service": "graphql"})


async def export_schema(request: Request):
    try:
        schema, _ = _create_graphql_assets()
    except Exception as e:
        return PlainTextResponse(f"Error: {e}\n{traceback.format_exc()}", status_code=500)
    
    try:
        if hasattr(schema, "as_str"):
            return PlainTextResponse(schema.as_str())
    except Exception:
        pass
    return PlainTextResponse(str(schema))


async def schema_stats(request: Request):
    """Endpoint de estadísticas del schema GraphQL"""
    try:
        schema, _ = _create_graphql_assets()
    except Exception as e:
        return JSONResponse({
            "error": str(e),
            "traceback": traceback.format_exc()
        }, status_code=500)

    # Obtener tipos del schema (Strawberry usa schema_converter)
    try:
        if hasattr(schema, 'schema_converter'):
            type_map = schema.schema_converter.type_map
        elif hasattr(schema, '_schema'):
            # Fallback para versiones diferentes
            type_map = schema._schema.type_map
        else:
            type_map = {}
        
        # Contar tipos (excluir internos que empiezan con __)
        num_types = len([t for t in type_map.keys() if not str(t).startswith('__')])
    except Exception:
        num_types = 0
    
    # Obtener queries y mutations
    queries = {}
    mutations = {}
    
    if hasattr(schema, 'query_type') and schema.query_type:
        queries = getattr(schema.query_type, 'fields', {}) or getattr(schema.query_type, '_type_definition', {}).get('fields', {})
    
    if hasattr(schema, 'mutation_type') and schema.mutation_type:
        mutations = getattr(schema.mutation_type, 'fields', {}) or getattr(schema.mutation_type, '_type_definition', {}).get('fields', {})

    return JSONResponse({
        "status": "ok",
        "types": num_types,
        "queries": len(queries) if isinstance(queries, (dict, list)) else 0,
        "mutations": len(mutations) if isinstance(mutations, (dict, list)) else 0,
    })


# Wrapper para GraphQL
async def graphql_handler(scope, receive, send):
    """Handler ASGI para GraphQL"""
    try:
        _, graphql_app = _create_graphql_assets()
    except Exception as e:
        # Enviar respuesta de error
        await send({
            "type": "http.response.start",
            "status": 500,
            "headers": [[b"content-type", b"text/plain"]],
        })
        await send({
            "type": "http.response.body",
            "body": f"Error: {e}\n{traceback.format_exc()}".encode(),
        })
        return
    
    # Inyectar BD en scope
    if scope["type"] == "http":
        scope["state"] = scope.get("state", {})
        scope["state"]["db"] = async_session_maker()
    
    # Delegar a GraphQL
    await graphql_app(scope, receive, send)


# ── ODMGR webhook + notification endpoints ────────────────────────────────────

async def odm_webhook(request: Request):
    """
    POST /odm_webhook

    Recibe notificaciones de ODMGR cuando se publica una nueva versión de un dataset.
    Payload esperado (formato ODMGR notification_service.py):
        {
          "event": "dataset.published",
          "consumption_mode": "graphql"|"webhook"|"both",   # opcional
          "dataset": {
            "resource_id": "<uuid>",
            "resource_name": "...",
            "version": "1.2.0",
            "version_type": "patch"|"minor"|"major",
            "record_count": 1234
          }
        }
    """
    try:
        body = await request.body()
        payload = json.loads(body)
    except Exception:
        return JSONResponse({"error": "invalid JSON"}, status_code=400)

    event = payload.get("event", "")
    if event != "dataset.published":
        return JSONResponse({"status": "ignored", "event": event})

    dataset = payload.get("dataset", {})
    resource_id = dataset.get("resource_id", "")
    resource_name = dataset.get("resource_name", "")
    version = dataset.get("version", "")
    version_type = dataset.get("version_type", "patch")
    record_count = dataset.get("record_count")
    consumption_mode = payload.get("consumption_mode") or payload.get(
        "dataset", {}
    ).get("consumption_mode")

    if not resource_id or not resource_name or not version:
        return JSONResponse({"error": "missing required fields"}, status_code=400)

    try:
        from models.odmgr_notifications import OdmgrNotification

        notif = OdmgrNotification(
            id=str(uuid.uuid4()),
            notification_type="data_update",
            resource_id=resource_id,
            resource_name=resource_name,
            dataset_version=version,
            version_type=version_type,
            record_count=int(record_count) if record_count is not None else None,
            consumption_mode=consumption_mode,
            status="pending",   # no visible hasta que el diff esté listo
            raw_payload=body.decode("utf-8", errors="replace"),
            received_at=datetime.now(timezone.utc),
        )

        async with async_session_maker() as session:
            session.add(notif)
            await session.commit()

        return JSONResponse({"status": "ok", "id": notif.id})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notifications_list(request: Request):
    """GET /api/notifications?limit=50&estado=pendiente|tratada|all"""
    limit  = int(request.query_params.get("limit", 100))
    estado = request.query_params.get("estado", "pendiente")  # pendiente | tratada | all

    try:
        from models.odmgr_notifications import OdmgrNotification

        async with async_session_maker() as session:
            stmt = select(OdmgrNotification)
            if estado == "pendiente":
                stmt = stmt.where(OdmgrNotification.status.in_(["ready", "error"]))
            elif estado == "tratada":
                stmt = stmt.where(OdmgrNotification.status.in_(["applied", "dismissed"]))
            # estado == "all" → sin filtro de status
            stmt = stmt.order_by(
                OdmgrNotification.received_at.desc()
            ).limit(limit)
            result = await session.execute(stmt)
            notifications = result.scalars().all()

        items = [
            {
                "id": str(n.id),
                "notification_type": n.notification_type,
                "resource_id": n.resource_id,
                "resource_name": n.resource_name,
                "dataset_version": n.dataset_version,
                "version_type": n.version_type,
                "record_count": n.record_count,
                "consumption_mode": n.consumption_mode,
                "status": n.status,
                "diff_summary": json.loads(n.diff_summary) if n.diff_summary else None,
                "error_message": n.error_message,
                "read": n.read,
                "read_at": n.read_at.isoformat() if n.read_at else None,
                "received_at": n.received_at.isoformat(),
                "ready_at": n.ready_at.isoformat() if n.ready_at else None,
            }
            for n in notifications
        ]
        return JSONResponse({"items": items, "total": len(items)})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notifications_unread_count(request: Request):
    """GET /api/notifications/unread_count — solo cuenta las ready sin leer"""
    try:
        from models.odmgr_notifications import OdmgrNotification

        async with async_session_maker() as session:
            stmt = select(func.count()).select_from(OdmgrNotification).where(
                OdmgrNotification.status == "ready",
                OdmgrNotification.read == False,
                OdmgrNotification.deleted_at == None,
            )
            result = await session.execute(stmt)
            count = result.scalar_one()

        return JSONResponse({"count": count})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notification_mark_read(request: Request):
    """POST /api/notifications/{id}/read"""
    notif_id = request.path_params.get("id", "")

    try:
        from models.odmgr_notifications import OdmgrNotification

        async with async_session_maker() as session:
            stmt = (
                update(OdmgrNotification)
                .where(OdmgrNotification.id == notif_id)
                .values(read=True, read_at=datetime.now(timezone.utc))
            )
            await session.execute(stmt)
            await session.commit()

        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notifications_mark_all_read(request: Request):
    """POST /api/notifications/read_all"""
    try:
        from models.odmgr_notifications import OdmgrNotification

        async with async_session_maker() as session:
            stmt = (
                update(OdmgrNotification)
                .where(OdmgrNotification.read == False)
                .values(read=True, read_at=datetime.now(timezone.utc))
            )
            await session.execute(stmt)
            await session.commit()

        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# ── Notification changes (diff a nivel de registro) ───────────────────────────

async def notification_changes_list(request: Request):
    """GET /api/notifications/{id}/changes?change_type=all"""
    notif_id = request.path_params.get("id", "")
    change_type = request.query_params.get("change_type", "all")

    try:
        from models.odmgr_notification_changes import OdmgrNotificationChange

        async with async_session_maker() as session:
            stmt = select(OdmgrNotificationChange).where(
                OdmgrNotificationChange.notification_id == notif_id
            )
            if change_type != "all":
                stmt = stmt.where(OdmgrNotificationChange.change_type == change_type)
            stmt = stmt.order_by(
                OdmgrNotificationChange.sort_order.asc().nullslast(),
                OdmgrNotificationChange.change_type.asc(),
            )
            result = await session.execute(stmt)
            changes = result.scalars().all()

        items = [
            {
                "id": str(c.id),
                "notification_id": str(c.notification_id),
                "change_type": c.change_type,
                "entity_id": c.entity_id,
                "entity_name": c.entity_name,
                "field_name": c.field_name,
                "old_value": c.old_value,
                "new_value": c.new_value,
                "status": c.status,
                "reviewed_at": c.reviewed_at.isoformat() if c.reviewed_at else None,
                "applied_at": c.applied_at.isoformat() if c.applied_at else None,
                "error_message": c.error_message,
            }
            for c in changes
        ]

        # Resumen por tipo
        summary = {
            "total": len(items),
            "alta": sum(1 for c in changes if c.change_type == "alta"),
            "baja": sum(1 for c in changes if c.change_type == "baja"),
            "modificacion": sum(1 for c in changes if c.change_type == "modificacion"),
            "pending": sum(1 for c in changes if c.status == "pending"),
            "accepted": sum(1 for c in changes if c.status == "accepted"),
            "rejected": sum(1 for c in changes if c.status == "rejected"),
        }

        return JSONResponse({"items": items, "summary": summary})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notification_change_review(request: Request):
    """POST /api/notifications/{id}/changes/{change_id}/accept  |  /reject"""
    notif_id  = request.path_params.get("id", "")
    change_id = request.path_params.get("change_id", "")
    action    = request.path_params.get("action", "")  # accept | reject

    if action not in ("accept", "reject"):
        return JSONResponse({"error": "invalid action"}, status_code=400)

    new_status = "accepted" if action == "accept" else "rejected"

    try:
        from models.odmgr_notification_changes import OdmgrNotificationChange

        async with async_session_maker() as session:
            stmt = (
                update(OdmgrNotificationChange)
                .where(
                    OdmgrNotificationChange.id == change_id,
                    OdmgrNotificationChange.notification_id == notif_id,
                )
                .values(status=new_status, reviewed_at=datetime.now(timezone.utc))
            )
            await session.execute(stmt)
            await session.commit()

        return JSONResponse({"status": "ok", "change_status": new_status})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notification_changes_review_all(request: Request):
    """POST /api/notifications/{id}/changes/accept_all  |  /reject_all"""
    notif_id = request.path_params.get("id", "")
    action   = request.path_params.get("bulk_action", "")  # accept_all | reject_all

    if action not in ("accept_all", "reject_all"):
        return JSONResponse({"error": "invalid action"}, status_code=400)

    new_status = "accepted" if action == "accept_all" else "rejected"

    try:
        from models.odmgr_notification_changes import OdmgrNotificationChange

        async with async_session_maker() as session:
            stmt = (
                update(OdmgrNotificationChange)
                .where(
                    OdmgrNotificationChange.notification_id == notif_id,
                    OdmgrNotificationChange.status == "pending",
                )
                .values(status=new_status, reviewed_at=datetime.now(timezone.utc))
            )
            result = await session.execute(stmt)
            await session.commit()

        return JSONResponse({"status": "ok", "updated": result.rowcount, "change_status": new_status})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notification_apply(request: Request):
    """
    POST /api/notifications/{id}/apply

    Aplica todos los cambios aceptados y hace soft-delete de la notificación.
    La lógica real de ETL (INSERT/UPDATE/soft_delete en SIPI) se conectará aquí.
    """
    notif_id = request.path_params.get("id", "")

    try:
        from models.odmgr_notifications import OdmgrNotification
        from models.odmgr_notification_changes import OdmgrNotificationChange

        now = datetime.now(timezone.utc)

        async with async_session_maker() as session:
            # Marcar cambios aceptados como applied
            stmt_changes = (
                update(OdmgrNotificationChange)
                .where(
                    OdmgrNotificationChange.notification_id == notif_id,
                    OdmgrNotificationChange.status == "accepted",
                )
                .values(status="applied", applied_at=now)
            )
            result = await session.execute(stmt_changes)
            applied_count = result.rowcount

            # Marcar notificación como tratada
            stmt_notif = (
                update(OdmgrNotification)
                .where(OdmgrNotification.id == notif_id)
                .values(status="applied")
            )
            await session.execute(stmt_notif)
            await session.commit()

        return JSONResponse({"status": "ok", "applied_changes": applied_count})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


async def notification_dismiss(request: Request):
    """POST /api/notifications/{id}/dismiss — descarta sin aplicar"""
    notif_id = request.path_params.get("id", "")

    try:
        from models.odmgr_notifications import OdmgrNotification

        async with async_session_maker() as session:
            stmt = (
                update(OdmgrNotification)
                .where(OdmgrNotification.id == notif_id)
                .values(status="dismissed")
            )
            await session.execute(stmt)
            await session.commit()

        return JSONResponse({"status": "ok"})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# App principal
application = Starlette(
    routes=[
        Route("/", docs_page),
        Route("/health", health),
        Route("/schema.graphql", export_schema),
        Route("/stats", schema_stats),
        Route("/odm_webhook", odm_webhook, methods=["POST"]),
        Route("/api/notifications", notifications_list, methods=["GET"]),
        Route("/api/notifications/unread_count", notifications_unread_count, methods=["GET"]),
        Route("/api/notifications/read_all", notifications_mark_all_read, methods=["POST"]),
        Route("/api/notifications/{id}/read", notification_mark_read, methods=["POST"]),
        # Cambios individuales (diff a nivel de registro)
        Route("/api/notifications/{id}/changes", notification_changes_list, methods=["GET"]),
        Route("/api/notifications/{id}/changes/{change_id}/{action}", notification_change_review, methods=["POST"]),
        Route("/api/notifications/{id}/apply", notification_apply, methods=["POST"]),
        Route("/api/notifications/{id}/dismiss", notification_dismiss, methods=["POST"]),
        Route("/api/notifications/{id}/{bulk_action}", notification_changes_review_all, methods=["POST"]),
        Mount("/graphql", app=graphql_handler, name="graphql"),
    ]
)

print("OK Starlette app inicializada")

import logging

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Logger específico para GraphQL
graphql_logger = logging.getLogger('app.graphql')
graphql_logger.setLevel(logging.INFO)
