from typing import Optional

from pydantic import Field

from competitive_verifier.models import ShellCommand, ShellCommandLike
from competitive_verifier.oj.verify.languages.user_defined import UserDefinedLanguage
from competitive_verifier.oj.verify.models import OjVerifyUserDefinedConfig


class OjVerifyHaskellConfig(OjVerifyUserDefinedConfig):
    execute: ShellCommandLike = Field(
        default_factory=lambda: ShellCommand(
            command=["runghc", "{basedir}/{path}"],
        ),
    )


class HaskellLanguage(UserDefinedLanguage):
    def __init__(self, *, config: Optional[OjVerifyHaskellConfig]):
        super().__init__(extension="hs", config=config or OjVerifyHaskellConfig())
