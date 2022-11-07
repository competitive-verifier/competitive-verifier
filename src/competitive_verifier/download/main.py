import argparse
import logging
import sys
from logging import getLogger
from typing import Iterable, Optional, Union

from competitive_verifier import oj
from competitive_verifier.arg import add_verify_files_json_argument
from competitive_verifier.error import VerifierError
from competitive_verifier.log import configure_logging
from competitive_verifier.models import (
    ProblemVerificationCommand,
    VerificationFile,
    VerificationInput,
)

logger = getLogger(__name__)


def run_impl(url_or_files: Iterable[Union[str, VerificationFile]]) -> bool:
    result = True
    for uf in url_or_files:
        if isinstance(uf, str):
            urls = (uf,)
            if not oj.download(uf):
                result = False
        else:
            urls = enumerate_urls(uf)

        for url in urls:
            if not oj.download(url):
                result = False
    if not result:
        raise VerifierError("Failed to download")
    return result


def enumerate_urls(file: VerificationFile) -> Iterable[str]:
    for verification_command in file.verification:
        if isinstance(verification_command, ProblemVerificationCommand):
            yield verification_command.problem


def run(args: argparse.Namespace) -> bool:
    logger.debug("arguments=%s", vars(args))
    logger.info("verify_files_json=%s", str(args.verify_files_json))
    verification = VerificationInput.parse_file(args.verify_files_json)

    return run_impl(verification.files.values())


def argument_download(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    add_verify_files_json_argument(parser)
    return parser


def main(args: Optional[list[str]] = None) -> None:
    try:
        configure_logging(logging.INFO)
        parsed = argument_download(argparse.ArgumentParser()).parse_args(args)
        run(parsed)
    except (VerifierError) as e:
        sys.stderr.write(e.message)
        sys.exit(2)


if __name__ == "__main__":
    main()
