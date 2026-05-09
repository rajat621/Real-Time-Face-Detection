from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.db.base import Base
from app.db.session import get_database_url, get_engine
from app.routers.feed import router as feed_router
from app.routers.roi import router as roi_router
from app.services.stream import StreamManager

settings = get_settings()
stream_manager = StreamManager()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.state.stream_manager = stream_manager
    app.include_router(feed_router)
    app.include_router(roi_router)

    @app.on_event("startup")
    async def initialize_local_storage() -> None:
        database_url = get_database_url()
        if database_url.startswith("sqlite"):
            async with get_engine().begin() as connection:
                await connection.run_sync(Base.metadata.create_all)

    return app


app = create_app()
