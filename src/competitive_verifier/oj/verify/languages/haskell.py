from typing import Literal

from pydantic import Field

from competitive_verifier.models import ShellCommand, ShellCommandLike
from competitive_verifier.oj.verify.models import OjVerifyUserDefinedConfig

from .user_defined import UserDefinedLanguage


class OjVerifyHaskellConfig(OjVerifyUserDefinedConfig):
    execute: ShellCommandLike = Field(
        default_factory=lambda: ShellCommand(
            command=["runghc", "{basedir}/{path}"],
        ),
    )


class HaskellLanguage(UserDefinedLanguage):
    extension: Literal["hs"] = "hs"  # pyright: ignore[reportIncompatibleVariableOverride]
    config: OjVerifyHaskellConfig = Field(default_factory=OjVerifyHaskellConfig)  # pyright: ignore[reportIncompatibleVariableOverride]
