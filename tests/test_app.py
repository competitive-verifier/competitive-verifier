import argparse
import math
import os
import pathlib
from typing import Any

import pytest
from pytest_mock import MockerFixture

import competitive_verifier.app as app
from competitive_verifier.arg import COMPETITIVE_VERIFY_FILES_PATH


def parse_args(args: list[str]) -> argparse.Namespace:
    return app.get_parser().parse_args(args)


@pytest.fixture
def setenv(mocker: MockerFixture):
    mocker.patch.dict(
        os.environ,
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        clear=True,
    )


def test_parse_args_default(setenv: Any):
    parsed = parse_args(["verify"])

    assert parsed.verify_files_json == pathlib.Path(
        ".competitive-verifier/verify_files.json"
    )
    assert parsed.timeout == math.inf
    assert parsed.default_tle is None
    assert parsed.default_mle is None
    assert parsed.prev_result is None
    assert parsed.split is None
    assert parsed.split_index is None

    parsed = parse_args(
        [
            "docs",
            ".cr/res0.json",
            ".cr/res1.json",
        ]
    )

    assert parsed.verify_files_json == pathlib.Path(
        ".competitive-verifier/verify_files.json"
    )
    assert parsed.result_json == [
        pathlib.Path(".cr/res0.json"),
        pathlib.Path(".cr/res1.json"),
    ]


def test_parse_args_json_path(setenv: Any):
    parsed = parse_args(["verify", "--verify-json", ".cv/f.json"])
    assert parsed.verify_files_json == pathlib.Path(".cv/f.json")

    parsed = parse_args(
        [
            "docs",
            "--verify-json",
            ".cv/d.json",
            ".cr/res0.json",
            ".cr/res1.json",
        ]
    )
    assert parsed.verify_files_json == pathlib.Path(".cv/d.json")
    assert parsed.result_json == [
        pathlib.Path(".cr/res0.json"),
        pathlib.Path(".cr/res1.json"),
    ]


def test_parse_args_time(setenv: Any):
    parsed = parse_args(["verify", "--timeout", "600", "--tle", "10"])

    assert parsed.timeout == 600.0
    assert parsed.default_tle == 10.0
    assert parsed.prev_result is None


def test_parse_args_prev_result(setenv: Any):
    parsed = parse_args(["verify", "--prev-result", ".cv/prev.json"])
    assert parsed.prev_result == pathlib.Path(".cv/prev.json")


def test_parallel_split(setenv: Any):
    parsed = parse_args(["verify", "--split-index", "1", "--split", "5"])
    assert parsed.split == 5
    assert parsed.split_index == 1
