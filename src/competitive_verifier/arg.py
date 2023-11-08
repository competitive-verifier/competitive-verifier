import argparse
import os
import pathlib

COMPETITIVE_VERIFY_FILES_PATH = "COMPETITIVE_VERIFY_FILES_PATH"


def add_verbose_argument(
    parser: argparse.ArgumentParser,
) -> argparse.Action:
    return parser.add_argument(
        "-v", "--verbose", action="store_true", help="Show debug level log."
    )


def add_verify_files_json_argument(
    parser: argparse.ArgumentParser,
    required: bool = True,
) -> argparse.Action:
    default = os.getenv(COMPETITIVE_VERIFY_FILES_PATH)
    return parser.add_argument(
        "--verify-json",
        dest="verify_files_json",
        default=default,
        required=required and not bool(default),
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
        "--check-error",
        help="Exit not zero if failed verification exists",
        dest="ignore_error",
        action="store_false",
    )


def add_write_summary_argument(parser: argparse.ArgumentParser) -> argparse.Action:
    return parser.add_argument(
        "--write-summary",
        action="store_true",
        help="Write GitHub Actions summary",
    )


def add_include_exclude_argument(
    parser: argparse.ArgumentParser,
) -> tuple[argparse.Action, argparse.Action]:
    return parser.add_argument(
        "--include",
        nargs="*",
        help="Included file",
        default=[],
        type=str,
    ), parser.add_argument(
        "--exclude",
        nargs="*",
        help="Excluded file",
        default=[],
        type=str,
    )
