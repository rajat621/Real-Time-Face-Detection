
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.models.roi import ROIDetection
from app.schemas.roi import ROIListResponse, ROISchema

router = APIRouter(tags=["roi"])


@router.get("/roi", response_model=ROIListResponse)
async def list_rois(
    session_id: UUID = Query(...),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    session: AsyncSession = Depends(get_async_session),
):
    try:
        total_result = await session.execute(
            select(func.count()).select_from(ROIDetection).where(ROIDetection.session_id == str(session_id))
        )
        total = int(total_result.scalar_one())
        query = (
            select(ROIDetection)
            .where(ROIDetection.session_id == str(session_id))
            .order_by(ROIDetection.timestamp.desc(), ROIDetection.id.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await session.execute(query)
        items = [ROISchema.model_validate(row) for row in result.scalars().all()]
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Database unavailable") from exc

    return ROIListResponse(session_id=session_id, limit=limit, offset=offset, total=total, items=items)
