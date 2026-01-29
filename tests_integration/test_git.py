import pathlib
import subprocess
import tempfile
from datetime import datetime, timedelta, timezone

import pytest

from competitive_verifier import git


@pytest.fixture(scope="session")
def mock_repo_make(integration_test_data_dir: pathlib.Path):
    bundle = integration_test_data_dir / "test-repository.bundle"

    with tempfile.TemporaryDirectory() as tmpdir:
        subprocess.run(["git", "clone", str(bundle), tmpdir], check=True)  # noqa: S607
        yield pathlib.Path(tmpdir).resolve()


@pytest.fixture
def mock_repo(mock_repo_make: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.chdir(mock_repo_make)
    return mock_repo_make


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (
            [],
            datetime(2025, 9, 20, 10, 34, 55, tzinfo=timezone(timedelta(hours=-7))),
        ),
        (
            [pathlib.Path("files1")],
            datetime(2025, 9, 20, 3, 21, 21, tzinfo=timezone(timedelta(hours=+9))),
        ),
        (
            [pathlib.Path("files2")],
            datetime(2025, 9, 20, 11, 34, 55, tzinfo=timezone.utc),
        ),
        (
            [pathlib.Path("files1/foo.txt"), pathlib.Path("r1.txt")],
            datetime(2025, 9, 20, 10, 34, 55, tzinfo=timezone(timedelta(hours=-7))),
        ),
        (
            [pathlib.Path("notmatch")],
            datetime.min.replace(tzinfo=timezone.utc),
        ),
    ],
)
def test_get_commit_time(
    files: list[pathlib.Path],
    expected: datetime,
    mock_repo: pathlib.Path,
):
    assert git.get_commit_time(files) == expected


@pytest.mark.parametrize(
    ("files", "expected"),
    [
        (
            [],
            {
                pathlib.Path("files1/foo.txt"),
                pathlib.Path("files1/bar.txt"),
                pathlib.Path("files1/baz.txt"),
                pathlib.Path("files2/a.c"),
                pathlib.Path("files2/b.c"),
                pathlib.Path("r1.txt"),
                pathlib.Path("r2.txt"),
            },
        ),
        (
            ["files1"],
            {
                pathlib.Path("files1/foo.txt"),
                pathlib.Path("files1/bar.txt"),
                pathlib.Path("files1/baz.txt"),
            },
        ),
        (
            ["files1/foo.txt", "r1.txt"],
            {
                pathlib.Path("files1/foo.txt"),
                pathlib.Path("r1.txt"),
            },
        ),
    ],
)
def test_ls_files(
    files: list[str],
    expected: set[pathlib.Path],
    mock_repo: pathlib.Path,
):
    assert git.ls_files(*files) == expected


def test_get_root_directory(mock_repo: pathlib.Path, monkeypatch: pytest.MonkeyPatch):
    assert git.get_root_directory() == mock_repo
    monkeypatch.chdir("./files1")
    assert git.get_root_directory() == mock_repo
