import hashlib
import os
import pathlib
import shutil
import sys
from contextlib import nullcontext
from logging import getLogger
from typing import Optional

import onlinejudge._implementation.utils
import onlinejudge.utils
import onlinejudge_command.main
import onlinejudge_command.subcommand.download
from onlinejudge.service.atcoder import AtCoderService
from onlinejudge.service.library_checker import LibraryCheckerProblem
from onlinejudge.service.yukicoder import YukicoderService
from onlinejudge.type import NotLoggedInError

import competitive_verifier.config
import competitive_verifier.exec
from competitive_verifier import log
from competitive_verifier.models.result import TestcaseResult, VerificationResult
from competitive_verifier.models.result_status import ResultStatus
from competitive_verifier.oj_test_command import run as run_test

_oj_cache_dir = competitive_verifier.config.cache_dir.resolve() / "online-judge-tools"
_problem_cache_dir = competitive_verifier.config.cache_dir / "problems"
onlinejudge._implementation.utils.user_cache_dir = _oj_cache_dir
logger = getLogger(__name__)

checker_exe_path = "checker.exe" if sys.platform == "win32" else "checker"


def get_cache_directory() -> pathlib.Path:
    return _oj_cache_dir


def get_directory(url: str) -> pathlib.Path:
    return _problem_cache_dir / hashlib.md5(url.encode()).hexdigest()


def is_yukicoder(url: str) -> bool:
    return YukicoderService.from_url(url) is not None


def is_atcoder(url: str) -> bool:
    return AtCoderService.from_url(url) is not None


def get_checker_problem(url: str) -> Optional[LibraryCheckerProblem]:
    return LibraryCheckerProblem.from_url(url)


def get_checker_path(url: str) -> Optional[pathlib.Path]:
    checker_problem = get_checker_problem(url)
    if checker_problem:
        problem_dir = (
            checker_problem._get_problem_directory_path()  # pyright: ignore reportPrivateUsage=false
        )
        return problem_dir / checker_exe_path


def download(url: str, *, group_log: bool = False) -> bool:
    directory = get_directory(url)
    test_directory = directory / "test"

    logger.info("download[Start]: %s", url)
    if not (test_directory).exists() or list((test_directory).iterdir()) == []:
        logger.info("download[Run]: %s", url)

        if group_log:
            cm = log.group(f"download[Run]: {url}")
        else:
            cm = nullcontext()
        with cm:
            directory.mkdir(parents=True, exist_ok=True)
            # time.sleep(2)

            arg_list: list[str] = [
                "--cookie",
                str(get_cache_directory() / "cookie.txt"),
                "download",
                "--system",
                "-d",
                str(test_directory),
                "--silent",
                url,
            ]

            YUKICODER_TOKEN = os.environ.get("YUKICODER_TOKEN")
            if YUKICODER_TOKEN:
                arg_list += ["--yukicoder-token", YUKICODER_TOKEN]
            DROPBOX_TOKEN = os.environ.get("DROPBOX_TOKEN")
            if DROPBOX_TOKEN:
                arg_list += ["--dropbox-token", DROPBOX_TOKEN]

            try:
                parser = onlinejudge_command.main.get_parser()
                args = parser.parse_args(arg_list)
                onlinejudge_command.subcommand.download.run(args)

                checker_path = get_checker_path(url)
                if checker_path:
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
                    logger.exception("Failed to download", e)
                return False
    else:
        logger.info("download:already exists: %s", url)
    return True


def test(
    *,
    url: str,
    command: str,
    tle: float,
    error: Optional[float],
) -> VerificationResult:
    directory = get_directory(url)
    test_directory = directory / "test"

    arg_list: list[str] = [
        "--cookie",
        str(get_cache_directory() / "cookie.txt"),
        "test",
        "-c",
        command,
        "-d",
        str(test_directory),
        "--print-input",
        "--tle",
        str(tle),
    ]

    checker_path = directory / checker_exe_path
    if checker_path.exists():
        arg_list += ["--judge-command", str(checker_path)]
    if error:
        arg_list += ["-e", str(error)]

    parser = onlinejudge_command.main.get_parser()
    args = parser.parse_args(arg_list)
    result = run_test(args)

    return VerificationResult(
        status=ResultStatus.SUCCESS if result.is_success else ResultStatus.FAILURE,
        elapsed=result.elapsed,
        slowest=result.slowest,
        heaviest=result.heaviest,
        testcases=[
            TestcaseResult(
                name=case.testcase.name,
                elapsed=case.elapsed,
                memory=case.memory,
                status=case.status,
            )
            for case in result.testcases
        ],
    )
