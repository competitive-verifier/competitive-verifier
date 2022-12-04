# Python Version: 3.x
import pathlib
from logging import getLogger
from typing import Optional, Sequence

import competitive_verifier_oj_clone.utils as utils
from competitive_verifier_oj_clone.languages.models import Language, LanguageEnvironment
from competitive_verifier_oj_clone.languages.special_comments import (
    list_special_comments,
)

from .. import subprocess2 as subprocess

logger = getLogger(__name__)


class UserDefinedLanguageEnvironment(LanguageEnvironment):
    config: dict[str, str]

    def __init__(self, *, config: dict[str, str]):
        self.config = config

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> Optional[str]:
        compile = self.config.get("compile")
        if compile:
            return compile.format(
                path=str(path), basedir=str(basedir), tempdir=str(tempdir)
            )
        return None

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        assert "execute" in self.config
        return self.config["execute"].format(
            path=str(path), basedir=str(basedir), tempdir=str(tempdir)
        )


class UserDefinedLanguage(Language):
    extension: str
    config: dict[str, str]

    def __init__(self, *, extension: str, config: dict[str, str]):
        self.extension = extension
        self.config = config

    def list_attributes(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> dict[str, str]:
        if "list_attributes" not in self.config:
            return list_special_comments(path)
        logger.warning(
            '"languages.*.list_attributes" field in .verify-helper/config.toml is now obsoleted'
        )

        command = self.config["list_attributes"].format(
            path=str(path), basedir=str(basedir)
        )
        text = subprocess.run(command, text=False).stdout
        attributes: dict[str, str] = {}
        for line in text.splitlines():
            key, _, value = line.decode().partition(" ")
            attributes[key] = value
        return attributes

    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        if "list_dependencies" not in self.config:
            logger.warning(
                "The functionality to list dependencies of .%s file is not implemented yet.",
                self.extension,
            )
            return list(
                utils.glob_with_predicate(
                    lambda path: path.suffix == "." + self.extension
                )
            )

        command = self.config["list_dependencies"].format(
            path=path.as_posix(), basedir=basedir.as_posix()
        )
        text = subprocess.run(command, text=False).stdout
        dependencies = [path]
        for line in text.splitlines():
            dependencies.append(pathlib.Path(line.decode()))
        return dependencies

    def bundle(self, path: pathlib.Path, *, basedir: pathlib.Path) -> Optional[bytes]:
        if "bundle" not in self.config:
            return None
        command = self.config["bundle"].format(path=str(path), basedir=str(basedir))
        logger.info("$ %s", command)
        return subprocess.run(command, text=False).stdout

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[LanguageEnvironment]:
        return [UserDefinedLanguageEnvironment(config=self.config)]
