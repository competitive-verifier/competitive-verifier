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
from logging import getLogger
from typing import Any, BinaryIO, Iterator, Optional

import colorama
import requests
from onlinejudge import utils

logger = getLogger(__name__)

# These strings can control logging output.
NO_HEADER = "NO_HEADER: "
HINT = "HINT: "
SUCCESS = "SUCCESS: "
FAILURE = "FAILURE: "


def get_user_agent() -> str:
    meta = importlib.metadata.metadata("competitive-verifier")
    name = meta.get("Name")
    version = meta.get("Version")
    url = meta.get("Home-page")
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


def exec_command(
    command_str: str,
    *,
    stdin: Optional[BinaryIO] = None,
    input: Optional[bytes] = None,
    timeout: Optional[float] = None,
    gnu_time: Optional[str] = None,
) -> tuple[dict[str, Any], subprocess.Popen[bytes]]:
    if input is not None:
        assert stdin is None
        stdin = subprocess.PIPE  # type: ignore
    if gnu_time is not None:
        context: Any = tempfile.NamedTemporaryFile(delete=True)
    else:
        context = contextlib.nullcontext()
    with context as fh:
        command = shlex.split(command_str)
        if gnu_time is not None:
            command = [gnu_time, "-f", "%M", "-o", fh.name, "--"] + command
        if os.name == "nt":
            # HACK: without this encoding and decoding, something randomly fails with multithreading; see https://github.com/kmyk/online-judge-tools/issues/468
            command = command_str.encode().decode()  # type: ignore
        begin = time.perf_counter()

        # We need kill processes called from the "time" command using process groups. Without this, orphans spawn. see https://github.com/kmyk/online-judge-tools/issues/640
        preexec_fn = None
        if gnu_time is not None and os.name == "posix":
            preexec_fn = os.setsid

        try:
            proc = subprocess.Popen(
                command,
                stdin=stdin,
                stdout=subprocess.PIPE,
                stderr=sys.stderr,
                preexec_fn=preexec_fn,
            )  # pylint: disable=subprocess-popen-preexec-fn
        except FileNotFoundError:
            logger.error("No such file or directory: %s", command)
            sys.exit(1)
        except PermissionError:
            logger.error("Permission denied: %s", command)
            sys.exit(1)
        answer: Optional[bytes] = None
        try:
            answer, _ = proc.communicate(input=input, timeout=timeout)
        except subprocess.TimeoutExpired:
            pass
        finally:
            if preexec_fn is not None:
                try:
                    os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
            else:
                proc.terminate()

        end = time.perf_counter()
        memory: Optional[float] = None
        if gnu_time is not None:
            with open(fh.name) as fh1:
                reported = fh1.read()
            logger.debug("GNU time says:\n%s", reported)
            if reported.strip() and reported.splitlines()[-1].isdigit():
                memory = int(reported.splitlines()[-1]) / 1000
    info = {
        "answer": answer,  # Optional[byte]
        "elapsed": end - begin,  # float, in second
        "memory": memory,  # Optional[float], in megabyte
    }
    return info, proc


def green(s: str) -> str:
    """green(s) color s with green.

    This function exists to encapsulate the coloring methods only in utils.py.
    """

    return colorama.Fore.GREEN + s + colorama.Fore.RESET


def red(s: str) -> str:
    """red(s) color s with red.

    This function exists to encapsulate the coloring methods only in utils.py.
    """

    return colorama.Fore.RED + s + colorama.Fore.RESET


def remove_suffix(s: str, suffix: str) -> str:
    assert s.endswith(suffix)
    return s[: -len(suffix)]


def get_default_command() -> str:
    """get_default_command returns a command to execute the default output of g++ or clang++. The value is basically `./a.out`, but `.\a.exe` on Windows.

    The type of return values must be `str` and must not be `pathlib.Path`, because the strings `./a.out` and `a.out` are different as commands but same as a path.
    """
    if platform.system() == "Windows":
        return r".\a.exe"
    return "./a.out"
