# Python Version: 3.x
import pathlib
from logging import getLogger
from typing import *

import toml

logger = getLogger(__name__)

default_config_path_cv = pathlib.Path(".competitive-verifier/config.toml")
default_config_path = pathlib.Path(".verify-helper/config.toml")

_loaded_config: Optional[Dict[str, Any]] = None


def _load(config_path: pathlib.Path) -> Optional[Dict[str, Any]]:
    if config_path.exists():
        return dict(toml.load(str(config_path)))
    return None


def set_config_path(config_path: pathlib.Path) -> None:
    global _loaded_config  # pylint: disable=invalid-name
    assert _loaded_config is None
    _loaded_config = _load(default_config_path_cv) or _load(default_config_path)
    if _loaded_config is None:
        _loaded_config = {}
        logger.info("no config file")
    else:
        logger.info("config file loaded: %s: %s", str(config_path), _loaded_config)


def get_config() -> Dict[str, Any]:
    if _loaded_config is None:
        set_config_path(default_config_path)
    assert _loaded_config is not None
    return _loaded_config
