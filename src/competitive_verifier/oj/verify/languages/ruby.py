from typing import Literal

from pydantic import Field

from competitive_verifier.models import ShellCommand, ShellCommandLike
from competitive_verifier.oj.verify.models import OjVerifyUserDefinedConfig

from .user_defined import UserDefinedLanguage


class OjVerifyRubyConfig(OjVerifyUserDefinedConfig):
    execute: ShellCommandLike = Field(
        default_factory=lambda: ShellCommand(command=["ruby", "{basedir}/{path}"]),
    )


class RubyLanguage(UserDefinedLanguage):
    extension: Literal["rb"] = "rb"  # pyright: ignore[reportIncompatibleVariableOverride]
    config: OjVerifyRubyConfig = Field(default_factory=OjVerifyRubyConfig)  # pyright: ignore[reportIncompatibleVariableOverride]
