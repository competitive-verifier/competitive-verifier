import contextlib
import http.cookiejar
import importlib.metadata
import os
import pathlib
import platform
import shlex
import signal
import subprocess
import sys
import tempfile
import time
from collections.abc import Iterator
from logging import getLogger
from typing import Any, BinaryIO, IO, overload
import colorama
from pydantic import BaseModel, Field
import requests
from onlinejudge import utils


logger = getLogger(__name__)

# ruff: noqa: G003
# These strings can control logging output.
HINT = "HINT: "
SUCCESS = "SUCCESS: "
FAILURE = "FAILURE: "


class OjExecInfo(BaseModel):
    answer: bytes | None = Field(
        description="The standard output of the executed command"
    )
    elapsed: float = Field(
        description="The elapsed time of the executed command in seconds"
    )
    memory: float | None = Field(
        description="The maximum memory usage of the executed command in megabytes"
    )


def get_user_agent() -> str:
    meta = importlib.metadata.metadata("competitive-verifier")
    name = meta["Name"]
    version = meta["Version"]
    url = meta["Home-page"]
    return f"{name}/{version} (+{url})"


@contextlib.contextmanager
def new_session_with_our_user_agent(
    *, path: pathlib.Path
) -> Iterator[requests.Session]:
    session = requests.Session()
    session.headers["User-Agent"] = get_user_agent()
    logger.debug("User-Agent: %s", session.headers["User-Agent"])
    try:
        with utils.with_cookiejar(session, path=path) as session:
            yield session
    except http.cookiejar.LoadError:
        logger.info(HINT + "You can delete the broken cookie.jar file: %s", str(path))
        raise


def measure_command(
    command: list[str] | str,
    *,
    env: dict[str, str] | None = None,
    stdin: BinaryIO | int | None = None,
    input: bytes | None = None,  # noqa: A002
    timeout: float | None = None,
    gnu_time: str | None = None,
) -> tuple[OjExecInfo, subprocess.Popen[bytes]]:
    if input is not None:
        if stdin is not None:
            raise ValueError(
                stdin, "stdin and input cannot be specified at the same time"
            )
        stdin = subprocess.PIPE

    if isinstance(command, str):
        command = shlex.split(command)
    with (
        contextlib.nullcontext()
        if gnu_time is None
        else tempfile.NamedTemporaryFile(delete=True)
    ) as fh:
        if fh is not None:
            if gnu_time is None:
                raise ValueError("invalid state: gnu_time is None")
            command = [gnu_time, "-f", "%M", "-o", fh.name, "--", *command]
        begin = time.perf_counter()

        # We need kill processes called from the "time" command using process groups. Without this, orphans spawn. see https://github.com/kmyk/online-judge-tools/issues/640
        start_new_session = gnu_time is not None and os.name == "posix"

        try:
            if env:
                env = os.environ | env
            proc = subprocess.Popen(
                command,
                stdin=stdin,
                stdout=subprocess.PIPE,
                env=env,
                stderr=sys.stderr,
                start_new_session=start_new_session,
            )
        except FileNotFoundError:
            logger.exception("No such file or directory: %s", command)
            sys.exit(1)
        except PermissionError:
            logger.exception("Permission denied: %s", command)
            sys.exit(1)
        answer: bytes | None = None
        try:
            answer, _ = proc.communicate(input=input, timeout=timeout)
        except subprocess.TimeoutExpired:
            pass
        finally:
            if start_new_session:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
            else:
                proc.terminate()

        end = time.perf_counter()
        memory: float | None = None
        if fh is not None:
            reported = fh.read().strip()
            logger.debug("GNU time says:\n%s", reported)
            if reported.strip() and reported.splitlines()[-1].isdigit():
                memory = int(reported.splitlines()[-1]) / 1000
        return OjExecInfo(
            answer=answer,
            elapsed=end - begin,
            memory=memory,
        ), proc


def green(s: str) -> str:
    """Make `s` colored with green.

    This function exists to encapsulate the coloring methods only in utils.py.
    """
    return colorama.Fore.GREEN + s + colorama.Fore.RESET


def red(s: str) -> str:
    """Make `s` colored with red.

    This function exists to encapsulate the coloring methods only in utils.py.
    """
    return colorama.Fore.RED + s + colorama.Fore.RESET


def remove_suffix(s: str, suffix: str) -> str:
    assert s.endswith(suffix)
    return s[: -len(suffix)]


def get_default_command() -> str:
    r"""get_default_command returns a command to execute the default output of g++ or clang++. The value is basically `./a.out`, but `.\a.exe` on Windows.

    The type of return values must be `str` and must not be `pathlib.Path`, because the strings `./a.out` and `a.out` are different as commands but same as a path.
    """
    if platform.system() == "Windows":
        return r".\a.exe"
    return "./a.out"
