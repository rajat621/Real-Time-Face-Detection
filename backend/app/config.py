from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Real-Time Face Detection"
    environment: str = "development"
    database_url: str = ""
    frontend_origin: str = "http://localhost:3000"
    max_frame_size_bytes: int = 5 * 1024 * 1024
    ingest_rate_limit_per_second: int = 30
    default_stream_width: int = 1280
    default_stream_height: int = 720
    default_stream_background: str = "#101418"
    default_stream_text: str = "Waiting for camera"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
