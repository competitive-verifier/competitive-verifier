import datetime
import pathlib
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import ProblemVerification, VerificationInput
from competitive_verifier.verify.verifier import InputContainer

pytestmark = pytest.mark.allow_mkdir


class HashInputContainer(InputContainer):
    def __init__(
        self,
        verifications: VerificationInput,
        *,
        default_tle: float | None = None,
        default_mle: float | None = None,
    ) -> None:
        super().__init__(
            verifications=verifications,
            verification_time=datetime.datetime.now(),
            prev_result=None,
            split_state=None,
            default_tle=default_tle,
            default_mle=default_mle,
        )

    def get_file_timestamp(self, path: pathlib.Path) -> datetime.datetime:
        raise NotImplementedError


def _hash(
    obj: dict[str, Any],
    path: str = "foo.py",
    *,
    default_tle: float | None = None,
    default_mle: float | None = None,
) -> str:
    h = HashInputContainer(
        VerificationInput.model_validate(obj),
        default_tle=default_tle,
        default_mle=default_mle,
    ).file_content_hash(pathlib.Path(path))
    assert h is not None
    return h


def _problem(**kwargs: Any) -> dict[str, Any]:
    return {
        "files": {
            "foo.py": {
                "verification": {
                    "type": "problem",
                    "problem": "https://judge.yosupo.jp/problem/aplusb",
                    "command": "true",
                    **kwargs,
                },
            },
        },
    }


def _local(cases: str = "cases") -> dict[str, Any]:
    return {
        "files": {
            "foo.py": {
                "verification": {
                    "type": "local",
                    "input": cases,
                    "command": "true",
                },
            },
        },
    }


@pytest.fixture(autouse=True)
def chdir_tmp(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.chdir(tmp_path)
    pathlib.Path("foo.py").write_bytes(b"print(1)")


def test_hash_changes_with_dependency_content():
    before = _hash(_problem())
    pathlib.Path("foo.py").write_bytes(b"print(2)")
    assert _hash(_problem()) != before


def test_hash_changes_with_default_limits():
    base = _hash(_problem())
    assert _hash(_problem(), default_tle=1) != base
    assert _hash(_problem(), default_mle=1) != base
    assert _hash(_problem(), default_tle=1) != _hash(_problem(), default_tle=2)
    assert _hash(_problem(), default_tle=1) == _hash(_problem(), default_tle=1)


def test_explicit_limit_takes_precedence_over_default():
    assert _hash(_problem(tle=3), default_tle=1) == _hash(_problem(tle=3))
    assert _hash(_problem(tle=3), default_tle=1) == _hash(
        _problem(tle=3), default_tle=2
    )
    assert _hash(_problem(tle=3)) != _hash(_problem(tle=4))


def test_default_limits_ignored_for_non_problem_verification():
    obj: dict[str, Any] = {
        "files": {"foo.py": {"verification": {"type": "command", "command": "true"}}}
    }
    assert _hash(obj) == _hash(obj, default_tle=1, default_mle=1)


def test_hash_changes_with_local_cases():
    cases = pathlib.Path("cases")
    cases.mkdir()
    (cases / "a.in").write_bytes(b"1 2\n")
    (cases / "a.out").write_bytes(b"3\n")
    with_a = _hash(_local())
    assert with_a == _hash(_local())

    (cases / "a.out").write_bytes(b"4\n")
    with_a_changed = _hash(_local())
    assert with_a_changed != with_a

    (cases / "b.in").write_bytes(b"5 6\n")
    (cases / "b.out").write_bytes(b"11\n")
    with_a_b = _hash(_local())
    assert len({with_a, with_a_changed, with_a_b}) == 3

    (cases / "b.in").unlink()
    (cases / "b.out").unlink()
    assert _hash(_local()) == with_a_changed


def test_hash_changes_when_local_cases_missing():
    missing = _hash(_local())
    assert missing == _hash(_local())
    cases = pathlib.Path("cases")
    cases.mkdir()
    empty = _hash(_local())
    assert empty != missing
    (cases / "a.in").write_bytes(b"1 2\n")
    (cases / "a.out").write_bytes(b"3\n")
    assert _hash(_local()) not in {missing, empty}


def test_hash_includes_testdata_hash(mocker: MockerFixture):
    hashes: list[str] = []
    for testdata_hash in [None, "version1", "version2"]:
        mocker.patch.object(
            ProblemVerification, "testdata_hash", return_value=testdata_hash
        )
        hashes.append(_hash(_problem()))
        assert _hash(_problem()) == hashes[-1]
    assert len(set(hashes)) == len(hashes)
