from pydantic import BaseSettings, Field
from pathlib import Path
    humanizer_db_port: str = Field(default="5432", env="HUMANIZER_DB_PORT")
    humanizer_db_name: str = Field(default="humanizer", env="HUMANIZER_DB_NAME")
    postgres_key: str | None = Field(default=None, env="POSTGRES_KEY")
    postgres_password_encrypted: str | None = Field(default=None, env="POSTGRES_PASSWORD_ENCRYPTED")

    # Application settings
    ollama_base_url: str = Field(default="http://localhost:11434", env="OLLAMA_BASE_URL")
    embedding_model: str = Field(default="nomic-embed-text", env="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=512, env="EMBEDDING_DIMENSIONS")  # Default to 512 for Matryoshka

    # Logging
    humanizer_log_level: str = Field(default="INFO", env="HUMANIZER_LOG_LEVEL")

    # Paths
    config_path: Path = Field(
        default=Path("~/.humanizer/config.json").expanduser(),
        env="HUMANIZER_CONFIG"
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"  # Allow extra fields from env
    )

    @property
    def database_url(self) -> str:
        return f"postgresql+asyncpg://postgres:postgres@{self.humanizer_db_host}:{self.humanizer_db_port}/{self.humanizer_db_name}"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Add debug logging for environment variable loading
        from humanizer.utils.logging import get_logger
        logger = get_logger(__name__)
        logger.debug(f"Loading settings from env file: {self.model_config['env_file']}")
        logger.debug(f"Embedding model: {self.embedding_model}")
        logger.debug(f"Embedding dimensions: {self.embedding_dimensions}")

_settings = None

def load_config(config_path: str | Path = None):
    """Load configuration from file"""
    global _settings
    if config_path:
        _settings = Settings(config_path=Path(config_path))
    return _settings

def get_settings() -> Settings:
    """Get current settings"""
    global _settings
    if _settings is None:
        _settings = Settings(_env_file=".env")  # Explicitly specify env file
    return _settings

def update_config(key: str, value: str):
    """Update configuration value"""
    settings = get_settings()
    if hasattr(settings, key):
        setattr(settings, key, value)
    else:
        raise ValueError(f"Unknown configuration key: {key}")
