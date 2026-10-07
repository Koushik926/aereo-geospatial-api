"""Application configuration via pydantic-settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./aereo.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    UPLOAD_DIR: str = "/tmp/aereo_uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = [".kml", ".zip"]
    CRS_DEFAULT: str = "EPSG:4326"
    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


settings = Settings()
