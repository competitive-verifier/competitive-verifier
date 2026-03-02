import logging
import pathlib
import uuid
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import Problem
from competitive_verifier.models.problem import TestCaseFile as TstCaseFile
from competitive_verifier.oj.problem import LocalProblem, YukicoderProblem


@pytest.mark.allow_mkdir
def test_local_problem(caplog: pytest.LogCaptureFixture, testtemp: pathlib.Path):
    NOT_FOUND_TUPLE = (
        "competitive_verifier.oj.problem",
        logging.WARNING,
        "no cases found",
    )
    DANGLING_OUTPUT_TUPLE = (
        "competitive_verifier.oj.problem",
        logging.WARNING,
        "dangling output case",
    )

    problem = LocalProblem(testtemp)
    assert not problem.download_system_cases()
    assert caplog.record_tuples == [NOT_FOUND_TUPLE]
    caplog.clear()
    assert list(problem.iter_system_cases()) == []
    assert caplog.record_tuples == [NOT_FOUND_TUPLE]
    caplog.clear()

    (testtemp / "top.in").touch()
    (testtemp / "top.out").touch()
    (testtemp / "other.tmp").touch()

    (testtemp / "subdir").mkdir()
    (testtemp / "subdir" / "ss.in").touch()
    (testtemp / "subdir" / "ss.out").touch()
    (testtemp / "subdir" / "other.tmp").touch()

    assert problem.download_system_cases()
    assert list(problem.iter_system_cases()) == [
        TstCaseFile(
            name="subdir/ss",
            input_path=testtemp / "subdir/ss.in",
            output_path=testtemp / "subdir/ss.out",
        ),
        TstCaseFile(
            name="top",
            input_path=testtemp / "top.in",
            output_path=testtemp / "top.out",
        ),
    ]
    assert caplog.record_tuples == []

    (testtemp / "subdir" / "only_in.in").touch()
    (testtemp / "subdir" / "only_out.out").touch()
    assert problem.download_system_cases()
    assert list(problem.iter_system_cases()) == [
        TstCaseFile(
            name="subdir/ss",
            input_path=testtemp / "subdir/ss.in",
            output_path=testtemp / "subdir/ss.out",
        ),
        TstCaseFile(
            name="top",
            input_path=testtemp / "top.in",
            output_path=testtemp / "top.out",
        ),
    ]
    assert caplog.record_tuples == [DANGLING_OUTPUT_TUPLE, DANGLING_OUTPUT_TUPLE]


test_problem_params = [
    (
        YukicoderProblem(problem_no=227),
        "68f6c4b6bd028f62cf05d0767b039e80",
        "YukicoderProblem.from_url('https://yukicoder.me/problems/no/227')",
    ),
    (
        YukicoderProblem(problem_id=227),
        "01d49ca1b113ce255a359b4263c99b15",
        "YukicoderProblem.from_url('https://yukicoder.me/problems/227')",
    ),
]


def test_problem_eq():
    class DummyProblem(Problem):
        def __init__(self, url: str) -> None:
            self._url = url

        @property
        def url(self):
            return self._url

        @classmethod
        def from_url(cls, url: str):
            return cls(url)

        def download_system_cases(self) -> Any:
            raise NotImplementedError

        def iter_system_cases(self) -> Any:
            raise NotImplementedError

    yukicoder = YukicoderProblem(problem_id=227)
    dummy = DummyProblem("https://yukicoder.me/problems/227")

    assert yukicoder == YukicoderProblem(problem_id=227)
    assert yukicoder != YukicoderProblem(problem_no=227)
    assert yukicoder.url == dummy.url
    assert yukicoder != yukicoder.url
    assert yukicoder != dummy


@pytest.mark.parametrize(
    ("problem", "hash_id", "repr_str"),
    test_problem_params,
)
def test_problem(
    problem: Problem,
    hash_id: str,
    repr_str: str,
    mocker: MockerFixture,
    subtests: pytest.Subtests,
):
    cache_dir = pathlib.Path("/test_problem/dir") / uuid.uuid4().hex
    mocker.patch(
        "competitive_verifier.config.get_problem_cache_dir",
        return_value=cache_dir,
    )
    with subtests.test(msg="hash_id"):
        assert problem.hash_id == hash_id
    with subtests.test(msg="problem_directory"):
        assert problem.problem_directory == cache_dir / hash_id
    with subtests.test(msg="test_directory"):
        assert problem.test_directory == cache_dir / hash_id / "test"
    with subtests.test(msg="repr"):
        assert repr(problem) == repr_str
