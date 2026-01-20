import argparse
import importlib.metadata
from collections.abc import Callable
from logging import getLogger

# ruff: noqa: PLC0415

logger = getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    import competitive_verifier.check.main as check
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.merge_input.main as merge_input
    import competitive_verifier.merge_result.main as merge_result
    import competitive_verifier.migrate.main as migrate
    import competitive_verifier.oj.resolve.main as oj_resolve
    import competitive_verifier.verify.main as verify

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="version",
        version=importlib.metadata.version("competitive-verifier"),
        help="print the competitive-verifier version number",
    )

    subparsers = parser.add_subparsers(dest="subcommand")

    subparser = subparsers.add_parser(
        "verify",
        help="Verify library",
    )
    verify.argument(subparser)

    subparser = subparsers.add_parser(
        "docs",
        help="Create documents",
    )
    docs.argument(subparser)

    subparser = subparsers.add_parser(
        "download",
        help="Download problems",
    )
    download.argument(subparser)

    subparser = subparsers.add_parser(
        "merge-input",
        help="Merge verify_files.json",
    )
    merge_input.argument(subparser)

    subparser = subparsers.add_parser(
        "merge-result",
        help="Merge result of `verify`",
    )
    merge_result.argument(subparser)

    subparser = subparsers.add_parser(
        "check",
        help="Check result of `verify`",
    )
    check.argument(subparser)

    subparser = subparsers.add_parser(
        "oj-resolve",
        help="Create verify_files json using `oj-verify`",
    )
    oj_resolve.argument(subparser)

    subparser = subparsers.add_parser(
        "migrate",
        help="Migration from verification-helper(`oj-verify`) project",
    )
    migrate.argument(subparser)

    return parser


def select_runner(
    subcommand: str,
) -> Callable[[argparse.Namespace], bool] | None:
    import competitive_verifier.check.main as check
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.merge_input.main as merge_input
    import competitive_verifier.merge_result.main as merge_result
    import competitive_verifier.migrate.main as migrate
    import competitive_verifier.oj.resolve.main as oj_resolve
    import competitive_verifier.verify.main as verify

    d = {
        # Use sys.stdout for result
        "merge-result": merge_result.run,
        "merge-input": merge_input.run,
        "oj-resolve": oj_resolve.run,
        "check": check.run,
        "migrate": migrate.run,
        # Use sys.stdout for logging
        "download": download.run,
        "verify": verify.run,
        "docs": docs.run,
    }

    return d.get(subcommand)


def main(args: list[str] | None = None) -> int:
    parser = get_parser()
    parsed = parser.parse_args(args)

    runner = select_runner(parsed.subcommand)
    if runner:
        return not runner(parsed)
    parser.print_help()
    return 2
