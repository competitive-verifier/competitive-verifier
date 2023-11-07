import contextlib
import datetime
import inspect
import os
import pathlib
import shutil
from typing import Iterable

import pytest
import requests
from pytest_mock import MockerFixture

from .types import ConfigDirSetter, FilePaths
from .utils import md5_number


@pytest.fixture(scope="session")
def file_paths() -> FilePaths:
    root = pathlib.Path(__file__).parent.parent.parent / "integration_test_data"
    dest_root = root / "dst_dir"
    assert root.exists()
    if dest_root.is_dir():
        shutil.rmtree(dest_root)

    return FilePaths(
        root=root,
        targets="targets",
        dest_root=dest_root,
    )


@pytest.fixture
def set_config_dir(mocker: MockerFixture, file_paths: FilePaths) -> ConfigDirSetter:
    def _set_config_dir(name: str):
        d = file_paths.dest_root / "config" / (name or inspect.stack()[1].function)

        mocker.patch.dict(
            os.environ,
            {"COMPETITIVE_VERIFY_CONFIG_PATH": d.as_posix()},
        )
        return d

    return _set_config_dir


@pytest.fixture(autouse=True)
def setenv(
    mocker: MockerFixture,
    monkeypatch: pytest.MonkeyPatch,
    file_paths: FilePaths,
):
    monkeypatch.chdir(file_paths.root)

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
