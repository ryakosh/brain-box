import os
from pathlib import Path
from typing import Optional, Tuple, Type

from pydantic import BaseModel, Field
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

DIR_NAME = "brain_box"

_xdg_config_home = os.environ.get("XDG_CONFIG_HOME", os.path.expanduser("~/.config"))
XDG_CONFIG_PATH = Path(_xdg_config_home) / DIR_NAME / "brain_box.toml"
CWD_CONFIG_PATH = Path.cwd() / "brain_box.toml"

_xdg_data_home = os.environ.get("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
XDG_DATA_PATH = Path(_xdg_data_home) / DIR_NAME
DEFAULT_DB_PATH = XDG_DATA_PATH / "brain_box.db"


class General(BaseModel):
    """Configuration for general settings."""

    host: str = Field(default="127.0.0.1", description="Host to bind.")
    port: int = Field(default=8000, description="Port to bind.")
    cert: Optional[str] = Field(
        default=None, description="Path to the certificate file."
    )
    cert_key: Optional[str] = Field(
        default=None, description="Path to the certificate key file."
    )


class Database(BaseModel):
    """Configuration for database settings."""

    url: str = Field(
        default=f"sqlite:///{DEFAULT_DB_PATH}", description="Database connection URL."
    )


class Security(BaseModel):
    """Configuration for security settings."""

    username: str = Field(default="admin", description="Username.")
    hashed_password: Optional[str] = Field(
        default=None, description="Hashed password to password-protect the app."
    )
    token_secret: str = Field(
        default="CHANGE_TO_A_SECURE_SECRET", description="Secret for signing tokens."
    )
    token_ttl: int = Field(
        default=60 * 24 * 7, description="Token expiration in minutes."
    )


class Settings(BaseSettings):
    """Main settings for Brain Box.

    Priority Order (High to Low):
    1. Environment Variables (BRAINBOX_GENERAL__HOST)
    2. Local Directory TOML (./settings.toml)
    3. XDG User TOML (~/.config/brainbox/settings.toml)
    """

    general: General = General()
    database: Database = Database()
    security: Security = Security()

    model_config = SettingsConfigDict(
        env_prefix="BRAINBOX_",
        env_nested_delimiter="__",  # Use double underscore for nesting
        extra="ignore",  # Ignore unknown keys in config files
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Defines the priority of configuration loaders."""

        return (
            init_settings,
            env_settings,
            TomlConfigSettingsSource(settings_cls, CWD_CONFIG_PATH),
            TomlConfigSettingsSource(settings_cls, XDG_CONFIG_PATH),
        )


settings = Settings()
