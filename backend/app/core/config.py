"""
Centralized application configuration, loaded from environment variables (.env).
"""

from pathlib import Path

from pydantic_settings import BaseSettings

# config.py lives at backend/app/core/config.py
# Project root for this repository is the "backend" directory (three levels up)
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # backend directory
ENV_FILE_PATH = PROJECT_ROOT / ".env"


class Settings(BaseSettings):
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "raguser"
    mysql_password: str = "changeme"
    mysql_database: str = "codebase_rag"

    llm_api_key: str = ""
    llm_model: str = "gemini-3.6-flash"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
        )

    class Config:
        env_file = str(ENV_FILE_PATH)


settings = Settings()