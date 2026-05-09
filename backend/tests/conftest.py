# backend/tests/conftest.py
from httpx import ASGITransport

from app.main import app


def get_app_transport() -> ASGITransport:
    return ASGITransport(app=app)
