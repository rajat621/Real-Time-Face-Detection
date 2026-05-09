# backend/app/models/roi.py
from datetime import datetime

from sqlalchemy import Computed, DateTime, Float, Index, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ROIDetection(Base):
    __tablename__ = "roi_detections"
    __table_args__ = (
        Index("idx_roi_session", "session_id"),
        Index("idx_roi_timestamp", "timestamp"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(36), nullable=False)
    frame_index: Mapped[int] = mapped_column(Integer, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    x_min: Mapped[int] = mapped_column(Integer, nullable=False)
    y_min: Mapped[int] = mapped_column(Integer, nullable=False)
    x_max: Mapped[int] = mapped_column(Integer, nullable=False)
    y_max: Mapped[int] = mapped_column(Integer, nullable=False)
    width: Mapped[int] = mapped_column(Computed("x_max - x_min", persisted=True))
    height: Mapped[int] = mapped_column(Computed("y_max - y_min", persisted=True))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    frame_width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    frame_height: Mapped[int | None] = mapped_column(Integer, nullable=True)
