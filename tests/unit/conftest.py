import os

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_perf_counter(mocker: MockerFixture):
    pc = 0.0

    def _perf_counter() -> float:
        nonlocal pc
        ppc = pc
        pc += 1.0
        return ppc

    mocker.patch("time.perf_counter", side_effect=_perf_counter)


@pytest.fixture
def mockenv(mocker: MockerFixture, request: pytest.FixtureRequest):
    mocker.patch.dict(os.environ, request.param or {}, clear=True)


@pytest.fixture(autouse=True)
def mock_mkdir(mocker: MockerFixture):
    mocker.patch("pathlib.Path.mkdir", side_effect=RuntimeError("mkdir is not allowed"))
