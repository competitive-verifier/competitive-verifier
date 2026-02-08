from argparse import ArgumentParser
from collections.abc import Iterable
from itertools import chain
from logging import getLogger
from typing import Literal

from pydantic import Field

from competitive_verifier import oj
from competitive_verifier.arg import (
    OptionalVerifyFilesJsonArguments,
    VerboseArguments,
)
from competitive_verifier.models import (
    ProblemVerification,
    VerificationFile,
    VerificationInput,
)
from competitive_verifier.resource import try_ulimit_stack

logger = getLogger(__name__)

UrlOrVerificationFile = str | VerificationFile


def _parse_single_url(url_or_file: UrlOrVerificationFile) -> Iterable[str]:
    if isinstance(url_or_file, str):
        yield url_or_file
    else:
        for v in url_or_file.verification_list:
            if isinstance(v, ProblemVerification):
                yield v.problem


def parse_urls(
    url_or_file: UrlOrVerificationFile | Iterable[UrlOrVerificationFile],
) -> set[str]:
    if isinstance(url_or_file, (str, VerificationFile)):
        return set(_parse_single_url(url_or_file))

    return set(chain.from_iterable(map(_parse_single_url, url_or_file)))


def download_files(
    url_or_file: UrlOrVerificationFile | Iterable[UrlOrVerificationFile],
    *,
    check: bool = False,
    group_log: bool = False,
) -> bool:
    result = True
    try_ulimit_stack()

    for url in parse_urls(url_or_file):
        if not oj.download(url, group_log=group_log):
            result = False

    if check and not result:
        raise RuntimeError("Failed to download")
    return result


class Download(OptionalVerifyFilesJsonArguments, VerboseArguments):
    subcommand: Literal["download"] = Field(
        default="download",
        description="Download problems",
    )
    urls: list[str] = Field(default_factory=list)

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "urls",
            nargs="*",
            help="A list of problem URL",
        )

    def _run(self) -> bool:
        logger.debug("arguments:%s", self)
        logger.info(
            "verify_files_json=%s, urls=%s",
            str(self.verify_files_json),
            self.urls,
        )
        files: list[VerificationFile] = []
        if self.verify_files_json:
            files.extend(
                VerificationInput.parse_file_relative(
                    self.verify_files_json
                ).files.values()
            )

        return download_files(files + self.urls, group_log=True)
