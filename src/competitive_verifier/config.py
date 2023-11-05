import pathlib


def get_config_dir():
    return pathlib.Path(".competitive-verifier")


def get_cache_dir():
    return get_config_dir() / "cache"
