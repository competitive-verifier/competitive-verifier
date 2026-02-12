import math
import pathlib
from argparse import ArgumentParser
from functools import cached_property
from logging import getLogger
from typing import Literal

from pydantic import Field, field_validator

from competitive_verifier import github
from competitive_verifier.arg import (
    IgnoreErrorArguments,
    VerboseArguments,
    VerifyFilesJsonArguments,
    WriteSummaryArguments,
)
from competitive_verifier.models import VerificationInput, VerifyCommandResult

from .verifier import SplitState, Verifier

logger = getLogger(__name__)


class Verify(
    WriteSummaryArguments,
    IgnoreErrorArguments,
    VerifyFilesJsonArguments,
    VerboseArguments,
):
    subcommand: Literal["verify"] = Field(
        default="verify",
        description="Verify library",
    )
    timeout: float = math.inf
    default_tle: float | None = None
    default_mle: float | None = None

    prev_result: pathlib.Path | None = None

    download: bool = True

    output: pathlib.Path | None = None

    split: int | None = None
    split_index: int | None = None

    @field_validator("timeout", mode="after")
    @classmethod
    def timeout_zero_equals_inf(cls, value: float) -> float:
        if value == 0:
            return math.inf
        return value

    @cached_property
    def split_state(self) -> SplitState | None:
        split = self.split
        split_index = self.split_index
        match (split_index, split):
            case (int(), int()):
                if split <= 0:
                    raise ValueError("--split must be greater than 0.")
                if not (0 <= split_index < split):
                    raise ValueError(
                        "--split-index must be greater than 0 and less than --split."
                    )
                return SplitState(size=split, index=split_index)
            case (None, int()):
                raise ValueError("--split argument requires --split-index argument.")
            case (int(), None):
                raise ValueError("--split-index argument requires --split argument.")
            case _:
                return None

    @classmethod
    def add_parser(cls, parser: ArgumentParser):
        super().add_parser(parser)
        parser.add_argument(
            "--timeout",
            type=float,
            default=math.inf,
            help="Timeout seconds. if value is zero, it is same to math.inf.",
        )
        parser.add_argument(
            "--tle",
            dest="default_tle",
            type=float,
            default=None,
            help="Threshold seconds to be TLE",
        )
        parser.add_argument(
            "--mle",
            dest="default_mle",
            type=float,
            default=None,
            help="Threshold memory usage (MB) to be MLE",
        )
        parser.add_argument(
            "--prev-result",
            type=pathlib.Path,
            required=False,
            help="Previous result json file",
        )

        parser.add_argument(
            "--no-download",
            action="store_false",
            dest="download",
            help="Suppress `oj download`",
        )
        parser.add_argument(
            "--output",
            "-o",
            type=pathlib.Path,
            required=False,
            help="The output file for which verifier saves the result json.",
        )
        parallel_group = parser.add_argument_group("parallel")
        parallel_group.add_argument(
            "--split",
            type=int,
            help="Parallel job size",
            required=False,
        )
        parallel_group.add_argument(
            "--split-index",
            type=int,
            help="Parallel job index",
            required=False,
        )

    def _run(self) -> bool:
        logger.debug("arguments:%s", self)
        logger.info("verify_files_json=%s", str(self.verify_files_json))
        verifications = VerificationInput.parse_file_relative(self.verify_files_json)
        prev_result = None
        if self.prev_result:
            try:
                prev_result = VerifyCommandResult.parse_file_relative(self.prev_result)
            except Exception:
                logger.warning("Failed to parse prev_result: %s", self.prev_result)

        verifier = Verifier(
            verifications,
            use_git_timestamp=github.env.is_in_github_actions(),
            timeout=self.timeout,
            default_tle=self.default_tle,
            default_mle=self.default_mle,
            prev_result=prev_result,
            split_state=self.split_state,
        )
        result = verifier.verify(download=self.download)
        self.write_result(result)

        result_json = result.model_dump_json(exclude_none=True)
        print(result_json)

        if self.output:
            self.output.parent.mkdir(parents=True, exist_ok=True)
            self.output.write_text(result_json, encoding="utf-8")

        is_success = result.is_success()

        if is_success:
            logger.info("success!")
        else:
            logger.warning("not success!")

        return is_success or self.ignore_error
