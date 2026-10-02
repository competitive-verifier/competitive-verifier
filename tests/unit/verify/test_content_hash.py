import datetime
import pathlib
from typing import Any

import pytest

from competitive_verifier.models import VerificationInput
from competitive_verifier.verify.verifier import InputContainer, content_hash

pytestmark = pytest.mark.allow_mkdir


@pytest.fixture(autouse=True)
def chdir_tmp(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    pathlib.Path("foo.py").write_bytes(b"print(1)")
    pathlib.Path("bar.py").write_bytes(b"print(2)")


def test_content_hash_changes_with_content():
    before = content_hash([pathlib.Path("foo.py"), pathlib.Path("bar.py")])
    assert before is not None
    pathlib.Path("bar.py").write_bytes(b"print(3)")
    assert content_hash([pathlib.Path("foo.py"), pathlib.Path("bar.py")]) != before


def test_content_hash_changes_with_path():
    before = content_hash([pathlib.Path("foo.py")])
    pathlib.Path("foo.py").rename("baz.py")
    assert content_hash([pathlib.Path("baz.py")]) != before


def test_content_hash_ignores_order():
    assert content_hash([pathlib.Path("foo.py"), pathlib.Path("bar.py")]) == (
        content_hash([pathlib.Path("bar.py"), pathlib.Path("foo.py")])
    )


def test_content_hash_none_when_file_missing():
    assert content_hash([pathlib.Path("foo.py"), pathlib.Path("missing.py")]) is None


class HashInputContainer(InputContainer):
    def __init__(self, verifications: VerificationInput) -> None:
        super().__init__(
            verifications=verifications,
            verification_time=datetime.datetime.now(),
            prev_result=None,
            split_state=None,
        )

    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        raise NotImplementedError


def _file_content_hash(obj: dict[str, Any], path: str = "foo.py") -> str | None:
    return HashInputContainer(VerificationInput.model_validate(obj)).file_content_hash(
        pathlib.Path(path)
    )


def _input() -> dict[str, Any]:
    return {
        "files": {
            "foo.py": {
                "dependencies": ["bar.py"],
                "verification": {
                    "type": "local",
                    "input": "cases",
                    "command": "true",
                },
            },
            "bar.py": {},
        },
    }


def test_file_content_hash_covers_transitive_dependencies():
    assert _file_content_hash(_input()) == content_hash(
        [pathlib.Path("foo.py"), pathlib.Path("bar.py")]
    )
    assert _file_content_hash(_input(), "bar.py") == content_hash(
        [pathlib.Path("bar.py")]
    )


def test_file_content_hash_none_for_unknown_file():
    assert _file_content_hash(_input(), "unknown.py") is None


def test_file_content_hash_ignores_testdata():
    cases = pathlib.Path("cases")
    cases.mkdir()
    (cases / "a.in").write_bytes(b"1 2\n")
    (cases / "a.out").write_bytes(b"3\n")
    before = _file_content_hash(_input())
    (cases / "a.out").write_bytes(b"4\n")
    assert _file_content_hash(_input()) == before
