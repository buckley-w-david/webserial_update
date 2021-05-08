import os
from typing import Any, List, Dict

import toml
from pydantic import (
    BaseSettings,
    FilePath,
    HttpUrl
)

def toml_config_settings_source(settings: BaseSettings) -> Dict[str, Any]:
    """
    A simple settings source that loads variables from a TOML file
    """
    with open(os.environ.get('WEBSERIAL_UPDATE_CONFIG', 'config.toml'), 'r') as f:
        return toml.load(f)


class Settings(BaseSettings):
    calibre_library: str
    calibre_username: str
    calibre_password: str
    urls: FilePath

    class Config:
        env_prefix = 'WEBSERIAL_UPDATE_'
        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                env_settings,
                toml_config_settings_source,
                file_secret_settings,
            )

