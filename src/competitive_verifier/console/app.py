import argparse
import pathlib
from typing import Optional

import competitive_verifier.console.config as config


def get_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config-file',
                        type=pathlib.Path,
                        default=config.default_config_path,
                        help='default: "{}"'.format(config.default_config_path))

    # subparsers = parser.add_subparsers(dest='subcommand')

    # subparser = subparsers.add_parser('all')
    # subparser.add_argument('-j', '--jobs', type=int, default=1)
    # subparser.add_argument('--timeout', type=float, default=600)
    # subparser.add_argument('--tle', type=float, default=60)

    # subparser = subparsers.add_parser('run')
    # subparser.add_argument('path', nargs='*', type=pathlib.Path)
    # subparser.add_argument('-j', '--jobs', type=int, default=1)
    # subparser.add_argument('--timeout', type=float, default=600)
    # subparser.add_argument('--tle', type=float, default=60)

    # subparser = subparsers.add_parser('docs')
    # subparser.add_argument('-j', '--jobs', type=int, default=1)

    # subparser = subparsers.add_parser('stats')
    # subparser.add_argument('-j', '--jobs', type=int, default=1)

    return parser


def parse_args(args: Optional[list[str]]) -> argparse.Namespace:
    return get_parser().parse_args(args)


def main(args: Optional[list[str]] = None):
    parsed = parse_args(args)
    print(parsed)


if __name__ == "__main__":
    main()
