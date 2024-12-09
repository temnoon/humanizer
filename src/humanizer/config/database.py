# src/humanizer/config/database.py
from pydantic import BaseModel
from enum import Enum

class DatabaseRole(Enum):
    ADMIN = "humanizer_admin"
    APP = "humanizer_app"
    READONLY = "humanizer_readonly"
    BACKUP = "humanizer_backup"

class DatabaseConfig(BaseModel):
    host: str = "localhost"
    port: int = 5432
    database: str = "humanizer"
    role: DatabaseRole
    user: str = "postgres"
    password: str = "postgres"

    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @property
    def asyncpg_url(self) -> str:
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

class DatabaseConfigs:
    """Database configurations for different roles"""

    @property
    def admin(self) -> DatabaseConfig:
        return DatabaseConfig(
            role=DatabaseRole.ADMIN,
            user="humanizer_admin",
            password="admin_pass"  # Use environment variables in production
        )

    @property
    def app(self) -> DatabaseConfig:
        return DatabaseConfig(
            role=DatabaseRole.APP,
            user="humanizer_app",
            password="app_pass"
        )

    @property
    def readonly(self) -> DatabaseConfig:
        return DatabaseConfig(
            role=DatabaseRole.READONLY,
            user="humanizer_readonly",
            password="read_pass"
        )
