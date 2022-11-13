import argparse
import pathlib
import sys
from typing import Optional

from .resolver import OjResolver


def run_impl(
    include: list[pathlib.Path],
    exclude: list[pathlib.Path],
) -> bool:
    resolver = OjResolver(
        include=include,
        exclude=exclude,
    )
    resolved = resolver.resolve()
    print(resolved.impl.json(exclude_none=True))
    return True


def run(args: argparse.Namespace) -> bool:
    return run_impl(
        include=args.include,
        exclude=args.exclude,
    )


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--include",
        nargs="*",
        help="Included file",
        default=[],
        type=pathlib.Path,
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        help="Excluded file",
        default=[],
        type=pathlib.Path,
    )

    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        parsed = argument(argparse.ArgumentParser()).parse_args(args)
        if not run(parsed):
            sys.exit(1)
    except Exception as e:
        sys.stderr.write(str(e))
        sys.exit(2)


if __name__ == "__main__":
    main()
