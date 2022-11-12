import argparse
import sys
from typing import Optional

from ..arg import add_ignore_error_argument
from .resolver import OjResolver


def run_impl() -> bool:
    resolver = OjResolver()
    resolved = resolver.resolve()
    print(resolved.json())
    return True


def run(args: argparse.Namespace) -> bool:
    return run_impl()


def argument_oj_resolve(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_ignore_error_argument(parser)
    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        parsed = argument_oj_resolve(argparse.ArgumentParser()).parse_args(args)
        if not run(parsed):
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()
