from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CareerPilot AI API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/career_pilot"
    OPENAI_API_KEY: str | None = None
    MCP_CORE_SERVER_URL: str = "http://localhost:8001/mcp"
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
