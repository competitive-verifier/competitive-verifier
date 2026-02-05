import collections
import io
import zipfile
from collections.abc import Iterator
from logging import getLogger

from competitive_verifier.models import TestCase

from . import fmtutils

logger = getLogger(__name__)


def extract_from_files(
    files: Iterator[tuple[str, bytes]],
    fmt: str = "%s.%e",
    *,
    ignore_unmatched_samples: bool = False,
) -> list[TestCase]:
    """Extract test case from files.

    Args:
        files (Iterator[tuple[str, bytes]]): A list of test case files.
        fmt (str): The format of filename.
        suffix (str): The extension for output files.
        ignore_unmatched_samples (bool): If true, ignore unmatched sample error.
    """
    table = {
        "s": r"[^/]+",
        "e": r"(in|out)",
    }
    names: dict[str, dict[str, tuple[str, bytes]]] = collections.defaultdict(dict)
    for filename, content in files:
        m = fmtutils.percentparse(filename, fmt, table)
        if not m or m["e"] in names[m["s"]]:
            raise ValueError
        names[m["s"]][m["e"]] = (filename, content)
    testcases: list[TestCase] = []
    for name in sorted(names.keys()):
        data = names[name]
        if "in" not in data or "out" not in data:
            logger.error("unmatched sample found: %s", str(data))
            if not ignore_unmatched_samples:
                raise RuntimeError(f"unmatched sample found: {data}")
        else:
            testcases += [TestCase(name, *data["in"], *data["out"])]
    return testcases


def extract_from_zip(
    zip_data: bytes,
    fmt: str,
    *,
    ignore_unmatched_samples: bool = False,
) -> list[TestCase]:
    with zipfile.ZipFile(io.BytesIO(zip_data)) as fh:
        return extract_from_files(
            (
                (filename, fh.read(filename))
                for filename in fh.namelist()
                if not filename.endswith("/")
            ),
            fmt=fmt,
            ignore_unmatched_samples=ignore_unmatched_samples,
        )
