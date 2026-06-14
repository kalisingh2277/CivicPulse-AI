from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.enums import ProcessingStatus
from app.schemas.geo import GeoPoint


class ComplaintCreate(BaseModel):
    description: str = Field(min_length=5, max_length=2000)
    location: GeoPoint
    address_text: str | None = Field(default=None, max_length=300)
    declined_intercept: bool = False


class MediaPresignIn(BaseModel):
    mime: str
    bytes: int = Field(gt=0)


class MediaPresignOut(BaseModel):
    upload_url: str
    object_key: str


class MediaConfirmIn(BaseModel):
    object_key: str
    mime: str
    width: int | None = None
    height: int | None = None


class MediaOut(BaseModel):
    id: UUID
    object_key: str
    mime: str
    url: str
    cv_status: str


class ComplaintOut(BaseModel):
    id: UUID
    public_code: str
    description: str
    address_text: str | None
    ward_id: int | None
    processing_status: ProcessingStatus
    issue_id: UUID | None
    # The citizen tracks the *issue's* status once their complaint is triaged.
    issue_status: str | None = None
    issue_public_code: str | None = None
    location: GeoPoint
    created_at: datetime
    media: list[MediaOut] = []
