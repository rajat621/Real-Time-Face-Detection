
from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from uuid import UUID

from PIL import Image
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.roi import ROIDetection
from app.schemas.roi import ROISchema
from app.services.detection import DetectionBox, detect_faces
from app.services.drawing import draw_face_box
from app.services.stream import StreamManager


class FrameDecodeError(ValueError):
    pass


class DatabaseUnavailableError(RuntimeError):
    pass


@dataclass(slots=True)
class ProcessedFrameResult:
    frame_bytes: bytes
    face_detected: bool
    confidence: float | None
    roi: ROISchema | None
    frame_index: int


def decode_jpeg(frame_bytes: bytes) -> Image.Image:
    try:
        image = Image.open(BytesIO(frame_bytes))
        return image.convert("RGB")
    except Exception as exc:  # pragma: no cover - Pillow raises several concrete exceptions
        raise FrameDecodeError("Malformed JPEG frame") from exc


async def _store_roi(
    session: AsyncSession,
    session_id: UUID,
    frame_index: int,
    box: DetectionBox,
    frame_width: int,
    frame_height: int,
) -> ROISchema:
    roi = ROIDetection(
        session_id=str(session_id),
        frame_index=frame_index,
        x_min=box.x_min,
        y_min=box.y_min,
        x_max=box.x_max,
        y_max=box.y_max,
        confidence=box.confidence,
        frame_width=frame_width,
        frame_height=frame_height,
    )
    session.add(roi)
    try:
        await session.commit()
        await session.refresh(roi)
    except SQLAlchemyError as exc:
        await session.rollback()
        raise DatabaseUnavailableError("Database unavailable") from exc
    return ROISchema.model_validate(roi)


async def process_frame(
    *,
    session: AsyncSession,
    stream_manager: StreamManager,
    session_id: UUID,
    frame_index: int,
    frame_bytes: bytes,
) -> ProcessedFrameResult:
    image = decode_jpeg(frame_bytes)
    detections = detect_faces(image)
    face_detected = bool(detections)
    confidence: float | None = detections[0].confidence if face_detected else None
    processed_image = image
    roi_schema: ROISchema | None = None

    if face_detected:
        box = detections[0]
        processed_image = draw_face_box(image, box)
        roi_schema = await _store_roi(
            session=session,
            session_id=session_id,
            frame_index=frame_index,
            box=box,
            frame_width=image.width,
            frame_height=image.height,
        )
    elif image:
        processed_image = image.copy()

    output = BytesIO()
    processed_image.save(output, format="JPEG", quality=90)
    processed_bytes = output.getvalue()

    await stream_manager.update_frame(
        session_id=session_id,
        frame_bytes=processed_bytes,
        status="face_detected" if face_detected else "no_face",
        confidence=confidence,
    )

    return ProcessedFrameResult(
        frame_bytes=processed_bytes,
        face_detected=face_detected,
        confidence=confidence,
        roi=roi_schema,
        frame_index=frame_index,
    )
