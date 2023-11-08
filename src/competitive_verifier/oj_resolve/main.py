import argparse
import logging
import pathlib
import sys
from logging import getLogger
from typing import Optional, Union

from pydantic import ValidationError

from competitive_verifier.arg import add_include_exclude_argument, add_verbose_argument
from competitive_verifier.log import configure_stderr_logging
from competitive_verifier.oj.verify.list import OjVerifyConfig

from .resolver import OjResolver

logger = getLogger(__name__)


def run_impl(
    include: list[str],
    exclude: list[str],
    config: Union[pathlib.Path, OjVerifyConfig, None],
    enable_bundle: bool,
) -> bool:
    if config is None:
        logger.info("no config file")
        config = OjVerifyConfig()
    elif not isinstance(config, OjVerifyConfig):
        try:
            config_path = config
            with pathlib.Path(config_path).open("rb") as fp:
                config = OjVerifyConfig.load(fp)
                logger.info("config file loaded: %s: %s", str(config_path), config)
        except ValidationError as e:
            logger.error("config file validation error: %s", e)
            config = OjVerifyConfig()

    resolver = OjResolver(
        include=include,
        exclude=exclude,
        config=config,
    )
    resolved = resolver.resolve(bundle=enable_bundle)
    print(resolved.model_dump_json(exclude_none=True))
    return True


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    return run_impl(
        include=args.include,
        exclude=args.exclude,
        config=args.config,
        enable_bundle=args.bundle,
    )


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    add_include_exclude_argument(parser)
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
