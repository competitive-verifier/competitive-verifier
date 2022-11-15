# Python Version: 3.x
import pathlib
from logging import getLogger
from typing import Any, Optional, TypedDict

import toml

logger = getLogger(__name__)


class OjVerifyConfig(TypedDict):
    languages: dict[str, Any]


_loaded_config: Optional[OjVerifyConfig] = None


def _load(config_path: pathlib.Path) -> Optional[OjVerifyConfig]:
    if config_path.exists():
        return OjVerifyConfig(**toml.load(str(config_path)))
    return None


def set_config_path(config_path: pathlib.Path) -> None:
    global _loaded_config  # pylint: disable=invalid-name
    assert _loaded_config is None
    _loaded_config = _load(config_path)
    if _loaded_config is None:
        _loaded_config = OjVerifyConfig(languages={})
        logger.info("no config file")
    else:
        logger.info("config file loaded: %s: %s", str(config_path), _loaded_config)


def get_config() -> OjVerifyConfig:
    global _loaded_config  # pylint: disable=invalid-name
    if _loaded_config is None:
        # Use default config
        _loaded_config = OjVerifyConfig(languages={})
    return _loaded_config
