from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql+asyncpg://localhost:5432/pai_a2a_hub"
    hub_name: str = "PAI A2A Hub"
    admin_api_key: str = ""
    cors_origins: list[str] = ["*"]
    task_expiry_interval_seconds: int = 300  # 5 minutes
    default_task_ttl_seconds: int = 3600  # 1 hour

    model_config = {"env_prefix": "", "env_file": ".env"}


settings = Settings()
