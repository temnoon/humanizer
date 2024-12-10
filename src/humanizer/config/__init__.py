# src/humanizer/config/__init__.py
from pydantic import BaseModel, Field
from pathlib import Path
from typing import Optional

class Settings(BaseModel):
    humanizer_db_host: str = Field(title="DB Host", default="localhost", description="Database host")
    humanizer_db_port: str = Field(title="DB Port", default="5432", description="Database port")
    humanizer_db_name: str = Field(title="DB Name", default="humanizer", description="Database name")
    postgres_key: Optional[str] = Field(title="Postgres Key", default=None, description="Postgres encryption key")
    postgres_password_encrypted: Optional[str] = Field(title="Encrypted Password", default=None, description="Encrypted postgres password")

    # Application settings
    ollama_base_url: str = Field(title="Ollama URL", default="http://localhost:11434", description="Ollama API base URL")
    embedding_model: str = Field(title="Model", default="nomic-embed-text", description="Embedding model name")
    embedding_dimensions: int = Field(title="Dimensions", default=512, description="Embedding dimensions")

    # Logging
    humanizer_log_level: str = Field(title="Log Level", default="INFO", description="Logging level")

    # Paths
    config_path: Path = Field(
        title="Config Path",
        default=Path("~/.humanizer/config.json").expanduser(),
        description="Path to config file"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "allow"

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://postgres:postgres@{self.humanizer_db_host}:{self.humanizer_db_port}/{self.humanizer_db_name}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        from humanizer.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.debug(f"Loading settings from env file: {self.Config.env_file}")
        logger.debug(f"Embedding model: {self.embedding_model}")
        logger.debug(f"Embedding dimensions: {self.embedding_dimensions}")

_settings: Optional[Settings] = None

def load_config(config_path: Optional[str | Path] = None) -> Settings:
    """Load configuration from file"""
    global _settings
    if config_path:
        _settings = Settings(config_path=Path(config_path))
    return _settings or Settings()

def get_settings() -> Settings:
    """Get current settings"""
    global _settings
    if _settings is None:
        _settings = Settings(_env_file=".env")
    return _settings

def update_config(key: str, value: str):
    """Update configuration value"""
    settings = get_settings()
    if hasattr(settings, key):
        setattr(settings, key, value)
    else:
        raise ValueError(f"Unknown configuration key: {key}")
