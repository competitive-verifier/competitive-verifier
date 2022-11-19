import pathlib
import subprocess
from typing import Literal, Optional, Union, overload

_StrOrListStr = Union[str, list[str]]
_StrBytesPath = Union[str, bytes, pathlib.Path]


@overload
def run(
    command: _StrOrListStr,
    text: Literal[False] = False,
    check: bool = False,
    cwd: Optional[_StrBytesPath] = None,
    env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess[bytes]:
    ...


@overload
def run(
    command: _StrOrListStr,
    text: Literal[True],
    check: bool = False,
    cwd: Optional[_StrBytesPath] = None,
    env: Optional[dict[str, str]] = None,
) -> subprocess.CompletedProcess[str]:
    ...


def run(
    command: _StrOrListStr,
    text: bool = False,
    check: bool = False,
    cwd: Optional[_StrBytesPath] = None,
    env: Optional[dict[str, str]] = None,
) -> Union[subprocess.CompletedProcess[str], subprocess.CompletedProcess[bytes]]:
    return subprocess.run(
        command,
        shell=isinstance(command, str),
        text=text,
        check=check,
        env=env,
        cwd=cwd,
        capture_output=True,
    )
