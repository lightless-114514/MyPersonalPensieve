from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Application
    app_name: str = "pensieve-backend"
    server_port: int = 8080
    debug: bool = False

    # MySQL
    mysql_host: str = "localhost"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "sdfof2005"
    mysql_database: str = "pensieve"

    @property
    def database_url(self) -> str:
        return (
            f"mysql+asyncmy://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379

    # Qdrant
    qdrant_host: str = "localhost"
    qdrant_port: int = 6334
    qdrant_collection_name: str = "pensieve_memories"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Upload
    upload_dir: str = "./uploads"

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
