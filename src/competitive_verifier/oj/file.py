import pathlib
from collections.abc import Iterable
from logging import getLogger

from competitive_verifier.models import TestCaseData

logger = getLogger(__name__)


def _name_to_filename(name: str, ext: str):
    return pathlib.Path(name).with_suffix(f".{ext}").name


def save_testcases(samples: Iterable[TestCaseData], *, directory: pathlib.Path):
    for sample in samples:
        save_testcase(sample, directory=directory)


def save_testcase(sample: TestCaseData, *, directory: pathlib.Path):
    for data, ext in [(sample.input_data, "in"), (sample.output_data, "out")]:
        path = directory / _name_to_filename(sample.name, ext)

        if path.exists():
            logger.error("Failed to download since file already exists: %s", path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        logger.debug("saved to: %s", path)
