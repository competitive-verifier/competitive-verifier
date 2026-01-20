import argparse
import math
import os
import pathlib
import re
from collections.abc import Callable
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import app
from competitive_verifier.arg import COMPETITIVE_VERIFY_FILES_PATH


def parse_args(args: list[str]) -> argparse.Namespace:
    return app.get_parser().parse_args(args)


@pytest.fixture
def setenv(mocker: MockerFixture):
    def _setenv(verify_files_path: str | None):
        if verify_files_path:
            mocker.patch.dict(
                os.environ,
                {COMPETITIVE_VERIFY_FILES_PATH: verify_files_path},
                clear=True,
            )

    return _setenv


def test_parse_args_default(setenv: Callable[[str | None], None]):
    setenv(".competitive-verifier/verify_files.json")
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


def test_parse_args_json_path(setenv: Callable[[str | None], None]):
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


def test_parse_args_time(setenv: Callable[[str | None], None]):
    setenv(".competitive-verifier/verify_files.json")
    parsed = parse_args(["verify", "--timeout", "600", "--tle", "10"])

    assert parsed.timeout == 600.0
    assert parsed.default_tle == 10.0
    assert parsed.prev_result is None


def test_parse_args_prev_result(setenv: Callable[[str | None], None]):
    setenv(".competitive-verifier/verify_files.json")
    parsed = parse_args(["verify", "--prev-result", ".cv/prev.json"])
    assert parsed.prev_result == pathlib.Path(".cv/prev.json")


def test_parallel_split(setenv: Callable[[str | None], None]):
    setenv(".competitive-verifier/verify_files.json")
    parsed = parse_args(["verify", "--split-index", "1", "--split", "5"])
    assert parsed.split == 5
    assert parsed.split_index == 1


def test_app_help(capsys: pytest.CaptureFixture[str]):
    assert app.main([]) == 2

    out, err = capsys.readouterr()
    assert out == app.get_parser().format_help()
    assert err == ""


