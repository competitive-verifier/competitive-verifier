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
import onlinejudge_command.subcommand.test
from onlinejudge.service.library_checker import LibraryCheckerProblem
from onlinejudge.service.yukicoder import YukicoderService
from onlinejudge.type import NotLoggedInError

import competitive_verifier.config
import competitive_verifier.exec
from competitive_verifier import log

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


def get_checker_problem(url: str) -> Optional[LibraryCheckerProblem]:
    return LibraryCheckerProblem.from_url(url)


def get_checker_path(url: str) -> Optional[pathlib.Path]:
    checker_problem = get_checker_problem(url)
    if checker_problem:
        problem_dir = (
            checker_problem._get_problem_directory_path()
        )  # pyright: reportPrivateUsage=false
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

            try:
                parser = onlinejudge_command.main.get_parser()  # type: ignore
                args = parser.parse_args(arg_list)  # type: ignore
                onlinejudge_command.subcommand.download.run(args)  # type: ignore

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
) -> bool:
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

    parser = onlinejudge_command.main.get_parser()  # type: ignore
    args = parser.parse_args(arg_list)  # type: ignore
    return bool(onlinejudge_command.subcommand.test.run(args))  # type: ignore
