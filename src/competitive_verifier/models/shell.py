import subprocess
from typing import TYPE_CHECKING, Literal, Optional, Union, overload

from pydantic import BaseModel

from competitive_verifier.exec import exec_command

if TYPE_CHECKING:
    from _typeshed import StrOrBytesPath


class ShellCommand(BaseModel):
    command: Union[list[str], str]
    """Shell command
    """

    env: Optional[dict[str, str]] = None
    """Envitonment variables for command
    """

    @overload
    def exec_command(
        self,
        text: Literal[False] = False,
        check: bool = False,
        capture_output: bool = False,
        cwd: Optional["StrOrBytesPath"] = None,
        group_log: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        ...

    @overload
    def exec_command(
        self,
        text: Literal[True] = True,
        check: bool = False,
        capture_output: bool = False,
        cwd: Optional["StrOrBytesPath"] = None,
        group_log: bool = False,
    ) -> subprocess.CompletedProcess[str]:
        ...

    def exec_command(
        self,
        text: bool = False,
        check: bool = False,
        capture_output: bool = False,
        cwd: Optional["StrOrBytesPath"] = None,
        group_log: bool = False,
    ) -> Union[subprocess.CompletedProcess[str], subprocess.CompletedProcess[bytes]]:
        return exec_command(
            command=self.command,
            env=self.env,
            text=text,
            check=check,
            capture_output=capture_output,
            cwd=cwd,
            group_log=group_log,
        )

    @classmethod
    def parse_command_like(cls, cmd: "ShellCommandLike") -> "ShellCommand":
        if isinstance(cmd, str) or isinstance(cmd, list):
            return ShellCommand(command=cmd)
        return cmd


ShellCommandLike = Union[ShellCommand, Union[list[str], str]]
