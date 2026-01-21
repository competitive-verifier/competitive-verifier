import os

import pytest
from pytest_mock import MockerFixture


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--use-prev-dest",
        action="store_true",
        help="Skip deletion of dst_dir.",
    )


@pytest.fixture
def mock_perf_counter(mocker: MockerFixture):
    pc = 0.0

    def _perf_counter() -> float:
        nonlocal pc
        ppc = pc
        pc += 1.0
        return ppc

    with mocker.patch("time.perf_counter", side_effect=_perf_counter):
        yield


@pytest.fixture
def mockenv(mocker: MockerFixture, request: pytest.FixtureRequest):
    mocker.patch.dict(os.environ, request.param or {}, clear=True)
