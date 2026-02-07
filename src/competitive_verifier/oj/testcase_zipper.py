import collections
import io
import zipfile
from collections.abc import Iterable, Iterator
from logging import getLogger

from competitive_verifier.models import TestCaseData

from . import fmtutils

logger = getLogger(__name__)


def extract_from_files(
    files: Iterator[tuple[str, bytes]],
    fmt: str = "%s.%e",
    *,
    ignore_unmatched_samples: bool = False,
) -> Iterable[TestCaseData]:
    """Extract test case from files.

    Args:
        files (Iterator[tuple[str, bytes]]): A list of test case files.
        fmt (str): The format of filename.
        ignore_unmatched_samples (bool): If true, ignore unmatched sample error.
    """
    table = {
        "s": r"[^/]+",
        "e": r"(in|out)",
    }
    names: dict[str, dict[str, bytes]] = collections.defaultdict(dict)
    for filename, content in files:
        m = fmtutils.percentparse(filename, fmt, table)
        if not m or m["e"] in names[m["s"]]:
            raise ValueError
        names[m["s"]][m["e"]] = content
    for name in sorted(names.keys()):
        data = names[name]
        if "in" not in data or "out" not in data:
            logger.error("unmatched sample found: %s", str(data))
            if not ignore_unmatched_samples:
                raise RuntimeError(f"unmatched sample found: {data}")
        else:
            yield TestCaseData(name, data["in"], data["out"])


def extract_from_zip(
    zip_data: bytes,
    fmt: str,
    *,
    ignore_unmatched_samples: bool = False,
) -> list[TestCaseData]:
    with zipfile.ZipFile(io.BytesIO(zip_data)) as fh:
        return list(
            extract_from_files(
                files=(
                    (filename, fh.read(filename))
                    for filename in fh.namelist()
                    if not filename.endswith("/")
                ),
                fmt=fmt,
                ignore_unmatched_samples=ignore_unmatched_samples,
            )
        )
