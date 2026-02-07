"""This module collects helper classes to compare outputs for `test` subcommand."""

import abc
import math
from logging import getLogger

logger = getLogger(__name__)


class OutputComparator(abc.ABC):
    @abc.abstractmethod
    def __call__(self, actual: bytes, expected: bytes) -> bool:
        """Compare two byte strings.

        Args:
            actual (bytes): Actual output
            expected (bytes): Expected output
        Returns:
            bool: True if they are considered equal
        """
        ...


class ExactComparator(OutputComparator):
    def __call__(self, actual: bytes, expected: bytes) -> bool:
        return actual == expected


class FloatingPointNumberComparator(OutputComparator):
    def __init__(self, *, rel_tol: float, abs_tol: float):
        if max(rel_tol, abs_tol) > 1:
            logger.warning(
                "the tolerance is too large: relative = %s, absolute = %s",
                rel_tol,
                abs_tol,
            )
        self.rel_tol = rel_tol
        self.abs_tol = abs_tol

    def __call__(self, actual: bytes, expected: bytes) -> bool:
        """Assume that both actual and expected are floating point numbers.

        Returns:
        True if the relative error or absolute error is smaller than the accepted error
        """
        try:
            x: float | None = float(actual)
        except ValueError:
            x = None
        try:
            y: float | None = float(expected)
        except ValueError:
            y = None
        if x is not None and y is not None:
            return math.isclose(x, y, rel_tol=self.rel_tol, abs_tol=self.abs_tol)
        return actual == expected


class SplitComparator(OutputComparator):
    def __init__(self, word_comparator: OutputComparator):
        self.word_comparator = word_comparator

    def __call__(self, actual: bytes, expected: bytes) -> bool:
        # str.split() also removes trailing '\r'
        actual_words = actual.split()
        expected_words = expected.split()
        if len(actual_words) != len(expected_words):
            return False
        return all(
            self.word_comparator(x, y)
            for x, y in zip(actual_words, expected_words, strict=False)
        )


class SplitLinesComparator(OutputComparator):
    def __init__(self, line_comparator: OutputComparator):
        self.line_comparator = line_comparator

    def __call__(self, actual: bytes, expected: bytes) -> bool:
        actual_lines = actual.rstrip(b"\n").split(b"\n")
        expected_lines = expected.rstrip(b"\n").split(b"\n")
        if len(actual_lines) != len(expected_lines):
            return False
        return all(
            self.line_comparator(x, y)
            for x, y in zip(actual_lines, expected_lines, strict=False)
        )


class CRLFInsensitiveComparator(OutputComparator):
    def __init__(self, file_comparator: OutputComparator):
        self.file_comparator = file_comparator

    def __call__(self, actual: bytes, expected: bytes) -> bool:
        return self.file_comparator(
            actual.replace(b"\r\n", b"\n"), expected.replace(b"\r\n", b"\n")
        )
