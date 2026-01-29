import logging
import os
import pathlib
import tempfile

import pytest
from pytest_mock import MockerFixture, MockType


@pytest.fixture
def mock_logger(mocker: MockerFixture) -> MockType:
    mocker.patch.object(logging.Logger, "isEnabledFor", return_value=True)
    return mocker.patch.object(logging.Logger, "_log")


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


@pytest.fixture
def tempdir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield pathlib.Path(tmpdir)
