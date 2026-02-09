import os

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_perf_counter(mocker: MockerFixture, request: pytest.FixtureRequest):
    if not hasattr(request, "param") or not request.param:
        values = [float(i) for i in range(1000)]
    else:
        assert isinstance(request.param, list)
        values = request.param  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType]

    mocker.patch("time.perf_counter", side_effect=values)


@pytest.fixture
def mockenv(mocker: MockerFixture, request: pytest.FixtureRequest):
    mocker.patch.dict(os.environ, request.param or {}, clear=True)


@pytest.fixture(autouse=True)
def mock_mkdir(mocker: MockerFixture):
    mocker.patch("pathlib.Path.mkdir", side_effect=RuntimeError("mkdir is not allowed"))
