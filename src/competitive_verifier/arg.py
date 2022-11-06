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
        help="File path of verify_files.json. default: environ variable $COMPETITIVE_VERIFY_FILES_PATH",
        type=pathlib.Path,
    )
