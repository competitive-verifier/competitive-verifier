import pathlib
import pytest
from pytest_mock import MockerFixture


@pytest.fixture
def mock_exists(mocker: MockerFixture):
    def _mock_exists(val: bool):
        return mocker.patch.object(pathlib.Path, "exists", return_value=val)

    return _mock_exists


@pytest.fixture
def mock_exec_command(mocker: MockerFixture):
    return mocker.patch("subprocess.run")
