import argparse
import pathlib
import sys
from typing import Optional

import competitive_verifier_oj_clone.config

from .resolver import OjResolver


def run_impl(
    include: list[str],
    exclude: list[str],
    config_path: Optional[pathlib.Path],
    enable_bundle: bool,
) -> bool:
    if config_path:
        competitive_verifier_oj_clone.config.set_config_path(config_path)

    resolver = OjResolver(
        include=include,
        exclude=exclude,
    )
    resolved = resolver.resolve(bundle=enable_bundle)
    print(resolved.impl.json(exclude_none=True))
    return True


def run(args: argparse.Namespace) -> bool:
    return run_impl(
        include=args.include,
        exclude=args.exclude,
        config_path=args.config,
        enable_bundle=args.bundle,
    )


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    parser.add_argument(
        "--include",
        nargs="*",
        help="Included file",
        default=[],
        type=str,
    )
    parser.add_argument(
        "--exclude",
        nargs="*",
        help="Excluded file",
        default=[],
        type=str,
    )
    parser.add_argument(
        "--no-bundle",
        dest="bundle",
        action="store_false",
        help="Disable bundle",
    )
    parser.add_argument(
        "--config",
        help="config.toml",
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
