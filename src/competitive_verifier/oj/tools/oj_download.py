import os
import pathlib
import shutil
import textwrap
from collections.abc import Iterator
from contextlib import nullcontext
from itertools import chain
from logging import getLogger

import requests.exceptions
from onlinejudge import dispatch
from onlinejudge.service.atcoder import AtCoderProblem
from onlinejudge.service.library_checker import LibraryCheckerProblem
from onlinejudge.service.yukicoder import YukicoderProblem
from onlinejudge.type import NotLoggedInError, SampleParseError, TestCase

from competitive_verifier import log

from . import utils
from .func import (
    get_cache_directory,
    get_checker_path,
    get_directory,
    is_atcoder,
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
        if dispatch.contest_from_url(url) is not None:
            logger.warning(
                "You specified a URL for a contest instead of a problem. If you want to download for all problems of a contest at once, please try to use `oj-prepare` command of https://github.com/online-judge-tools/template-generator"
            )
        logger.error('The URL "%s" is not supported', url)
        return False

    if isinstance(problem, LibraryCheckerProblem):
        return _run_library_checker(
            problem=problem,
            directory=directory,
        )

    # get samples from the server
    with utils.new_session_with_our_user_agent(path=cookie) as sess:
        if isinstance(problem, AtCoderProblem) and system:
            dropbox_token = os.environ.get("DROPBOX_TOKEN")
            if not dropbox_token:
                logger.info(
                    utils.HINT
                    + "You need to give the access token. Please do the following:\n%s",
                    textwrap.dedent(
                        """
                        1. Open the following URL in your browser:
                            https://www.dropbox.com/oauth2/authorize?client_id=153gig8dqgk3ujg&response_type=code
                        2. Authorize the app and take the access code.
                        3. Run the following command with replacing the "${YOUR_ACCESS_CODE}":
                            $ curl https://api.dropbox.com/oauth2/token --user 153gig8dqgk3ujg:5l7o7lh73o8i9ux --data grant_type=authorization_code --data code=${YOUR_ACCESS_CODE}
                        4. Get the access token from the JSON. It is in the "access_token" field.
                        5. Use the access token. For example:
                            $ oj download """
                        + problem.get_url()
                        + """ --system --dropbox-token=${YOUR_ACCESS_TOKEN}

                    (Please take care that the access code and the access token are CONFIDENTIAL information. DON'T SHARE with other people!)
                """
                    ),
                )
                raise SampleParseError("--dropbox-token is not given")
            sess.headers["Authorization"] = f"Bearer {dropbox_token}"
        if isinstance(problem, YukicoderProblem):
            yukicoder_token = os.environ.get("YUKICODER_TOKEN")
            if yukicoder_token:
                sess.headers["Authorization"] = f"Bearer {yukicoder_token}"
        try:
            samples = (
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
            return False
        except SampleParseError:
            logger.exception("Failed to parse samples from the server")
            return False

    if not samples:
        logger.error("Sample not found")
        return False

    # prepare files to write
    def iterate_files_to_write(
        sample: TestCase,
    ) -> Iterator[tuple[str, pathlib.Path, bytes]]:
        for ext in ["in", "out"]:
            data = getattr(sample, ext + "put_data")
            if data is None:
                continue
            filename = pathlib.Path(sample.name).with_suffix(f".{ext}").name
            path: pathlib.Path = directory / "test" / filename
            yield ext, path, data

    for _i, sample in enumerate(samples):
        for _, path, _ in iterate_files_to_write(sample):
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
        for _, path, data in iterate_files_to_write(sample):
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
                elif isinstance(e, NotLoggedInError) and is_atcoder(url):
                    logger.exception("Required: $DROPBOX_TOKEN environment variable")
                else:
                    logger.exception("Failed to download")
                return False
    else:
        logger.info("download:already exists: %s", url)
    return True
