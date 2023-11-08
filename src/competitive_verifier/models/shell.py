import pathlib
from subprocess import CompletedProcess
from typing import Annotated, Literal, Optional, Union, overload

from pydantic import BaseModel, Field

from competitive_verifier.exec import exec_command


class ShellCommand(BaseModel):
    command: Union[list[str], str] = Field(
        description="Shell command",
    )
    """Shell command
    """

    env: Optional[dict[str, str]] = Field(
        default=None,
        description="Envitonment variables for command",
    )
    """Envitonment variables for command
    """

    cwd: Optional[pathlib.Path] = Field(
        default=None,
        description="The working directory of child process.",
    )
    """The working directory of child process.
    """

    @overload
    def exec_command(
        self,
        text: Literal[False] = False,
        check: bool = False,
        capture_output: bool = False,
        group_log: bool = False,
    ) -> CompletedProcess[bytes]:
        ...

    @overload
    def exec_command(
        self,
        text: Literal[True] = True,
        check: bool = False,
        capture_output: bool = False,
        group_log: bool = False,
    ) -> CompletedProcess[str]:
        ...

    def exec_command(
        self,
        text: bool = False,
        check: bool = False,
        capture_output: bool = False,
        group_log: bool = False,
    ) -> Union[CompletedProcess[str], CompletedProcess[bytes]]:
        return exec_command(
            command=self.command,
            env=self.env,
            text=text,
            check=check,
            capture_output=capture_output,
            cwd=self.cwd,
            group_log=group_log,
        )

    @classmethod
    def parse_command_like(cls, cmd: "ShellCommandLike") -> "ShellCommand":
        if isinstance(cmd, str) or isinstance(cmd, list):
            return ShellCommand(command=cmd)
        return cmd


ShellCommandLike = Annotated[
    Union[ShellCommand, Union[list[str], str]],
    Field(
        examples=[
            "command",
            ["command", "arg1", "arg2"],
            ShellCommand(
                command=["command", "arg1", "arg2"],
                env={"ENVVAR": "DUMMY"},
                cwd=pathlib.Path("/tmp"),
            ),
            ShellCommand(
                command="command",
                env={"ENVVAR": "DUMMY"},
                cwd=pathlib.Path("/tmp"),
            ),
        ]
    ),
]
