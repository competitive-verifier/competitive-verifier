import pathlib

import pytest


@pytest.fixture(scope="session")
def integration_test_data_dir() -> pathlib.Path:
    return pathlib.Path(__file__).parent.parent.parent / "integration_test_data"
