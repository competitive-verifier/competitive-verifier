import os
import pathlib
import shutil
import textwrap
from contextlib import nullcontext
from itertools import chain
from logging import getLogger
from typing import Iterator

import onlinejudge.dispatch as dispatch
import requests.exceptions
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
    problem._generate_test_cases_in_cloned_repository()  # pyright: ignore[reportPrivateUsage]
    path = problem._get_problem_directory_path()  # pyright: ignore[reportPrivateUsage]
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
        except Exception as e:
            logger.exception("Failed to copy checker %s", e)
            shutil.rmtree(directory)
            return False
    return True


# flake8: noqa: C901
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
            DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")
            if not DROPBOX_TOKEN:
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
            sess.headers["Authorization"] = "Bearer {}".format(DROPBOX_TOKEN)
        if isinstance(problem, YukicoderProblem):
            YUKICODER_TOKEN = os.environ.get("YUKICODER_TOKEN")
            if YUKICODER_TOKEN:
                sess.headers["Authorization"] = "Bearer {}".format(YUKICODER_TOKEN)
        try:
            if system:
                samples = problem.download_system_cases(session=sess)
            else:
                samples = problem.download_sample_cases(session=sess)
        except requests.exceptions.RequestException as e:
            logger.error("%s", e)
            logger.error(
                utils.HINT
                + "You may need to login to use `$ oj download ...` during contest. Please run: $ oj login %s",
                problem.get_service().get_url(),
            )
            return False
        except SampleParseError as e:
            logger.error("%s", e)
            return False

    if not samples:
        logger.error("Sample not found")
        return False

    # prepare files to write
    def iterate_files_to_write(
        sample: TestCase, *, i: int
    ) -> Iterator[tuple[str, pathlib.Path, bytes]]:
        for ext in ["in", "out"]:
            data = getattr(sample, ext + "put_data")
            if data is None:
                continue
            basename = os.path.basename(sample.name)
            filename = f"{basename}.{ext}"
            path: pathlib.Path = directory / "test" / filename
            yield ext, path, data

    for i, sample in enumerate(samples):
        for _, path, _ in iterate_files_to_write(sample, i=i):
            if path.exists():
                logger.error(
                    "Failed to download since file already exists: %s", str(path)
                )
                logger.info(
                    utils.HINT
                    + "We recommend adding your own test cases to test/ directory, and using one directory per one problem. Please see also https://github.com/online-judge-tools/oj/blob/master/docs/getting-started.md#random-testing. If you wanted to keep using one directory per one contest, you can run like `$ rm -rf test/ && oj d https://...`."
                )
                return False

    # write samples to files
    for i, sample in enumerate(samples):
        for _, path, data in iterate_files_to_write(sample, i=i):
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

        if group_log:
            cm = log.group(f"download[Run]: {url}")
        else:
            cm = nullcontext()
        with cm:
            directory.mkdir(parents=True, exist_ok=True)

            try:
                run(
                    url=url,
                    directory=directory,
                    cookie=get_cache_directory() / "cookie.txt",
                )
            except Exception as e:
                if isinstance(e, NotLoggedInError) and is_yukicoder(url):
                    logger.error("Required: $YUKICODER_TOKEN environment variable")
                elif isinstance(e, NotLoggedInError) and is_atcoder(url):
                    logger.error("Required: $DROPBOX_TOKEN environment variable")
                else:
                    logger.exception("Failed to download: %s", e)
                return False
    else:
        logger.info("download:already exists: %s", url)
    return True
