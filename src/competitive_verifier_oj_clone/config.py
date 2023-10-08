# Python Version: 3.x
import pathlib
import sys
from logging import getLogger
from typing import Any, Optional, TypedDict

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

logger = getLogger(__name__)


class OjVerifyConfig(TypedDict):
    languages: dict[str, Any]


_loaded_config: Optional[OjVerifyConfig] = None


def load(config_path: pathlib.Path) -> Optional[OjVerifyConfig]:
    if config_path.exists():
        with config_path.open("rb") as fp:
            return OjVerifyConfig(**tomli.load(fp))  # type:ignore
    return None


def set_config_path(config_path: pathlib.Path) -> None:
    global _loaded_config  # pylint: disable=invalid-name
    assert _loaded_config is None
    _loaded_config = load(config_path)
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
