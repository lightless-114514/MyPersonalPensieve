import os
import sys
from pathlib import Path
from pydantic_settings import BaseSettings


def _default_data_dir() -> str:
    """返回桌面端数据目录。

    优先顺序：
    1. 环境变量 PENSIEVE_DATA_DIR（开发/打包后由 Electron 注入）
    2. 打包模式下：可执行文件同级目录的 data 文件夹
    3. 开发模式下：backend/data
    """
    env = os.environ.get("PENSIEVE_DATA_DIR")
    if env:
        return str(Path(env).expanduser().resolve())

    if getattr(sys, "frozen", False):
        # PyInstaller 打包后：可执行文件同级目录
        return str(Path(sys.executable).parent / "data")

    return str(Path(__file__).resolve().parent.parent / "data")


class Settings(BaseSettings):
    # Application
    app_name: str = "pensieve-backend"
    server_port: int = 8080
    server_host: str = "127.0.0.1"
    debug: bool = False

    # Data directory（桌面端统一数据存放位置）
    data_dir: str = _default_data_dir()

    # SQLite（替代 MySQL）
    sqlite_path: str = ""  # 留空则使用 data_dir/pensieve.db

    @property
    def database_url(self) -> str:
        """异步 SQLAlchemy URL。"""
        path = self.sqlite_path or str(Path(self.data_dir) / "pensieve.db")
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        return f"sqlite+aiosqlite:///{path}"

    @property
    def database_url_sync(self) -> str:
        """同步 SQLAlchemy URL（alembic 使用）。"""
        path = self.sqlite_path or str(Path(self.data_dir) / "pensieve.db")
        Path(self.data_dir).mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{path}"

    # ChromaDB（替代 Qdrant）
    chroma_persist_dir: str = ""  # 留空则使用 data_dir/chroma
    chroma_collection_name: str = "pensieve_memories"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Upload
    upload_dir: str = ""  # 留空则使用 data_dir/uploads

    @property
    def upload_dir_resolved(self) -> str:
        if self.upload_dir:
            return self.upload_dir
        return str(Path(self.data_dir) / "uploads")

    # CORS
    cors_origins: list[str] = ["*"]

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()
