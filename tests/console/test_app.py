import pathlib

import competitive_verifier.console.app as app


def test_parse_args_default():
    parsed = app.parse_args(["verify"])

    assert parsed.verify_files_json == pathlib.Path(
        ".competitive-verifier/verify_files.json"
    )
    assert parsed.timeout == 1800.0
    assert parsed.default_tle == 60.0

    parsed = app.parse_args(["docs"])

    assert parsed.verify_result_json == pathlib.Path(
        ".competitive-verifier/verify_result.json"
    )

    parsed = app.parse_args(["all"])

    assert parsed.verify_files_json == pathlib.Path(
        ".competitive-verifier/verify_files.json"
    )
    assert parsed.timeout == 1800.0
    assert parsed.default_tle == 60.0


def test_parse_args_json_path():
    parsed = app.parse_args(["verify", ".cv/f.json"])

    assert parsed.verify_files_json == pathlib.Path(".cv/f.json")
    assert parsed.timeout == 1800.0
    assert parsed.default_tle == 60.0

    parsed = app.parse_args(["docs", ".cv/d.json"])

    assert parsed.verify_result_json == pathlib.Path(".cv/d.json")

    parsed = app.parse_args(["all", ".cv/f.json"])

    assert parsed.verify_files_json == pathlib.Path(".cv/f.json")
    assert parsed.timeout == 1800.0
    assert parsed.default_tle == 60.0


def test_parse_args_time():
    parsed = app.parse_args(["verify", "--timeout", "600", "--tle", "10"])

    assert parsed.timeout == 600.0
    assert parsed.default_tle == 10.0

    parsed = app.parse_args(["all", "--timeout", "600", "--tle", "10"])

    assert parsed.timeout == 600.0
    assert parsed.default_tle == 10.0
