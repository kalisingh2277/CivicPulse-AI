from datetime import UTC, datetime
from typing import Annotated
from uuid import UUID, uuid4

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, text

from app.api.deps import CurrentUser, require_roles
from app.core.db import SessionDep
from app.core.ratelimit import enforce_daily_complaint_limit
from app.models.complaint import Complaint, ComplaintMedia
from app.models.enums import ProcessingStatus, UserRole
from app.models.user import User
from app.schemas.complaint import (
    ComplaintCreate,
    ComplaintOut,
    MediaConfirmIn,
    MediaOut,
    MediaPresignIn,
    MediaPresignOut,
)
from app.schemas.geo import GeoPoint
from app.services import geo, storage

router = APIRouter(prefix="/complaints", tags=["complaints"])

CitizenUser = Annotated[User, Depends(require_roles(UserRole.citizen))]


async def _next_public_code(db: SessionDep) -> str:
    seq = (await db.execute(text("SELECT nextval('complaint_code_seq')"))).scalar_one()
    return f"CP-{datetime.now(UTC).year}-{seq:06d}"


async def _load_for_user(db: SessionDep, complaint_id: UUID, user: User) -> Complaint:
    complaint = await db.get(Complaint, complaint_id)
    # Citizens may only see their own; hide others' existence behind a 404.
    if complaint is None or (user.role == UserRole.citizen and complaint.citizen_id != user.id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "not_found", "message": "Complaint not found"},
        )
    return complaint


async def _media_out(db: SessionDep, complaint_id: UUID) -> list[MediaOut]:
    rows = (
        await db.execute(select(ComplaintMedia).where(ComplaintMedia.complaint_id == complaint_id))
    ).scalars()
    return [
        MediaOut(
            id=m.id,
            object_key=m.object_key,
            mime=m.mime,
            url=storage.presign_get(m.object_key),
            cv_status=m.cv_status,
        )
        for m in rows
    ]


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ComplaintOut)
async def create_complaint(
    body: ComplaintCreate, user: CitizenUser, db: SessionDep
) -> ComplaintOut:
    await enforce_daily_complaint_limit(str(user.id))
    lng, lat = body.location.lng, body.location.lat
    ward_id = await geo.find_ward(db, lng, lat)

    complaint = Complaint(
        public_code=await _next_public_code(db),
        citizen_id=user.id,
        description=body.description,
        location=geo.point(lng, lat),
        address_text=body.address_text,
        ward_id=ward_id,
        declined_intercept=body.declined_intercept,
        processing_status=ProcessingStatus.queued,
    )
    db.add(complaint)
    await db.commit()
    await db.refresh(complaint)

    # Day 5 wires the AI pipeline here: enqueue process_complaint(complaint.id)
    return ComplaintOut(
        id=complaint.id,
        public_code=complaint.public_code,
        description=complaint.description,
        address_text=complaint.address_text,
        ward_id=complaint.ward_id,
        processing_status=complaint.processing_status,
        issue_id=complaint.issue_id,
        location=GeoPoint(coordinates=(lng, lat)),
        created_at=complaint.created_at,
        media=[],
    )


@router.get("/mine", response_model=list[ComplaintOut])
async def my_complaints(user: CitizenUser, db: SessionDep) -> list[ComplaintOut]:
    rows = (
        await db.execute(
            text(
                """
                SELECT id, public_code, description, address_text, ward_id,
                       processing_status, issue_id, created_at,
                       ST_X(location::geometry) AS lng, ST_Y(location::geometry) AS lat
                FROM complaints
                WHERE citizen_id = :uid
                ORDER BY created_at DESC
                LIMIT 100
                """
            ),
            {"uid": user.id},
        )
    ).mappings()
    return [
        ComplaintOut(
            id=r["id"],
            public_code=r["public_code"],
            description=r["description"],
            address_text=r["address_text"],
            ward_id=r["ward_id"],
            processing_status=r["processing_status"],
            issue_id=r["issue_id"],
            location=GeoPoint(coordinates=(r["lng"], r["lat"])),
            created_at=r["created_at"],
        )
        for r in rows
    ]


@router.get("/{complaint_id}", response_model=ComplaintOut)
async def get_complaint(complaint_id: UUID, user: CurrentUser, db: SessionDep) -> ComplaintOut:
    complaint = await _load_for_user(db, complaint_id, user)
    coords = (
        await db.execute(
            text(
                "SELECT ST_X(location::geometry), ST_Y(location::geometry) "
                "FROM complaints WHERE id = :id"
            ),
            {"id": complaint_id},
        )
    ).first()
    return ComplaintOut(
        id=complaint.id,
        public_code=complaint.public_code,
        description=complaint.description,
        address_text=complaint.address_text,
        ward_id=complaint.ward_id,
        processing_status=complaint.processing_status,
        issue_id=complaint.issue_id,
        location=GeoPoint(coordinates=(coords[0], coords[1])),
        created_at=complaint.created_at,
        media=await _media_out(db, complaint_id),
    )


@router.post("/{complaint_id}/media/presign", response_model=MediaPresignOut)
async def presign_media(
    complaint_id: UUID, body: MediaPresignIn, user: CitizenUser, db: SessionDep
) -> MediaPresignOut:
    await _load_for_user(db, complaint_id, user)
    if body.mime not in storage.ALLOWED_MIME:
        raise HTTPException(
            status_code=422,
            detail={"code": "bad_mime", "message": "Only JPEG, PNG, or WebP images"},
        )
    if body.bytes > storage.MAX_BYTES:
        raise HTTPException(
            status_code=422,
            detail={"code": "too_large", "message": "Image exceeds 8 MB"},
        )
    existing = (
        await db.execute(
            select(func.count())
            .select_from(ComplaintMedia)
            .where(ComplaintMedia.complaint_id == complaint_id)
        )
    ).scalar_one()
    if existing >= 3:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={"code": "media_limit", "message": "Max 3 photos per complaint"},
        )
    ext = storage.ALLOWED_MIME[body.mime]
    object_key = f"complaints/{complaint_id}/{uuid4().hex}.{ext}"
    return MediaPresignOut(
        upload_url=storage.presign_put(object_key, body.mime), object_key=object_key
    )


@router.post("/{complaint_id}/media/confirm", response_model=MediaOut)
async def confirm_media(
    complaint_id: UUID, body: MediaConfirmIn, user: CitizenUser, db: SessionDep
) -> MediaOut:
    await _load_for_user(db, complaint_id, user)
    if not body.object_key.startswith(f"complaints/{complaint_id}/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "bad_key", "message": "object_key does not belong to this complaint"},
        )
    try:
        meta = await storage.head(body.object_key)
    except ClientError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "upload_missing", "message": "Upload not found in storage"},
        ) from e
    size = int(meta["ContentLength"])
    if size > storage.MAX_BYTES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": "too_large", "message": "Uploaded file exceeds 8 MB"},
        )

    media = ComplaintMedia(
        complaint_id=complaint_id,
        object_key=body.object_key,
        mime=body.mime,
        bytes=size,
        width=body.width,
        height=body.height,
    )
    db.add(media)
    await db.commit()
    await db.refresh(media)

    # Day 5 wires CV here: enqueue analyze_media(media.id)
    return MediaOut(
        id=media.id,
        object_key=media.object_key,
        mime=media.mime,
        url=storage.presign_get(media.object_key),
        cv_status=media.cv_status,
    )
