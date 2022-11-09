import argparse
import os
import pathlib

COMPETITIVE_VERIFY_FILES_PATH = "COMPETITIVE_VERIFY_FILES_PATH"


def add_verify_files_json_argument(parser: argparse.ArgumentParser) -> argparse.Action:
    default = os.getenv(COMPETITIVE_VERIFY_FILES_PATH)
    return parser.add_argument(
        "--verify-json",
        dest="verify_files_json",
        default=default,
        required=not bool(default),
        help="File path of verify_files.json. default: environ variable $COMPETITIVE_VERIFY_FILES_PATH",  # noqa: E501
        type=pathlib.Path,
    )


def add_result_json_argument(parser: argparse.ArgumentParser) -> argparse.Action:
    return parser.add_argument(
        "result_json",
        nargs="+",
        help="Json files which is result of `verify`",
        type=pathlib.Path,
    )


def add_ignore_error_argument(parser: argparse.ArgumentParser) -> argparse.Action:
    return parser.add_argument(
        "--ignore-error",
        help="exit 0 even if command failed",
        action="store_true",
    )
