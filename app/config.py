import os
import tomllib
from pathlib import Path

from pydantic import Field, PositiveInt
from pydantic_settings import (
    AWSSecretsManagerSettingsSource,
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
)


def get_app_version() -> str:
    """Simple getter for version in pyproject.toml.

    If you need to load multiple attributes from it, see:
    https://docs.pydantic.dev/latest/concepts/pydantic_settings/#pyprojecttoml
    """
    with Path('pyproject.toml').open('rb') as f:
        content = tomllib.load(f)

    return content['project']['version']


class Settings(BaseSettings):
    """Application settings.

    Will be read from multiple sources. Case-insensitive.
    See: https://docs.pydantic.dev/latest/concepts/pydantic_settings/
    """

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        """Add custom sources to settings queue.

        The order of the returned callables decides the priority of inputs;
        first item is the highest priority.
        """
        sources = [
            init_settings,
            env_settings,
            dotenv_settings,
            file_secret_settings,
        ]

        return tuple(sources)

    model_config = SettingsConfigDict()

    env: str = Field(default='')

    pgsql_host: str = Field(default='localhost')
    pgsql_port: int = Field(default=5432)
    pgsql_user: str = Field(default='postgres')
    pgsql_password: str = Field(default='postgres')
    pgsql_db_name: str = Field(default='postgres_capstone')

    app_main_version: str = Field(default='1')
    app_version: str = get_app_version()
    app_name: str = Field(default='Capstone API')



settings = Settings()  # type: ignore
