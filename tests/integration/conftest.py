import pathlib
import shutil
import pytest


@pytest.fixture(scope="session")
def dst_dir():
    DESTINATION_ROOT = pathlib.Path(__file__).parent / pathlib.Path("testdata/dst_dir")
    assert DESTINATION_ROOT.parent.exists()
    if DESTINATION_ROOT.is_dir():
        shutil.rmtree(DESTINATION_ROOT)
    return DESTINATION_ROOT


@pytest.fixture
def setenv(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(pathlib.Path(__file__).parent)
    # mocker.patch.dict(
    #     os.environ, {"YUKICODER_TOKEN": "YKTK", "DROPBOX_TOKEN": "DBTK"}, clear=True
    # )
    # mocker.patch(
    #     "competitive_verifier.oj.get_cache_directory",
    #     return_value=pathlib.Path("/bar/baz/online-judge-tools"),
    # )
    # mocker.patch(
    #     "competitive_verifier.oj.get_checker_path",
    #     return_value=None,
    # )

    # @contextlib.contextmanager
    # def new_session_with_our_user_agent(*, path: pathlib.Path):
    #     sess = requests.Session()
    #     sess.headers = {}
    #     yield sess

    # mocker.patch(
    #     "onlinejudge_command.utils.new_session_with_our_user_agent",
    #     side_effect=new_session_with_our_user_agent,
    # )
