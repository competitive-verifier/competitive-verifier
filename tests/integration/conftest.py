import pathlib
import tempfile
from collections.abc import Generator

import pytest


@pytest.fixture(scope="session")
def integration_test_data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent.parent / "integration_test_data"


@pytest.fixture
def testtemp() -> Generator[pathlib.Path, None, None]:
    with tempfile.TemporaryDirectory() as d:
        yield pathlib.Path(d).resolve()
