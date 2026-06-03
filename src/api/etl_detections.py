"""
API endpoints para detecciones de inmuebles religiosos
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from ..db.connection import get_db
from sipi_core.models.discovery import DeteccionAnuncio as Deteccion

router = APIRouter(prefix="/api/etl/detecciones", tags=["detecciones"])


@router.get("/weekly")
async def get_weekly_detections(
    db: AsyncSession = Depends(get_db),
    limit: int = Query(10, le=50)
):
    """
    Obtiene detecciones de la última semana
    """
    one_week_ago = datetime.now() - timedelta(days=7)
    
    # Query para detecciones de esta semana
    query = (
        select(Deteccion)
        .where(Deteccion.first_detected_at >= one_week_ago)
        .order_by(Deteccion.score.desc(), Deteccion.first_detected_at.desc())
        .limit(limit)
    )
    
    result = await db.execute(query)
    detections = result.scalars().all()
    
    # Count total
    count_query = (
        select(func.count(Deteccion.id))
        .where(Deteccion.first_detected_at >= one_week_ago)
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    return {
        "total": total,
        "items": [
            {
                "id": d.id,
                "titulo": d.inmueble_raw.titulo if d.inmueble_raw else None,
                "score": float(d.score),
                "status": d.status,
                "evidences": d.evidences,
                "detected_at": d.first_detected_at.isoformat()
            }
            for d in detections
        ]
    }