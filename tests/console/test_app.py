import argparse
import pathlib

import competitive_verifier.console.app as app


def parse_args(args: list[str]) -> argparse.Namespace:
    return app.get_parser().parse_args(args)


def test_parse_args_default():
    parsed = parse_args(["verify"])

    assert parsed.verify_files_json == pathlib.Path(
        ".competitive-verifier/verify_files.json"
    )
    assert parsed.timeout == 1800.0
    assert parsed.default_tle == 60.0
    assert parsed.prev_status is None
    assert parsed.split is None
    assert parsed.split_index is None

    parsed = parse_args(["docs"])

    assert parsed.verify_result_json == pathlib.Path(
        ".competitive-verifier/verify_result.json"
    )


def test_parse_args_json_path():
    parsed = parse_args(["verify", ".cv/f.json"])

    assert parsed.verify_files_json == pathlib.Path(".cv/f.json")

    parsed = parse_args(["docs", ".cv/d.json"])

    assert parsed.verify_result_json == pathlib.Path(".cv/d.json")


def test_parse_args_time():
    parsed = parse_args(["verify", "--timeout", "600", "--tle", "10"])

    assert parsed.timeout == 600.0
    assert parsed.default_tle == 10.0
    assert parsed.prev_status is None


def test_parse_args_prev_status():
    parsed = parse_args(["verify", "--prev-status", ".cv/prev.json"])
    assert parsed.prev_status == pathlib.Path(".cv/prev.json")


def test_parallel_split():
    parsed = parse_args(["verify", "--split-index", "1", "--split", "5"])
    assert parsed.split == 5
    assert parsed.split_index == 1

    parsed = parse_args(["verify", "--split-index", "1"])
