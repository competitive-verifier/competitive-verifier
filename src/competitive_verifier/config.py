import os
import pathlib

import onlinejudge._implementation.utils
import onlinejudge.utils  # pyright: ignore[reportUnusedImport]

COMPETITIVE_VERIFY_CONFIG_PATH = "COMPETITIVE_VERIFY_CONFIG_PATH"


def get_config_dir():
    p = pathlib.Path(os.getenv(COMPETITIVE_VERIFY_CONFIG_PATH, ".competitive-verifier"))
    onlinejudge._implementation.utils.user_cache_dir = _get_cache_dir(p)  # noqa: SLF001
    return p


def _get_cache_dir(config_dir: pathlib.Path):
    return config_dir / "cache"


def get_cache_dir():
    return _get_cache_dir(get_config_dir())
