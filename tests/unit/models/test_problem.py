import logging
import pathlib
import uuid

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import Problem
from competitive_verifier.models.problem import TestCaseFile as TstCaseFile
from competitive_verifier.oj.problem import (
    AOJArenaProblem,
    LocalProblem,
    YukicoderProblem,
)
from tests import LogComparer


@pytest.mark.allow_mkdir
def test_local_problem(caplog: pytest.LogCaptureFixture, testtemp: pathlib.Path):
    NOT_FOUND_RECORD = LogComparer("no cases found", logging.WARNING)
    DANGLING_OUTPUT_RECORD = LogComparer("dangling output case", logging.WARNING)

    problem = LocalProblem(testtemp)
    assert not problem.download_system_cases()
    assert caplog.records == [NOT_FOUND_RECORD]
    caplog.clear()
    assert list(problem.iter_system_cases()) == []
    assert caplog.records == [NOT_FOUND_RECORD]
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
    assert not caplog.records

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
    assert caplog.records == [DANGLING_OUTPUT_RECORD, DANGLING_OUTPUT_RECORD]


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
    yukicoder = YukicoderProblem(problem_id=227)

    assert yukicoder == YukicoderProblem(problem_id=227)
    assert yukicoder != YukicoderProblem(problem_no=227)
    assert yukicoder != AOJArenaProblem(arena_id="AOJ", alphabet="A")


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
