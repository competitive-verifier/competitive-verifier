import pathlib
from collections.abc import Iterable, Iterator
from logging import getLogger
from typing import TypeVar

from competitive_verifier.models import TestCaseData, TestCaseFile

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


_InOut = TypeVar("_InOut")


def enumerate_inouts(
    inputs: dict[str, _InOut],
    outputs: dict[str, _InOut],
) -> Iterator[tuple[str, _InOut, _InOut]]:
    common_keys = inputs.keys() & outputs.keys()
    if len(inputs) != len(common_keys) or len(outputs) != len(common_keys):
        logger.warning("dangling output case")

    if len(common_keys) == 0:
        logger.warning("no cases found")

    for key in sorted(common_keys):
        yield (key, inputs[key], outputs[key])


def merge_testcase_files(
    inputs: dict[str, pathlib.Path],
    outputs: dict[str, pathlib.Path],
) -> Iterator[TestCaseFile]:
    for name, i, o in enumerate_inouts(inputs, outputs):
        yield TestCaseFile(name=name, input_path=i, output_path=o)


def iter_testcases(*, directory: pathlib.Path) -> Iterator[TestCaseFile]:
    inputs: dict[str, pathlib.Path] = {}
    outputs: dict[str, pathlib.Path] = {}
    for path in directory.iterdir():
        match path.suffix:
            case ".in":
                inputs[path.stem] = path
            case ".out":
                outputs[path.stem] = path
            case _:
                ...
    return merge_testcase_files(inputs, outputs)
