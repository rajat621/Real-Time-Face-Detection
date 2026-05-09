
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, WebSocket, WebSocketDisconnect, status
import logging
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_session
from app.services.processing import DatabaseUnavailableError, FrameDecodeError, process_frame
from app.services.stream import RateLimitExceeded, StreamManager

router = APIRouter(prefix="/feed", tags=["feed"])

logger = logging.getLogger("feed")


def get_http_stream_manager(request: Request) -> StreamManager:
    return request.app.state.stream_manager


def get_websocket_stream_manager(websocket: WebSocket) -> StreamManager:
    return websocket.app.state.stream_manager


def parse_session_id(session_id: str) -> UUID:
    try:
        return UUID(session_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid session_id") from exc


@router.post("/ingest")
async def ingest_frame_http(
    request: Request,
    session: AsyncSession = Depends(get_async_session),
    stream_manager: StreamManager = Depends(get_http_stream_manager),
    session_id: str = Query(...),
):
    session_uuid = parse_session_id(session_id)
    frame = await request.body()
    if len(frame) > 5 * 1024 * 1024:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Frame exceeds 5 MB")
    try:
        logger.info("HTTP ingest: session=%s frame_size=%d", session_uuid, len(frame))
        await stream_manager.enforce_rate_limit(session_uuid)
        frame_index = await stream_manager.next_frame_index(session_uuid)
        result = await process_frame(
            session=session,
            stream_manager=stream_manager,
            session_id=session_uuid,
            frame_index=frame_index,
            frame_bytes=frame,
        )
    except RateLimitExceeded as exc:
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail=str(exc)) from exc
    except FrameDecodeError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except DatabaseUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    if not result.face_detected:
        logger.info("HTTP ingest: session=%s frame_index=%s no face", session_uuid, frame_index)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    logger.info("HTTP ingest: session=%s frame_index=%s face=%s confidence=%s", session_uuid, result.frame_index, result.face_detected, result.confidence)
    return {
        "status": "face_detected",
        "session_id": str(session_uuid),
        "frame_index": result.frame_index,
        "confidence": result.confidence,
        "roi_saved": True,
    }


@router.websocket("/ingest")
async def ingest_frame_websocket(
    websocket: WebSocket,
    session: AsyncSession = Depends(get_async_session),
    stream_manager: StreamManager = Depends(get_websocket_stream_manager),
):
    session_id = websocket.query_params.get("session_id")
    if session_id is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="session_id is required")
        return
    try:
        session_uuid = parse_session_id(session_id)
    except HTTPException:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid session_id")
        return

    await websocket.accept()
    logger.info("WS accepted: client=%s session=%s", websocket.client, session_id)
    try:
        while True:
            frame = await websocket.receive_bytes()
            logger.debug("WS recv: session=%s bytes=%d", session_uuid, len(frame))
            if len(frame) > 5 * 1024 * 1024:
                await websocket.send_json({"status": "error", "detail": "Frame exceeds 5 MB"})
                continue
            try:
                await stream_manager.enforce_rate_limit(session_uuid)
                frame_index = await stream_manager.next_frame_index(session_uuid)
                result = await process_frame(
                    session=session,
                    stream_manager=stream_manager,
                    session_id=session_uuid,
                    frame_index=frame_index,
                    frame_bytes=frame,
                )
            except RateLimitExceeded:
                await websocket.send_json({"status": "error", "detail": "Frame rate limit exceeded"})
                continue
            except FrameDecodeError:
                await websocket.send_json({"status": "error", "detail": "Malformed JPEG frame"})
                continue
            except DatabaseUnavailableError:
                await websocket.send_json({"status": "error", "detail": "Database unavailable"})
                continue

            payload = {
                "status": "face_detected" if result.face_detected else "no_face",
                "session_id": str(session_uuid),
                "frame_index": result.frame_index,
                "confidence": result.confidence,
            }
            logger.debug("WS send: session=%s payload=%s", session_uuid, payload)
            await websocket.send_json(payload)
    except WebSocketDisconnect:
        logger.info("WS disconnect: session=%s", session_id)
        return


@router.get("/stream")
async def stream_feed(
    stream_manager: StreamManager = Depends(get_http_stream_manager),
    session_id: str = Query(...),
):
    session_uuid = parse_session_id(session_id)

    async def streamer():
        async for chunk in stream_manager.frame_iterator(session_uuid):
            yield chunk

    return StreamingResponse(streamer(), media_type="multipart/x-mixed-replace; boundary=frame")
