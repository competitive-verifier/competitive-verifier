from typing import Optional

from pydantic import Field

from competitive_verifier.models import ShellCommand, ShellCommandLike
from competitive_verifier.oj.verify.languages.user_defined import UserDefinedLanguage
from competitive_verifier.oj.verify.models import OjVerifyUserDefinedConfig


class OjVerifyGoConfig(OjVerifyUserDefinedConfig):
    execute: ShellCommandLike = Field(
        default_factory=lambda: ShellCommand(
            command=["go", "run", "{basedir}/{path}"],
            env={"GO111MODULE": "off"},
        ),
    )


class GoLanguage(UserDefinedLanguage):
    def __init__(self, *, config: Optional[OjVerifyGoConfig]):
        super().__init__(extension="go", config=config or OjVerifyGoConfig())
