import pathlib
from logging import getLogger
from typing import Any, Optional, Sequence

from pydantic import ValidationInfo, field_validator

import competitive_verifier.oj.verify.shlex2 as shlex
from competitive_verifier.oj.verify.languages.user_defined import UserDefinedLanguage
from competitive_verifier.oj.verify.models import (
    LanguageEnvironment,
    OjVerifyUserDefinedConfig,
)

logger = getLogger(__name__)


class OjVerifyJavaConfig(OjVerifyUserDefinedConfig):
    execute: None = None  # pyright: ignore[reportIncompatibleVariableOverride]

    @field_validator("execute", "compile", mode="before")
    @classmethod
    def name_must_contain_space(cls, v: Any, info: ValidationInfo) -> None:
        if v is None:
            return None
        raise ValueError(f'You cannot overwrite "{info.field_name}" for Java language')


class JavaLanguageEnvironment(LanguageEnvironment):
    @property
    def name(self) -> str:
        return "Java"

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return shlex.join(["javac", str(basedir / path)])

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        relative_path = (basedir / path).relative_to(basedir)
        class_path = ".".join([*relative_path.parent.parts, relative_path.stem])
        return shlex.join(["java", class_path])


class JavaLanguage(UserDefinedLanguage):
    def __init__(self, *, config: Optional[OjVerifyJavaConfig]):
        super().__init__(extension="java", config=config or OjVerifyJavaConfig())

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> Sequence[LanguageEnvironment]:
        return [JavaLanguageEnvironment()]
