import pathlib
from collections.abc import Iterator
from contextlib import nullcontext
from logging import getLogger

import requests.exceptions

from competitive_verifier import log
from competitive_verifier.models import Problem, TestCase

from .problem import NotLoggedInError

logger = getLogger(__name__)


# prepare files to write
def _iterate_files_to_write(
    sample: TestCase,
    *,
    directory: pathlib.Path,
) -> Iterator[tuple[str, pathlib.Path, bytes]]:
    for ext in ["in", "out"]:
        data = getattr(sample, ext + "put_data")
        if data is None:
            continue
        filename = pathlib.Path(sample.name).with_suffix(f".{ext}").name
        path: pathlib.Path = directory / "test" / filename
        yield ext, path, data


def _run(*, problem: Problem) -> bool:
    directory = problem.problem_directory
    test_directory = directory / "test"

    if test_directory.exists() and any(test_directory.iterdir()):
        logger.info("download:already exists: %s", problem.url)
        return True

    directory.mkdir(parents=True, exist_ok=True)

    # Get samples from the server
    try:
        samples = problem.download_system_cases()
    except requests.exceptions.RequestException:
        logger.exception("Failed to download samples from the server")
        return False

    # Check samples
    if not samples:
        if samples is not False:
            logger.error("Sample not found")
        return False

    if samples is True:
        return True

    # write samples to files
    for sample in samples:
        for _, path, data in _iterate_files_to_write(sample, directory=directory):
            if path.exists():
                logger.error("Failed to download since file already exists: %s", path)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("wb") as fh:
                fh.write(data)
            logger.debug("saved to: %s", path)

    return True


def run_wrapper(url: str, *, group_log: bool = False) -> bool:
    # prepare values
    problem = Problem.from_url(url)
    if problem is None:
        logger.error('The URL "%s" is not supported', url)
        return False

    with (
        log.group(f"download[Run]: {url}")
        if group_log
        else nullcontext(logger.info("download[Run]: %s", url))
    ):
        try:
            _run(problem=problem)
        except Exception as e:
            if isinstance(e, NotLoggedInError):
                logger.exception(*e.args)
            else:
                logger.exception("Failed to download")
            return False
    return True
