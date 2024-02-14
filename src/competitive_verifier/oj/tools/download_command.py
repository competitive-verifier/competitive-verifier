import os
import pathlib
import shutil
import textwrap
from contextlib import nullcontext
from logging import getLogger
from typing import Iterator, Optional

import onlinejudge.dispatch as dispatch
import onlinejudge_command.download_history
import onlinejudge_command.format_utils as format_utils
import onlinejudge_command.main
import onlinejudge_command.pretty_printers as pretty_printers
import onlinejudge_command.utils as utils
import requests.exceptions
from onlinejudge.service.atcoder import AtCoderProblem
from onlinejudge.service.yukicoder import YukicoderProblem
from onlinejudge.type import NotLoggedInError, SampleParseError, TestCase

from competitive_verifier import log

from .func import (
    get_cache_directory,
    get_checker_path,
    get_directory,
    is_atcoder,
    is_yukicoder,
)

logger = getLogger(__name__)


# flake8: noqa: C901
def run(
    *,
    url: str,
    directory: pathlib.Path,
    cookie: pathlib.Path,
    format: Optional[str] = None,
    system: bool = True,
    silent: bool = True,
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

    is_default_format = format is None
    if format is None:
        format = "%b.%e"

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

    # append the history for submit subcommand
    if not dry_run and is_default_format:
        history = onlinejudge_command.download_history.DownloadHistory()
        if not list(directory.glob("*")):
            # reset the history to help users who use only one directory for many problems
            history.remove(directory=pathlib.Path.cwd())
        history.add(problem, directory=pathlib.Path.cwd())

    # prepare files to write
    def iterate_files_to_write(
        sample: TestCase, *, i: int
    ) -> Iterator[tuple[str, pathlib.Path, bytes]]:
        for ext in ["in", "out"]:
            data = getattr(sample, ext + "put_data")
            if data is None:
                continue
            name = sample.name
            table: dict[str, str] = {}
            table["i"] = str(i + 1)
            table["e"] = ext
            table["n"] = name
            table["b"] = os.path.basename(name)
            table["d"] = os.path.dirname(name)
            path: pathlib.Path = directory / format_utils.percentformat(format, table)
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
        logger.info("")
        logger.info("sample %d", i)
        for ext, path, data in iterate_files_to_write(sample, i=i):
            content = ""
            if not silent:
                content = "\n" + pretty_printers.make_pretty_large_file_content(
                    data, limit=40, head=20, tail=10
                )
            logger.info("%sput: %s%s", ext, sample.name, content)
            if not dry_run:
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("wb") as fh:
                    fh.write(data)
                logger.info(utils.SUCCESS + "saved to: %s", path)

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
            # time.sleep(2)

            try:
                run(
                    url=url,
                    directory=test_directory,
                    cookie=get_cache_directory() / "cookie.txt",
                )
                checker_path = get_checker_path(url)
                if checker_path and checker_path.exists():
                    try:
                        shutil.copy2(checker_path, directory)
                    except Exception as e:
                        logger.exception("Failed to copy checker %s", e)
                        shutil.rmtree(directory)
                        return False
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
