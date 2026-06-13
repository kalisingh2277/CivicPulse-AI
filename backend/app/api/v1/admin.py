from typing import Annotated

from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.core.db import SessionDep
from app.models.enums import UserRole
from app.models.user import User
from app.schemas.ward import WardImportRequest, WardImportResult
from app.services import wards as ward_service

router = APIRouter(prefix="/admin", tags=["admin"])

AdminUser = Annotated[User, Depends(require_roles(UserRole.admin))]


@router.post("/wards/import", response_model=WardImportResult)
async def import_wards(body: WardImportRequest, _: AdminUser, db: SessionDep) -> WardImportResult:
    n = await ward_service.import_feature_collection(
        db,
        body.feature_collection,
        code_prop=body.code_prop,
        name_prop=body.name_prop,
        zone_prop=body.zone_prop,
    )
    return WardImportResult(imported=n)
