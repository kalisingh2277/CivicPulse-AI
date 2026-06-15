from datetime import date
from typing import Annotated

from fastapi import APIRouter, Query

from app.api.deps import AdminUser, StaffUser
from app.core.db import SessionDep
from app.schemas.analytics import DepartmentRow, HeatCell, TrendPoint
from app.services import analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/heatmap", response_model=list[HeatCell])
async def heatmap(
    _: StaffUser,
    db: SessionDep,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: int | None = None,
) -> list[HeatCell]:
    cells = await analytics.heatmap(
        db, date_from=date_from, date_to=date_to, category_id=category_id
    )
    return [HeatCell(**c) for c in cells]


@router.get("/trends", response_model=list[TrendPoint])
async def trends(
    _: StaffUser,
    db: SessionDep,
    ward_id: int | None = None,
    category_id: int | None = None,
    weeks: Annotated[int, Query(ge=1, le=104)] = 26,
) -> list[TrendPoint]:
    rows = await analytics.trends(db, ward_id=ward_id, category_id=category_id, weeks=weeks)
    return [TrendPoint(**r) for r in rows]


@router.get("/departments", response_model=list[DepartmentRow])
async def departments(_: AdminUser, db: SessionDep) -> list[DepartmentRow]:
    rows = await analytics.department_performance(db)
    return [DepartmentRow(**r) for r in rows]
