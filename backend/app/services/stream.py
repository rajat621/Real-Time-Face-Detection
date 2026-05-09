
from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from io import BytesIO
from uuid import UUID

from PIL import Image, ImageDraw, ImageFont

from app.config import get_settings


JPEG_BOUNDARY = b"--frame\r\n"
JPEG_HEADER = b"Content-Type: image/jpeg\r\n\r\n"
JPEG_SUFFIX = b"\r\n"


@dataclass(slots=True)
class SessionStreamState:
    latest_frame: bytes | None = None
    latest_status: str = "no_face"
    latest_confidence: float | None = None
    last_frame_index: int = 0
    frame_timestamps: deque[float] = field(default_factory=deque)
    condition: asyncio.Condition = field(default_factory=asyncio.Condition)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class RateLimitExceeded(RuntimeError):
    pass


class StreamManager:
    def __init__(self) -> None:
        self._sessions: dict[UUID, SessionStreamState] = {}
        self._sessions_lock = asyncio.Lock()

    async def _get_state(self, session_id: UUID) -> SessionStreamState:
        async with self._sessions_lock:
            state = self._sessions.get(session_id)
            if state is None:
                state = SessionStreamState()
                self._sessions[session_id] = state
            return state

    async def next_frame_index(self, session_id: UUID) -> int:
        state = await self._get_state(session_id)
        async with state.lock:
            state.last_frame_index += 1
            return state.last_frame_index

    async def enforce_rate_limit(self, session_id: UUID) -> None:
        state = await self._get_state(session_id)
        async with state.lock:
            now = time.monotonic()
            window_start = now - 1.0
            while state.frame_timestamps and state.frame_timestamps[0] < window_start:
                state.frame_timestamps.popleft()
            if len(state.frame_timestamps) >= get_settings().ingest_rate_limit_per_second:
                raise RateLimitExceeded("Frame rate limit exceeded")
            state.frame_timestamps.append(now)

    async def update_frame(
        self,
        session_id: UUID,
        frame_bytes: bytes,
        status: str,
        confidence: float | None,
    ) -> None:
        state = await self._get_state(session_id)
        async with state.condition:
            state.latest_frame = frame_bytes
            state.latest_status = status
            state.latest_confidence = confidence
            state.condition.notify_all()

    async def frame_iterator(self, session_id: UUID):
        placeholder = await self._placeholder_frame()
        last_seen: bytes | None = None

        while True:
            state = await self._get_state(session_id)
            async with state.condition:
                if state.latest_frame is None or state.latest_frame == last_seen:
                    try:
                        await asyncio.wait_for(state.condition.wait(), timeout=0.5)
                    except TimeoutError:
                        yield JPEG_BOUNDARY + JPEG_HEADER + placeholder + JPEG_SUFFIX
                        continue

                frame_bytes = state.latest_frame or placeholder
                last_seen = frame_bytes

            yield JPEG_BOUNDARY + JPEG_HEADER + frame_bytes + JPEG_SUFFIX

    async def _placeholder_frame(self) -> bytes:
        settings = get_settings()
        image = Image.new(
            "RGB",
            (settings.default_stream_width, settings.default_stream_height),
            settings.default_stream_background,
        )
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default()
        message = settings.default_stream_text
        text_bbox = draw.textbbox((0, 0), message, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        x = (image.width - text_width) // 2
        y = (image.height - text_height) // 2
        draw.text((x, y), message, fill=(230, 235, 240), font=font)
        output = BytesIO()
        image.save(output, format="JPEG", quality=90)
        return output.getvalue()
