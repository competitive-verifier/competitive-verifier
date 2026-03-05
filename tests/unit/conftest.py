import os
import pathlib
import tempfile
from collections.abc import Generator
from contextlib import nullcontext

import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_perf_counter(mocker: MockerFixture, request: pytest.FixtureRequest):
    if values := getattr(request, "param", None):
        assert isinstance(request.param, list)
    else:
        values = [float(i) for i in range(1000)]

    return mocker.patch("time.perf_counter", side_effect=values)


@pytest.fixture
def mockenv(mocker: MockerFixture, request: pytest.FixtureRequest):
    mocker.patch.dict(os.environ, request.param or {}, clear=True)


@pytest.fixture(autouse=True)
def prohibit_mkdir(mocker: MockerFixture, request: pytest.FixtureRequest):
    if "allow_mkdir" in request.keywords:
        return None
    return mocker.patch(
        "pathlib.Path.mkdir",
        side_effect=RuntimeError("mkdir is not allowed"),
    )


class TempContext(nullcontext[pathlib.Path]):
    def __init__(self, enter_result: pathlib.Path) -> None:
        super().__init__(enter_result)
        os.mkdir(enter_result)  # noqa: PTH102

    @property
    def name(self):
        return self.enter_result

    def cleanup(self): ...


@pytest.fixture
def testtemp(
    mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
) -> Generator[pathlib.Path, None, None]:
    with tempfile.TemporaryDirectory() as d:
        monkeypatch.chdir(d)
        tmp = pathlib.Path(d).resolve()

        def temp_dir():
            count = 0
            while True:
                count += 1
                yield TempContext(tmp / str(count))

        mocker.patch("tempfile.TemporaryDirectory", side_effect=temp_dir())
        yield tmp
        monkeypatch.undo()
