import logging
import os
import pathlib

import pytest

from competitive_verifier.models.problem import TestCaseFile as TstCaseFile
from competitive_verifier.oj.problem import LocalProblem


def test_local_problem(caplog: pytest.LogCaptureFixture, testtemp: pathlib.Path):
    NOT_FOUND_TUPLE = (
        "competitive_verifier.oj.file",
        logging.WARNING,
        "no cases found",
    )
    DANGLING_OUTPUT_TUPLE = (
        "competitive_verifier.oj.file",
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

    os.mkdir(testtemp / "subdir")  # noqa: PTH102
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
