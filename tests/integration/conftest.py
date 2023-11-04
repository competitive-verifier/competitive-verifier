import contextlib
import datetime
import pathlib
import shutil
from hashlib import md5
from typing import Iterable

import pytest
import requests
from pytest_mock import MockerFixture


def md5_number(seed: bytes):
    return int(md5(seed).hexdigest(), 16)


@pytest.fixture(scope="session")
def dst_dir():
    DESTINATION_ROOT = pathlib.Path(__file__).parent / pathlib.Path("testdata/dst_dir")
    assert DESTINATION_ROOT.parent.exists()
    if DESTINATION_ROOT.is_dir():
        shutil.rmtree(DESTINATION_ROOT)
    return DESTINATION_ROOT


@pytest.fixture(autouse=True)
def setenv(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(pathlib.Path(__file__).parent / "testdata")

    def get_commit_time(files: Iterable[pathlib.Path]) -> datetime.datetime:
        md5 = md5_number(b"".join(sorted(f.as_posix().encode() for f in files)))

        return datetime.datetime.fromtimestamp(
            md5 % 300000000000 / 100,
            tz=datetime.timezone(datetime.timedelta(hours=md5 % 25 - 12)),
        )

    mocker.patch(
        "competitive_verifier.git.get_commit_time",
        side_effect=get_commit_time,
    )

    @contextlib.contextmanager
    def new_session_with_our_user_agent(*, path: pathlib.Path):
        sess = requests.Session()
        sess.headers = {}
        yield sess

    mocker.patch(
        "onlinejudge_command.utils.new_session_with_our_user_agent",
        side_effect=new_session_with_our_user_agent,
    )
