import logging

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Astro Agent API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"

    # CORS
    BACKEND_CORS_ORIGINS: list[str] = ["*"]

    # Server
    HOST: str = "0.0.0.0"  # noqa: S104
    PORT: int = 4219
    LOG_LEVEL: str = "INFO"

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Gemini API
    GEMINI_API_KEY: str = ""
    GEMINI_FILE_SEARCH_STORE_NAME: str = ""

    model_config = SettingsConfigDict(
        env_file=(".env", ".env.local"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )


settings = Settings()

# Configure Logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("api")
