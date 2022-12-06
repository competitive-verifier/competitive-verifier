import subprocess
import sys
from contextlib import nullcontext
from logging import getLogger
from typing import Literal, Optional, Union, overload

from competitive_verifier import log

logger = getLogger(__name__)

_StrOrListStr = Union[str, list[str]]


@overload
def exec_command(
    command: _StrOrListStr,
    text: Literal[False] = False,
    check: bool = False,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
    group_log: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    ...


@overload
def exec_command(
    command: _StrOrListStr,
    text: Literal[True],
    check: bool = False,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
    group_log: bool = False,
) -> subprocess.CompletedProcess[str]:
    ...


def exec_command(
    command: _StrOrListStr,
    text: bool = False,
    check: bool = False,
    capture_output: bool = False,
    env: Optional[dict[str, str]] = None,
    group_log: bool = False,
) -> Union[subprocess.CompletedProcess[str], subprocess.CompletedProcess[bytes]]:
    if group_log:
        cm = log.group(f"subprocess.run: {command}")
    else:
        logger.info("subprocess.run: %s", command)
        cm = nullcontext()

    encoding = sys.stdout.encoding if text else None

    with cm:
        return subprocess.run(
            command,
            shell=isinstance(command, str),
            text=text,
            check=check,
            env=env,
            capture_output=capture_output,
            encoding=encoding,
        )
