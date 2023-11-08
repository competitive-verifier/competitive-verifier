import argparse
import logging
import sys
from itertools import chain
from logging import getLogger
from typing import Iterable, Optional, Union

from competitive_verifier import oj
from competitive_verifier.arg import (
    add_verbose_argument,
    add_verify_files_json_argument,
)
from competitive_verifier.error import VerifierError
from competitive_verifier.log import configure_stderr_logging
from competitive_verifier.models import (
    ProblemVerification,
    VerificationFile,
    VerificationInput,
)
from competitive_verifier.resource import ulimit_stack

logger = getLogger(__name__)

UrlOrVerificationFile = Union[str, VerificationFile]


def parse_urls(
    input: Union[UrlOrVerificationFile, Iterable[UrlOrVerificationFile]]
) -> set[str]:
    def parse_single(url_or_file: UrlOrVerificationFile) -> Iterable[str]:
        if isinstance(url_or_file, str):
            return (url_or_file,)
        else:
            return enumerate_urls(url_or_file)

    if isinstance(input, (str, VerificationFile)):
        return set(parse_single(input))

    return set(chain.from_iterable(map(parse_single, input)))


def enumerate_urls(file: VerificationFile) -> Iterable[str]:
    for v in file.verification_list:
        if isinstance(v, ProblemVerification):
            yield v.problem


def run_impl(
    input: Union[UrlOrVerificationFile, Iterable[UrlOrVerificationFile]],
    check: bool = False,
    group_log: bool = False,
) -> bool:
    result = True
    try:
        ulimit_stack()
    except Exception:
        logger.warning("failed to increase the stack size[ulimit]")
    for url in parse_urls(input):
        if not oj.download(url, group_log=group_log):
            result = False

    if check and not result:
        raise VerifierError("Failed to download")
    return result


def run(args: argparse.Namespace) -> bool:
    default_level = logging.INFO
    if args.verbose:
        default_level = logging.DEBUG
    configure_stderr_logging(default_level)

    logger.debug("arguments=%s", vars(args))
    logger.info("verify_files_json=%s", str(args.verify_files_json))
    logger.info("urls=%s", args.urls)
    files: list[VerificationFile] = []
    if args.verify_files_json:
        verification = VerificationInput.parse_file_relative(args.verify_files_json)
        files = list(verification.files.values())

    return run_impl(files + args.urls, group_log=True)


def argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verbose_argument(parser)
    add_verify_files_json_argument(parser, required=False)
    parser.add_argument(
        "urls",
        nargs="*",
        help="A list of problem URL",
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