test_parse_args_params: list[
    tuple[dict[str, str] | None, list[str], dict[str, Any]]
] = [
    (None, [], {"subcommand": None}),
    (
        None,
        ["verify", "--verify-json", ".competitive-verifier/verify_files.json"],
        {
            "subcommand": "verify",
            "default_mle": None,
            "default_tle": None,
            "download": True,
            "ignore_error": True,
            "output": None,
            "prev_result": None,
            "split": None,
            "split_index": None,
            "timeout": math.inf,
            "verbose": False,
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
            "write_summary": False,
        },
    ),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        ["verify"],
        {
            "subcommand": "verify",
            "default_mle": None,
            "default_tle": None,
            "download": True,
            "ignore_error": True,
            "output": None,
            "prev_result": None,
            "split": None,
            "split_index": None,
            "timeout": math.inf,
            "verbose": False,
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
            "write_summary": False,
        },
    ),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        [
            "verify",
            "--mle",
            "1024.5",
            "--tle",
            "2.5",
            "--no-download",
            "--check-error",
            "--write-summary",
            "--verbose",
            "--split",
            "6",
            "--split-index",
            "6",
            "--timeout",
            "20.5",
            "--prev-result",
            ".competitive-verifier/prev.json",
            "--output",
            ".competitive-verifier/out.json",
        ],
        {
            "subcommand": "verify",
            "default_mle": 1024.5,
            "default_tle": 2.5,
            "download": False,
            "ignore_error": False,
            "output": pathlib.Path(".competitive-verifier/out.json"),
            "prev_result": pathlib.Path(".competitive-verifier/prev.json"),
            "split": 6,
            "split_index": 6,
            "timeout": 20.5,
            "verbose": True,
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
            "write_summary": True,
        },
    ),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        [
            "verify",
            "-o",
            ".competitive-verifier/out.json",
        ],
        {
            "subcommand": "verify",
            "default_mle": None,
            "default_tle": None,
            "download": True,
            "ignore_error": True,
            "output": pathlib.Path(".competitive-verifier/out.json"),
            "prev_result": None,
            "split": None,
            "split_index": None,
            "timeout": math.inf,
            "verbose": False,
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
            "write_summary": False,
        },
    ),
    (
        None,
        [
            "docs",
            "--verify-json",
            ".competitive-verifier/verify_files.json",
            "results/result1.json",
        ],
        {
            "subcommand": "docs",
            "destination": pathlib.Path(".competitive-verifier/_jekyll"),
            "docs": None,
            "exclude": [],
            "include": [],
            "ignore_error": True,
            "result_json": [pathlib.Path("results/result1.json")],
            "verbose": False,
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
            "write_summary": False,
        },
    ),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        [
            "docs",
            "results/result1.json",
            "results/result2.json",
            "--check-error",
            "--include",
            "indir1",
            "indir2",
            "--exclude",
            "indir1/ext",
            "indir2/ext/*",
            "--docs",
            ".verify/olddocs",
            "--destination",
            ".verify/_output",
            "--verbose",
            "--write-summary",
        ],
        {
            "subcommand": "docs",
            "destination": pathlib.Path(".verify/_output"),
            "docs": pathlib.Path(".verify/olddocs"),
            "include": ["indir1", "indir2"],
            "exclude": ["indir1/ext", "indir2/ext/*"],
            "ignore_error": False,
            "result_json": [
                pathlib.Path("results/result1.json"),
                pathlib.Path("results/result2.json"),
            ],
            "verbose": True,
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
            "write_summary": True,
        },
    ),
    (
        None,
        ["download"],
        {
            "subcommand": "download",
            "verbose": False,
            "urls": [],
            "verify_files_json": None,
        },
    ),
    (
        None,
        [
            "download",
            "https://example.com/ex1",
            "--verify-json",
            ".competitive-verifier/verify_files.json",
        ],
        {
            "subcommand": "download",
            "verbose": False,
            "urls": ["https://example.com/ex1"],
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
        },
    ),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        ["download", "https://example.com/ex1", "https://example.com/ex2", "--verbose"],
        {
            "subcommand": "download",
            "verbose": True,
            "urls": ["https://example.com/ex1", "https://example.com/ex2"],
            "verify_files_json": pathlib.Path(
                ".competitive-verifier/verify_files.json"
            ),
        },
    ),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ""},
        ["download", "https://example.com/ex1", "https://example.com/ex2"],
        {
            "subcommand": "download",
            "verbose": False,
            "urls": ["https://example.com/ex1", "https://example.com/ex2"],
            "verify_files_json": None,
        },
    ),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        ["merge-input", "input/verify1.json", "input/verify2.json"],
        {
            "subcommand": "merge-input",
            "verbose": False,
            "verify_files_json": [
                pathlib.Path("input/verify1.json"),
                pathlib.Path("input/verify2.json"),
            ],
        },
    ),
    (
        None,
        ["merge-result", "result/result1.json"],
        {
            "subcommand": "merge-result",
            "write_summary": False,
            "verbose": False,
            "result_json": [pathlib.Path("result/result1.json")],
        },
    ),
    (
        None,
        [
            "merge-result",
            "--verbose",
            "result/result1.json",
            "result/result2.json",
            "--write-summary",
        ],
        {
            "subcommand": "merge-result",
            "write_summary": True,
            "verbose": True,
            "result_json": [
                pathlib.Path("result/result1.json"),
                pathlib.Path("result/result2.json"),
            ],
        },
    ),
    (
        None,
        ["check", "result/result1.json"],
        {
            "subcommand": "check",
            "verbose": False,
            "result_json": [pathlib.Path("result/result1.json")],
        },
    ),
    (
        None,
        ["check", "--verbose", "result/result1.json", "result/result2.json"],
        {
            "subcommand": "check",
            "verbose": True,
            "result_json": [
                pathlib.Path("result/result1.json"),
                pathlib.Path("result/result2.json"),
            ],
        },
    ),
    (
        None,
        ["oj-resolve"],
        {
            "subcommand": "oj-resolve",
            "verbose": False,
            "bundle": True,
            "config": None,
            "exclude": [],
            "include": [],
        },
    ),
    (
        None,
        [
            "oj-resolve",
            "--config",
            "new-config.toml",
            "--verbose",
            "--include",
            "indir1",
            "indir2",
            "--exclude",
            "indir1/ext",
            "indir2/ext/*",
            "--no-bundle",
        ],
        {
            "subcommand": "oj-resolve",
            "verbose": True,
            "bundle": False,
            "config": pathlib.Path("new-config.toml"),
            "include": ["indir1", "indir2"],
            "exclude": ["indir1/ext", "indir2/ext/*"],
        },
    ),
    (
        None,
        ["migrate"],
        {
            "subcommand": "migrate",
            "dry_run": False,
            "verbose": False,
        },
    ),
    (
        None,
        ["migrate", "--verbose", "--dry-run"],
        {
            "subcommand": "migrate",
            "dry_run": True,
            "verbose": True,
        },
    ),
]


@pytest.mark.parametrize(
    ("env", "args", "expected"),
    test_parse_args_params,
    ids=(f"{' '.join(t[1])}:{t[0]}" for t in test_parse_args_params),
)
def test_parse_args(
    env: dict[str, str] | None,
    args: list[str],
    expected: dict[str, Any],
    mocker: MockerFixture,
):
    mocker.patch.dict(os.environ, env or {}, clear=True)
    parsed = app.get_parser().parse_args(args)
    assert vars(parsed) == expected


test_parse_args_error_params: list[tuple[dict[str, str] | None, list[str], str]] = [
    (None, ["verify"], "the following arguments are required: --verify-json"),
    (
        None,
        ["docs"],
        "the following arguments are required: --verify-json, result_json",
    ),
    (None, ["merge-input"], "the following arguments are required: verify_files_json"),
    (None, ["merge-result"], "the following arguments are required: result_json"),
    (None, ["check"], "the following arguments are required: result_json"),
    (
        {COMPETITIVE_VERIFY_FILES_PATH: ".competitive-verifier/verify_files.json"},
        ["docs"],
        "the following arguments are required: result_json",
    ),
]


class ParseError(Exception):
    pass


@pytest.mark.parametrize(
    ("env", "args", "expected_message"),
    test_parse_args_error_params,
    ids=(f"{' '.join(t[1])}:{t[0]}" for t in test_parse_args_error_params),
)
def test_parse_args_error(
    env: dict[str, str] | None,
    args: list[str],
    expected_message: str,
    mocker: MockerFixture,
):
    def _error(message: str | None):
        if message:
            raise ParseError(message)

    mocker.patch("argparse.ArgumentParser.error", side_effect=_error)
    mocker.patch.dict(os.environ, env or {}, clear=True)
    with pytest.raises(ParseError, match=f"^{re.escape(expected_message)}$"):
        app.get_parser().parse_args(args)
