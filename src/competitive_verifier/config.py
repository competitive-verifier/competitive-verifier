import os
import pathlib

COMPETITIVE_VERIFY_CONFIG_PATH = "COMPETITIVE_VERIFY_CONFIG_PATH"


def get_config_dir():
    return pathlib.Path(
        os.getenv(COMPETITIVE_VERIFY_CONFIG_PATH, ".competitive-verifier")
    )


def get_cache_dir():
    return get_config_dir() / "cache"


def get_problem_cache_dir() -> pathlib.Path:
    return get_cache_dir() / "problems"
