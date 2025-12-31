import pathlib
from collections.abc import Iterable
from functools import reduce
from logging import getLogger
from typing import TypeVar

from competitive_verifier.models import VerificationInput, VerifyCommandResult

logger = getLogger(__name__)

T = TypeVar("T", VerificationInput, VerifyCommandResult)


def merge_input_files(files: Iterable[pathlib.Path]) -> VerificationInput:
    return merge(map(VerificationInput.parse_file_relative, files))


def merge_result_files(files: Iterable[pathlib.Path]) -> VerifyCommandResult:
    return merge(map(VerifyCommandResult.parse_file_relative, files))


def merge(results: Iterable[T]) -> T:
    return reduce(lambda a, b: a.merge(b), results)
