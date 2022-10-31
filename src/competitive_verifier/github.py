import datetime
import os
import pathlib
import subprocess
from typing import Iterable


def is_in_github_actions() -> bool:
    return "GITHUB_ACTION" in os.environ


def get_commit_time(files: Iterable[pathlib.Path]) -> datetime.datetime:
    code = ["git", "log", "-1", "--date=iso", "--pretty=%ad", "--"] + list(
        map(str, files)
    )
    timestamp = subprocess.check_output(code).decode().strip()
    if not timestamp:
        return datetime.datetime.min
    return datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S %z")
