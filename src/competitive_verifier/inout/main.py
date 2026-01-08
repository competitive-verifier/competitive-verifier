import pathlib
from argparse import ArgumentParser
from collections import Counter
from collections.abc import Iterable
from functools import reduce
from logging import getLogger
from typing import Literal, TypeVar

from pydantic import Field

from competitive_verifier import github, summary
from competitive_verifier.arg import (
    ResultJsonArguments,
    VerboseArguments,
    WriteSummaryArguments,
)
from competitive_verifier.models import (
    ResultStatus,
    VerificationInput,
    VerifyCommandResult,
)

logger = getLogger(__name__)

T = TypeVar("T", VerificationInput, VerifyCommandResult)


def merge(results: Iterable[T]) -> T:
    return reduce(lambda a, b: a.merge(b), results)


class MergeInput(VerboseArguments):
    subcommand: Literal["merge-input"] = Field(
        default="merge-input",
        description="Merge verify_files.json`",
    )
    verify_files_json: list[pathlib.Path]

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "verify_files_json",
            nargs="+",
            help="verify_files.json files",
            type=pathlib.Path,
        )

    def _run(self) -> bool:
        result = merge(
            map(VerificationInput.parse_file_relative, self.verify_files_json)
        )
        print(result.model_dump_json(exclude_none=True))
        return True


class MergeResult(WriteSummaryArguments, ResultJsonArguments, VerboseArguments):
    subcommand: Literal["merge-result"] = Field(
        default="merge-result",
        description="Merge result of `verify`",
    )

    def merge(self) -> VerifyCommandResult:
        return merge(map(VerifyCommandResult.parse_file_relative, self.result_json))

    def _run(self) -> bool:
        result = self.merge()
        if self.write_summary:
            gh_summary_path = github.env.get_step_summary_path()
            if gh_summary_path and gh_summary_path.parent.exists():
                with gh_summary_path.open("w", encoding="utf-8") as fp:
                    summary.write_summary(fp, result)
            else:
                logger.warning("write_summary=True but not found $GITHUB_STEP_SUMMARY")

        print(result.model_dump_json(exclude_none=True))
        return True


class Check(ResultJsonArguments, VerboseArguments):
    subcommand: Literal["check"] = Field(
        default="check",
        description="Check result of `verify`",
    )

    def _run(self) -> bool:
        result = merge(map(VerifyCommandResult.parse_file_relative, self.result_json))

        counter = Counter(
            r.status for fr in result.files.values() for r in fr.verifications
        )

        for st in ResultStatus:
            print(f"{st.value}: {counter.get(st, 0)}")

        if counter[ResultStatus.FAILURE] > 0:
            if self.verbose:
                logger.error("Failure test count: %d", counter[ResultStatus.FAILURE])
            return False
        return True
