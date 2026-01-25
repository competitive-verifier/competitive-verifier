import pathlib

import pytest


def pytest_addoption(parser: pytest.Parser):
    parser.addoption(
        "--use-prev-dest",
        action="store_true",
        help="Skip deletion of dst_dir.",
    )


@pytest.fixture(scope="session")
def integration_test_data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent / "integration_test_data"
