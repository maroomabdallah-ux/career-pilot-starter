from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CareerPilot AI API"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/career_pilot"
    JWT_SECRET_KEY: str = "development-only-change-me-at-least-32-bytes"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 14
    FRONTEND_URL: str = "http://localhost:5173"
    REFRESH_COOKIE_NAME: str = "careerpilot_refresh"
    ENABLE_LEGACY_CRUD_ROUTES: bool = False
    OPENAI_API_KEY: str | None = None
    PROFILE_AGENT_MODEL: str = "gpt-4.1-mini"
    RESUME_AGENT_MODEL: str = "gpt-4.1-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"
    MCP_CORE_SERVER_URL: str = "http://localhost:8001/mcp"
    MCP_AUTH_ISSUER_URL: str = "http://localhost:8000"
    MCP_HOST: str = "127.0.0.1"
    MCP_PORT: int = 8001
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
