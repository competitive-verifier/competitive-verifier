import logging
import os
import pathlib

import pytest

from competitive_verifier.models.problem import TestCaseFile
from competitive_verifier.oj.problem import LocalProblem


def test_local_problem(caplog: pytest.LogCaptureFixture, testtemp: pathlib.Path):
    problem = LocalProblem(testtemp)
    assert not problem.download_system_cases()
    assert list(problem.iter_system_cases()) == []
    assert caplog.record_tuples == []

    (testtemp / "top.in").touch()
    (testtemp / "top.out").touch()
    (testtemp / "other.tmp").touch()

    os.mkdir(testtemp / "subdir")  # noqa: PTH102
    (testtemp / "subdir" / "ss.in").touch()
    (testtemp / "subdir" / "ss.out").touch()
    (testtemp / "subdir" / "other.tmp").touch()

    assert problem.download_system_cases()
    assert list(problem.iter_system_cases()) == [
        TestCaseFile(
            name="top",
            input_path=testtemp / "top.in",
            output_path=testtemp / "top.out",
        ),
        TestCaseFile(
            name="subdir/ss",
            input_path=testtemp / "subdir/ss.in",
            output_path=testtemp / "subdir/ss.out",
        ),
    ]
    assert caplog.record_tuples == []

    (testtemp / "subdir" / "only_in.in").touch()
    (testtemp / "subdir" / "only_out.out").touch()
    assert problem.download_system_cases()
    assert list(problem.iter_system_cases()) == [
        TestCaseFile(
            name="top",
            input_path=testtemp / "top.in",
            output_path=testtemp / "top.out",
        ),
        TestCaseFile(
            name="subdir/ss",
            input_path=testtemp / "subdir/ss.in",
            output_path=testtemp / "subdir/ss.out",
        ),
    ]
    assert caplog.record_tuples == [
        (
            "competitive_verifier.oj.problem",
            logging.WARNING,
            "no .out file: " + (testtemp / "subdir" / "only_in.in").as_posix(),
        ),
    ]
