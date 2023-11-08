import argparse
import importlib.metadata
import sys
from logging import getLogger
from typing import Callable, Optional

logger = getLogger(__name__)


def get_parser() -> argparse.ArgumentParser:
    import competitive_verifier.check.main as check
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.merge_input.main as merge_input
    import competitive_verifier.merge_result.main as merge_result
    import competitive_verifier.migrate.main as migrate
    import competitive_verifier.oj_resolve.main as oj_resolve
    import competitive_verifier.verify.main as verify

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--version",
        action="store_true",
        help="print the online-judge-tools version number",
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
) -> Optional[Callable[[argparse.Namespace], bool]]:
    import competitive_verifier.check.main as check
    import competitive_verifier.documents.main as docs
    import competitive_verifier.download.main as download
    import competitive_verifier.merge_input.main as merge_input
    import competitive_verifier.merge_result.main as merge_result
    import competitive_verifier.migrate.main as migrate
    import competitive_verifier.oj_resolve.main as oj_resolve
    import competitive_verifier.verify.main as verify

    # Use sys.stdout for result
    if subcommand == "merge-result":
        return merge_result.run
    if subcommand == "merge-input":
        return merge_input.run
    if subcommand == "oj-resolve":
        return oj_resolve.run
    if subcommand == "check":
        return check.run
    if subcommand == "migrate":
        return migrate.run

    # Use sys.stdout for logging
    if subcommand == "download":
        return download.run
    if subcommand == "verify":
        return verify.run
    if subcommand == "docs":
        return docs.run
    return None


def main(args: Optional[list[str]] = None):
    parser = get_parser()
    parsed = parser.parse_args(args)

    if parsed.version:
        print(importlib.metadata.version("competitive-verifier"))
        sys.exit(0)

    runner = select_runner(parsed.subcommand)
    if runner:
        sys.exit(0 if runner(parsed) else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
