import pathlib
import tempfile
from collections.abc import Generator

import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--use-prev-dest",
        action="store_true",
        help="Skip deletion of dst_dir.",
    )


@pytest.fixture
def testtemp() -> Generator[pathlib.Path, None, None]:
    with tempfile.TemporaryDirectory() as d:
        yield pathlib.Path(d).resolve()
