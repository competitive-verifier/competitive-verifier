# Python Version: 3.x
import pathlib
from logging import getLogger
from tempfile import TemporaryDirectory
from typing import Optional, Sequence, Union

from pydantic import BaseModel

import competitive_verifier.oj.verify.languages.special_comments as special_comments
import competitive_verifier.oj.verify.utils as utils
from competitive_verifier.models import ShellCommand, ShellCommandLike
from competitive_verifier.oj.verify.models import (
    Language,
    LanguageEnvironment,
    OjVerifyUserDefinedConfig,
)

logger = getLogger(__name__)

StrPath = Union[pathlib.Path, str]


class PathContainer(BaseModel):
    path: StrPath
    basedir: StrPath
    tempdir: StrPath

    def _format(self, input: str):
        return input.format(
            path=str(self.path),
            dir=str(pathlib.Path(self.path).parent),
            basedir=str(self.basedir),
            tempdir=str(self.tempdir),
        )

    def format_command(self, command: ShellCommandLike) -> ShellCommandLike:
        if isinstance(command, str):
            return self._format(command)

        if not isinstance(command, ShellCommand):
            return list(map(self._format, command))

        if isinstance(command.command, str):
            cmd = self._format(command.command)
        else:
            cmd = list(map(self._format, command.command))

        env = (
            {self._format(k): self._format(v) for k, v in command.env.items()}
            if command.env
            else None
        )

        cwd = pathlib.Path(self._format(str(command.cwd))) if command.cwd else None

        return ShellCommand(
            command=cmd,
            env=env,
            cwd=cwd,
        )

    def parse_command(self, command: ShellCommandLike) -> ShellCommand:
        return ShellCommand.parse_command_like(self.format_command(command))


class UserDefinedLanguageEnvironment(LanguageEnvironment):
    config: OjVerifyUserDefinedConfig
    _name: str

    def __init__(self, *, name: str, config: OjVerifyUserDefinedConfig):
        self.config = config
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> Optional[ShellCommandLike]:
        if self.config.compile:
            return PathContainer(
                path=path, basedir=basedir, tempdir=tempdir
            ).format_command(self.config.compile)
        return None

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> ShellCommandLike:
        return PathContainer(
            path=path, basedir=basedir, tempdir=tempdir
        ).format_command(self.config.execute)


class UserDefinedLanguage(Language):
    extension: str
    config: OjVerifyUserDefinedConfig

    def __init__(self, *, extension: str, config: OjVerifyUserDefinedConfig):
        self.extension = extension
        self.config = config

    def list_attributes(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> dict[str, str]:
        if self.config.list_attributes is None:
            return dict(special_comments.list_special_comments(path))

        with TemporaryDirectory() as tempdir:
            text = (
                PathContainer(path=path, basedir=basedir, tempdir=tempdir)
                .parse_command(self.config.list_attributes)
                .exec_command(text=False, capture_output=True)
                .stdout
            )
        attributes: dict[str, str] = {}
        for line in text.splitlines():
            key, _, value = line.decode().partition(" ")
            attributes[key] = value
        return attributes

    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        if self.config.list_dependencies is None:
            logger.warning(
                "The functionality to list dependencies of .%s file is not implemented yet.",
                self.extension,
            )
            return list(
                utils.glob_with_predicate(
                    lambda path: path.suffix == "." + self.extension
                )
            )

        with TemporaryDirectory() as tempdir:
            text = (
                PathContainer(path=path, basedir=basedir, tempdir=tempdir)
                .parse_command(self.config.list_dependencies)
                .exec_command(text=False, capture_output=True)
                .stdout
            )
        dependencies = [path]
        for line in text.splitlines():
            dependencies.append(pathlib.Path(line.decode()))
        return dependencies

    def bundle(self, path: pathlib.Path, *, basedir: pathlib.Path) -> Optional[bytes]:
        if self.config.bundle is None:
            return None
        with TemporaryDirectory() as tempdir:
            return (
                PathContainer(path=path, basedir=basedir, tempdir=tempdir)
                .parse_command(self.config.bundle)
                .exec_command(text=False, capture_output=True)
                .stdout
            )

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[LanguageEnvironment]:
        return [UserDefinedLanguageEnvironment(name=self.extension, config=self.config)]
