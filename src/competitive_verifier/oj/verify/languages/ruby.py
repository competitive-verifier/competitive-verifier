from typing import Optional

from pydantic import Field

from competitive_verifier.models import ShellCommand, ShellCommandLike
from competitive_verifier.oj.verify.languages.user_defined import UserDefinedLanguage
from competitive_verifier.oj.verify.models import OjVerifyUserDefinedConfig


class OjVerifyRubyConfig(OjVerifyUserDefinedConfig):
    execute: ShellCommandLike = Field(
        default_factory=lambda: ShellCommand(command=["ruby", "{basedir}/{path}"]),
    )


class RubyLanguage(UserDefinedLanguage):
    def __init__(self, *, config: Optional[OjVerifyRubyConfig]):
        super().__init__(extension="rb", config=config or OjVerifyRubyConfig())
