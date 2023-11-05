import os
import pathlib


COMPETITIVE_VERIFY_CONFIG_PATH = "COMPETITIVE_VERIFY_CONFIG_PATH"


def get_config_dir():
    p = os.getenv(COMPETITIVE_VERIFY_CONFIG_PATH, ".competitive-verifier")
    return pathlib.Path(p)


def get_cache_dir():
    return get_config_dir() / "cache"
