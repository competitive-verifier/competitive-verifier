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


def load(config_path: Optional[pathlib.Path]) -> OjVerifyConfig:
    if config_path:
        try:
            with config_path.open("rb") as fp:
                config = OjVerifyConfig(**tomli.load(fp))
                if config:
                    logger.info("config file loaded: %s: %s", str(config_path), config)
                    return config
        except Exception:
            pass
        logger.info("no config file")
    return OjVerifyConfig(languages={})
