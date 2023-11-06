import contextlib
import datetime
import inspect
import os
import pathlib
import shutil
from typing import Generator, Iterable, Optional

import pytest
import requests
from pytest_mock import MockerFixture

from .data.integration_data import IntegrationData
from .data.user_defined_and_python import UserDefinedAndPythonData
from .types import ConfigDirSetter, FilePaths
from .utils import md5_number


@pytest.fixture(scope="session")
def check_necessary_commands() -> Optional[str]:
    git_path = shutil.which("git")
    if not git_path:
        raise Exception("The integration test needs command")
    if shutil.which("env"):
        return None
    if os.name != "nt":
        raise Exception("The integration test needs env command")

    for git_dir in pathlib.Path(git_path).parents:
        search = git_dir / "usr/bin"
        if search.is_dir():
            return str(search)
    raise Exception("The integration test needs env command")


@pytest.fixture()
def additional_path(
    monkeypatch: pytest.MonkeyPatch,
    check_necessary_commands: Optional[str],
):
    if check_necessary_commands:
        monkeypatch.setenv("PATH", check_necessary_commands, prepend=os.pathsep)


@pytest.fixture(scope="session")
def file_paths(request: pytest.FixtureRequest) -> FilePaths:
    root = pathlib.Path(__file__).parent.parent.parent / "integration_test_data"
    dest_root = root / "dst_dir"
    assert root.exists()

    if dest_root.is_dir() and not request.config.getoption("--use-prev-dest"):
        shutil.rmtree(dest_root)

    return FilePaths(
        root=root,
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


@pytest.fixture
def integration_data(
    monkeypatch: pytest.MonkeyPatch,
    file_paths: FilePaths,
    set_config_dir: ConfigDirSetter,
) -> Generator[IntegrationData, None, None]:
    yield UserDefinedAndPythonData(monkeypatch, set_config_dir, file_paths)


@pytest.fixture
def user_defined_and_python_data(
    integration_data: IntegrationData,
) -> UserDefinedAndPythonData:
    if isinstance(integration_data, UserDefinedAndPythonData):
        return integration_data
    assert False
