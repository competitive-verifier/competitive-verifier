import pathlib
import shutil
from collections.abc import Iterator
from contextlib import nullcontext
from itertools import chain
from logging import getLogger

import requests.exceptions

from competitive_verifier import log
from competitive_verifier.models import Problem, TestCase

from .func import get_checker_path, problem_directory
from .problem import (
    LibraryCheckerProblem,
    NotLoggedInError,
)

logger = getLogger(__name__)


def _run_library_checker(
    *,
    problem: LibraryCheckerProblem,
    directory: pathlib.Path,
    dry_run: bool = False,
) -> bool:
    problem.generate_test_cases_in_cloned_repository()
    path = problem.get_problem_directory_path()
    for file in chain(path.glob("in/*.in"), path.glob("out/*.out")):
        dst = directory / "test" / file.name
        if dst.exists():
            logger.error("Failed to download since file already exists: %s", str(dst))
            return False
        if not dry_run:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(file, dst)

    checker_path = get_checker_path(problem)
    if checker_path and checker_path.exists() and not dry_run:
        try:
            shutil.move(checker_path, directory)
        except Exception:
            logger.exception("Failed to copy checker")
            shutil.rmtree(directory)
            return False
    return True


def _run_services(problem: Problem):
    try:
        return problem.download_system_cases()
    except requests.exceptions.RequestException:
        logger.exception("Failed to download samples from the server")
        return None


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


def run(
    *,
    url: str,
    directory: pathlib.Path,
    dry_run: bool = False,
) -> bool:
    # prepare values
    problem = Problem.from_url(url)
    if problem is None:
        logger.error('The URL "%s" is not supported', url)
        return False

    if isinstance(problem, LibraryCheckerProblem):
        return _run_library_checker(
            problem=problem,
            directory=directory,
        )

    # get samples from the server
    samples = _run_services(problem)

    if not samples:
        if samples is not None:
            logger.error("Sample not found")
        return False

    # write samples to files
    for _i, sample in enumerate(samples):
        for _, path, data in _iterate_files_to_write(sample, directory=directory):
            if not dry_run:
                if path.exists():
                    logger.error(
                        "Failed to download since file already exists: %s", str(path)
                    )
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("wb") as fh:
                    fh.write(data)
                logger.debug("saved to: %s", path)

    return True


def run_wrapper(url: str, *, group_log: bool = False) -> bool:
    directory = problem_directory(url)
    test_directory = directory / "test"

    logger.info("download[Start]: %s into %s", url, test_directory)
    if not test_directory.exists() or list(test_directory.iterdir()) == []:
        logger.info("download[Run]: %s", url)

        with log.group(f"download[Run]: {url}") if group_log else nullcontext():
            directory.mkdir(parents=True, exist_ok=True)

            try:
                run(url=url, directory=directory)
            except Exception as e:
                if isinstance(e, NotLoggedInError):
                    logger.exception(*e.args)
                else:
                    logger.exception("Failed to download")
                return False
    else:
        logger.info("download:already exists: %s", url)
    return True
