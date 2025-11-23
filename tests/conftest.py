import pathlib

import pytest
from pytest_mock import MockerFixture


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--use-prev-dest",
        action="store_true",
        help="Skip deletion of dst_dir.",
    )


@pytest.fixture
def mock_exists(mocker: MockerFixture):
    def _mock_exists(val: bool):
        return mocker.patch.object(pathlib.Path, "exists", return_value=val)

    return _mock_exists


@pytest.fixture
def mock_exec_command(mocker: MockerFixture):
    return mocker.patch("subprocess.run")


@pytest.fixture
def mock_perf_counter(mocker: MockerFixture):
    pc = 0.0

    def _perf_counter() -> float:
        nonlocal pc
        ppc = pc
        pc += 1.0
        return ppc

    mocker.patch("time.perf_counter", side_effect=_perf_counter)
