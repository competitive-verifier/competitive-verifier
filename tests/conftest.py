import pathlib
import shutil
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


@pytest.fixture(scope="session")
def dst_dir():
    DESTINATION_ROOT = pathlib.Path(__file__).parent.parent / pathlib.Path(
        "testdata/dst_dir"
    )
    assert DESTINATION_ROOT.parent.exists()
    if DESTINATION_ROOT.is_dir():
        shutil.rmtree(DESTINATION_ROOT)
    return DESTINATION_ROOT
