from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ROISchema(BaseModel):
    id: int
    session_id: UUID
    frame_index: int
    timestamp: datetime
    x_min: int
    y_min: int
    x_max: int
    y_max: int
    width: int | None = None
    height: int | None = None
    confidence: float | None = None
    frame_width: int | None = None
    frame_height: int | None = None

    model_config = ConfigDict(from_attributes=True)


class ROIListResponse(BaseModel):
    session_id: UUID
    limit: int
    offset: int
    total: int
    items: list[ROISchema] = Field(default_factory=list)
