import inspect
import os
import pathlib
import platform
import shutil

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.oj.tools import problem

from .data.cpp import CppWithConfigData, CppWithoutConfigData
from .data.go import GoWithConfigData, GoWithoutConfigData
from .data.integration_data import IntegrationData
from .data.java import JavaData
from .data.rust import RustWithoutConfigData
from .data.user_defined_and_python import UserDefinedAndPythonData
from .mock import MockVerifyCommandResult, update_cloned_repository
from .types import ConfigDirSetter, FilePaths
from .utils import dummy_commit_time


def pytest_runtest_setup(item: pytest.Function):
    if platform.system() != "Linux" and item.get_closest_marker(
        name="integration"
    ):  # pragma: no cover
        pytest.skip(reason="Integration tests are only available on Linux")


@pytest.fixture(scope="session")
def check_necessary_commands() -> str | None:  # pragma: no cover
    git_path = shutil.which("git")
    if not git_path:
        raise AssertionError("The integration test needs command")
    if shutil.which("env"):
        return None
    if os.name != "nt":
        raise AssertionError("The integration test needs env command")

    for git_dir in pathlib.Path(git_path).parents:
        search = git_dir / "usr/bin"
        if search.is_dir():
            return str(search)
    raise AssertionError("The integration test needs env command")


@pytest.fixture(scope="session")
def is_vscode_debug() -> bool:  # pragma: no cover
    try:
        from debugpy import is_client_connected  # type: ignore  # noqa: PGH003, PLC0415
    except ImportError:
        return False

    return is_client_connected()  # pyright: ignore[reportUnknownVariableType]


@pytest.fixture(scope="session")
def use_prev_result(
    request: pytest.FixtureRequest, is_vscode_debug: bool
) -> bool:  # pragma: no cover
    return request.config.getoption("--use-prev-dest") or is_vscode_debug


@pytest.fixture
def additional_path(
    monkeypatch: pytest.MonkeyPatch,
    check_necessary_commands: str | None,
):
    if check_necessary_commands:  # pragma: no cover
        monkeypatch.setenv("PATH", check_necessary_commands, prepend=os.pathsep)


@pytest.fixture(scope="session")
def file_paths(
    integration_test_data_dir: pathlib.Path, use_prev_result: bool
) -> FilePaths:
    root = integration_test_data_dir
    dest_root = root / "dst_dir"
    assert root.exists()

    if dest_root.is_dir() and not use_prev_result:  # pragma: no cover
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
        problem.LibraryCheckerProblem,
        "update_cloned_repository",
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
    assert d.check_envinronment()
    return d
