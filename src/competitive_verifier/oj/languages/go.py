from typing import Literal

from pydantic import Field

from competitive_verifier.models import ShellCommand, ShellCommandLike

from .base import OjVerifyUserDefinedConfig
from .user_defined import UserDefinedLanguage


class OjVerifyGoConfig(OjVerifyUserDefinedConfig):
    execute: ShellCommandLike = Field(
        default_factory=lambda: ShellCommand(
            command=["go", "run", "{basedir}/{path}"],
            env={"GO111MODULE": "off"},
        ),
    )


class GoLanguage(UserDefinedLanguage):
    extension: Literal["go"] = "go"  # pyright: ignore[reportIncompatibleVariableOverride]
    config: OjVerifyGoConfig = Field(default_factory=OjVerifyGoConfig)  # pyright: ignore[reportIncompatibleVariableOverride]
