from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    APP_NAME: str = Field(default="i9 Smart Campaigns API")
    APP_VERSION: str = Field(default="1.0.0")
    DEBUG: bool = Field(default=True)
    ENVIRONMENT: str = Field(default="development")

    # Server
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)

    # Database
    DATABASE_URL: str

    # Auth / API Keys
    API_KEY_TABLETS: str = Field(default="i9smart_campaigns_readonly_2025")
    JWT_SECRET_KEY: str = Field(default="jwt-secret-key-change-in-production-2025")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRATION_MINUTES: int = Field(default=1440)

    # CORS / Cache / Storage
    CORS_ORIGINS: str = Field(default="*")
    REDIS_URL: str = Field(default="redis://localhost:6379/0")
    MINIO_ENDPOINT: str = Field(default="localhost:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin")
    MINIO_BUCKET: str = Field(default="campaigns")
    MINIO_SECURE: bool = Field(default=False)

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()  # type: ignore[call-arg]
