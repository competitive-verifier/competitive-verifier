import datetime
import pathlib
from hashlib import md5
from typing import Iterable


def md5_number(seed: bytes):
    return int(md5(seed).hexdigest(), 16)


def dummy_commit_time(files: Iterable[pathlib.Path]) -> datetime.datetime:
    md5 = md5_number(b"".join(sorted(f.as_posix().encode() for f in files)))

    return datetime.datetime.fromtimestamp(
        md5 % 300000000000 / 100,
        tz=datetime.timezone(datetime.timedelta(hours=md5 % 25 - 12)),
    )
