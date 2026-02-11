import os
import subprocess
import sys
from contextlib import nullcontext
from logging import getLogger
from typing import TYPE_CHECKING, Literal, Optional, overload

from competitive_verifier import log

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath

    _StrOrListStr = str | list[str]


logger = getLogger(__name__)


@overload
def exec_command(
    command: "_StrOrListStr",
    *,
    text: Literal[False] = False,
    check: bool = False,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
    cwd: Optional["StrOrBytesPath"] = None,
    group_log: bool = False,
) -> subprocess.CompletedProcess[bytes]: ...


@overload
def exec_command(
    command: "_StrOrListStr",
    *,
    text: Literal[True],
    check: bool = False,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
    cwd: Optional["StrOrBytesPath"] = None,
    group_log: bool = False,
) -> subprocess.CompletedProcess[str]: ...


@overload
def exec_command(
    command: "_StrOrListStr",
    *,
    text: bool = False,
    check: bool = False,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
    cwd: Optional["StrOrBytesPath"] = None,
    group_log: bool = False,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]: ...


def exec_command(
    command: "_StrOrListStr",
    *,
    text: bool = False,
    check: bool = False,
    capture_output: bool = False,
    env: dict[str, str] | None = None,
    cwd: Optional["StrOrBytesPath"] = None,
    group_log: bool = False,
) -> subprocess.CompletedProcess[str] | subprocess.CompletedProcess[bytes]:
    encoding = sys.stdout.encoding if text else None
    if env:
        env = os.environ | env

    with (
        log.group(f"subprocess.run: {command}")
        if group_log
        else nullcontext(logger.info("subprocess.run: %s", command))
    ):
        return subprocess.run(
            command,
            shell=isinstance(command, str),
            text=text,
            check=check,
            env=env,
            cwd=cwd,
            capture_output=capture_output,
            encoding=encoding,
        )
