# backend/app/db/session.py
from collections.abc import AsyncIterator
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
import socket

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import AsyncEngine

from app.config import get_settings

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _local_sqlite_url() -> str:
    database_path = Path(__file__).resolve().parents[3] / "app.db"
    return f"sqlite+aiosqlite:///{database_path.as_posix()}"


def _host_is_resolvable(hostname: str | None, port: int | None) -> bool:
    if not hostname:
        return False
    try:
        socket.getaddrinfo(hostname, port or 0)
    except OSError:
        return False
    return True


@lru_cache(maxsize=1)
def get_database_url() -> str:
    database_url = get_settings().database_url.strip()
    if not database_url:
        return _local_sqlite_url()

    parsed = urlparse(database_url)
    if parsed.scheme.startswith("postgres") and not _host_is_resolvable(parsed.hostname, parsed.port):
        return _local_sqlite_url()

    return database_url


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            get_database_url(),
            echo=False,
            future=True,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _session_factory


async def get_async_session() -> AsyncIterator[AsyncSession]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        yield session
