import pathlib
import onlinejudge.utils

config_dir = pathlib.Path(".competitive-verifier")
cache_dir = config_dir / "cache"
temp_dir = config_dir / "tmp"

onlinejudge.utils.user_cache_dir = cache_dir / "oj"
