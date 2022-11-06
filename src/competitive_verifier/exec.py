import subprocess
from contextlib import nullcontext
from logging import getLogger
from typing import Literal, Union, overload

from competitive_verifier import log

logger = getLogger(__name__)

_StrOrListStr = Union[str, list[str]]


@overload
def exec_command(
    command: _StrOrListStr,
    text: Literal[False] = False,
    check: bool = False,
    capture_output: bool = False,
    group_log: bool = False,
) -> subprocess.CompletedProcess[bytes]:
    ...


@overload
def exec_command(
    command: _StrOrListStr,
    text: Literal[True],
    check: bool = False,
    capture_output: bool = False,
    group_log: bool = False,
) -> subprocess.CompletedProcess[str]:
    ...


def exec_command(
    command: _StrOrListStr,
    text: bool = False,
    check: bool = False,
    capture_output: bool = False,
    group_log: bool = False,
) -> Union[subprocess.CompletedProcess[str], subprocess.CompletedProcess[bytes]]:
    if group_log:
        logger.info("subprocess.run: %s", command)
        cm = nullcontext()
    else:
        cm = log.group(f"subprocess.run: {command}")

    with cm:
        return subprocess.run(
            command,
            shell=True,
            text=text,
            check=check,
            capture_output=capture_output,
        )
