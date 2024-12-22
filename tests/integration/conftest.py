import contextlib
import inspect
import os
import pathlib
import shutil
from typing import Optional

import onlinejudge.service.library_checker as library_checker
import pytest
import requests
from pytest_mock import MockerFixture

from .data.cpp import CppWithConfigData, CppWithoutConfigData
from .data.go import GoWithConfigData, GoWithoutConfigData
from .data.integration_data import IntegrationData
from .data.java import JavaData
from .data.rust import RustWithoutConfigData
from .data.user_defined_and_python import UserDefinedAndPythonData
from .mock import MockVerifyCommandResult, update_cloned_repository
from .types import ConfigDirSetter, FilePaths
from .utils import dummy_commit_time


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

    mocker.patch(
        "competitive_verifier.git.get_commit_time",
        side_effect=dummy_commit_time,
    )

    @contextlib.contextmanager
    def new_session_with_our_user_agent(*, path: pathlib.Path):
        sess = requests.Session()
        sess.headers = {}
        yield sess

    mocker.patch(
        "competitive_verifier.oj.tools.utils.new_session_with_our_user_agent",
        side_effect=new_session_with_our_user_agent,
    )


@pytest.fixture
def user_defined_and_python_data(
    monkeypatch: pytest.MonkeyPatch,
    file_paths: FilePaths,
    set_config_dir: ConfigDirSetter,
) -> UserDefinedAndPythonData:
    return UserDefinedAndPythonData(monkeypatch, set_config_dir, file_paths)


@pytest.fixture
def mock_verification(mocker: MockerFixture):
    mocker.patch(
        "competitive_verifier.verify.verifier.VerifyCommandResult",
        side_effect=MockVerifyCommandResult,
    )

    mocker.patch.object(
        library_checker.LibraryCheckerService,
        "_update_cloned_repository",
        side_effect=update_cloned_repository,
    )


@pytest.fixture(
    params=[
        UserDefinedAndPythonData,
        GoWithConfigData,
        GoWithoutConfigData,
        JavaData,
        CppWithConfigData,
        CppWithoutConfigData,
        RustWithoutConfigData,
    ]
)
def integration_data(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    file_paths: FilePaths,
    set_config_dir: ConfigDirSetter,
) -> IntegrationData:
    cls = request.param
    assert issubclass(cls, IntegrationData)
    d = cls(monkeypatch, set_config_dir, file_paths)
    if not d.check_envinronment():
        pytest.skip(f"No envinronment {cls.__name__}")
    return d
