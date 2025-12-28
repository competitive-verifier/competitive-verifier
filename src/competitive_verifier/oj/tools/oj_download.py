import os
import pathlib
import shutil
from collections.abc import Iterator
from contextlib import nullcontext
from itertools import chain
from logging import getLogger

import requests.exceptions
from onlinejudge import dispatch
from onlinejudge.service.library_checker import LibraryCheckerProblem
from onlinejudge.service.yukicoder import YukicoderProblem
from onlinejudge.type import NotLoggedInError, Problem, SampleParseError, TestCase

from competitive_verifier import log

from . import utils
from .func import (
    get_cache_directory,
    get_checker_path,
    get_directory,
    is_yukicoder,
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


def _run_services(problem: Problem, *, system: bool, cookie: pathlib.Path):
    with utils.new_session_with_our_user_agent(path=cookie) as sess:
        if isinstance(problem, YukicoderProblem):
            yukicoder_token = os.environ.get("YUKICODER_TOKEN")
            if yukicoder_token:
                sess.headers["Authorization"] = f"Bearer {yukicoder_token}"
        try:
            return (
                problem.download_system_cases(session=sess)
                if system
                else problem.download_sample_cases(session=sess)
            )
        except requests.exceptions.RequestException:
            logger.exception(
                "Failed to download samples from the server\n"
                + utils.HINT
                + "You may need to login to use `$ oj download ...` during contest. Please run: $ oj login %s",
                problem.get_service().get_url(),
            )
            return None
        except SampleParseError:
            logger.exception("Failed to parse samples from the server")
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
    cookie: pathlib.Path,
    system: bool = True,
    dry_run: bool = False,
) -> bool:
    # prepare values
    problem = dispatch.problem_from_url(url)
    if problem is None:
        logger.error('The URL "%s" is not supported', url)
        return False

    if isinstance(problem, LibraryCheckerProblem):
        return _run_library_checker(
            problem=problem,
            directory=directory,
        )

    # get samples from the server
    samples = _run_services(
        problem,
        system=system,
        cookie=cookie,
    )

    if not samples:
        if samples is not None:
            logger.error("Sample not found")
        return False

    for _i, sample in enumerate(samples):
        for _, path, _ in _iterate_files_to_write(sample, directory=directory):
            if path.exists():
                logger.error(
                    "Failed to download since file already exists: %s", str(path)
                )
                logger.info(
                    utils.HINT
                    + "We recommend adding your own test cases to test/ directory, and using one directory per one problem."
                    " Please see also https://github.com/online-judge-tools/oj/blob/master/docs/getting-started.md#random-testing."
                    " If you wanted to keep using one directory per one contest, you can run like `$ rm -rf test/ && oj d https://...`."
                )
                return False

    # write samples to files
    for _i, sample in enumerate(samples):
        for _, path, data in _iterate_files_to_write(sample, directory=directory):
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("wb") as fh:
                    fh.write(data)
                logger.debug("saved to: %s", path)

    return True


def run_wrapper(url: str, *, group_log: bool = False) -> bool:
    directory = get_directory(url)
    test_directory = directory / "test"

    logger.info("download[Start]: %s into %s", url, test_directory)
    if not (test_directory).exists() or list((test_directory).iterdir()) == []:
        logger.info("download[Run]: %s", url)

        with log.group(f"download[Run]: {url}") if group_log else nullcontext():
            directory.mkdir(parents=True, exist_ok=True)

            try:
                run(
                    url=url,
                    directory=directory,
                    cookie=get_cache_directory() / "cookie.txt",
                )
            except Exception as e:
                if isinstance(e, NotLoggedInError) and is_yukicoder(url):
                    logger.exception("Required: $YUKICODER_TOKEN environment variable")
                else:
                    logger.exception("Failed to download")
                return False
    else:
        logger.info("download:already exists: %s", url)
    return True
