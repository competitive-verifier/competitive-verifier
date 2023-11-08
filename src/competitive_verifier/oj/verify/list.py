import sys
from logging import getLogger
from typing import BinaryIO

from pydantic import BaseModel, ConfigDict, Field

from competitive_verifier.oj.verify.languages.cplusplus import (
    CPlusPlusLanguage,
    OjVerifyCPlusPlusConfig,
)
from competitive_verifier.oj.verify.languages.go import GoLanguage, OjVerifyGoConfig
from competitive_verifier.oj.verify.languages.haskell import (
    HaskellLanguage,
    OjVerifyHaskellConfig,
)
from competitive_verifier.oj.verify.languages.java import (
    JavaLanguage,
    OjVerifyJavaConfig,
)
from competitive_verifier.oj.verify.languages.nim import NimLanguage, OjVerifyNimConfig
from competitive_verifier.oj.verify.languages.python import PythonLanguage
from competitive_verifier.oj.verify.languages.ruby import (
    OjVerifyRubyConfig,
    RubyLanguage,
)
from competitive_verifier.oj.verify.languages.rust import (
    OjVerifyRustConfig,
    RustLanguage,
)
from competitive_verifier.oj.verify.languages.user_defined import UserDefinedLanguage
from competitive_verifier.oj.verify.models import Language, OjVerifyUserDefinedConfig

if sys.version_info >= (3, 11):
    import tomllib as tomli
else:
    import tomli

logger = getLogger(__name__)


class OjVerifyLanguageConfigDict(BaseModel):
    model_config = ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, OjVerifyUserDefinedConfig]  # pyright: ignore

    cpp: OjVerifyCPlusPlusConfig = Field(default_factory=OjVerifyCPlusPlusConfig)
    go: OjVerifyGoConfig = Field(default_factory=OjVerifyGoConfig)
    haskell: OjVerifyHaskellConfig = Field(default_factory=OjVerifyHaskellConfig)
    java: OjVerifyJavaConfig = Field(default_factory=OjVerifyJavaConfig)
    nim: OjVerifyNimConfig = Field(default_factory=OjVerifyNimConfig)
    ruby: OjVerifyRubyConfig = Field(default_factory=OjVerifyRubyConfig)
    rust: OjVerifyRustConfig = Field(default_factory=OjVerifyRustConfig)


class OjVerifyConfig(BaseModel):
    languages: OjVerifyLanguageConfigDict = Field(
        default_factory=OjVerifyLanguageConfigDict  # pyright: ignore
    )

    @classmethod
    def load(cls, fp: BinaryIO) -> "OjVerifyConfig":
        return OjVerifyConfig.model_validate(tomli.load(fp))

    def get_dict(self) -> dict[str, Language]:
        languages = self.languages
        d: dict[str, Language] = {}
        d[".cpp"] = CPlusPlusLanguage(config=languages.cpp)
        d[".hpp"] = d[".cpp"]
        d[".cc"] = d[".cpp"]
        d[".h"] = d[".cpp"]
        d[".nim"] = NimLanguage(config=languages.nim)
        d[".py"] = PythonLanguage()
        d[".hs"] = HaskellLanguage(config=languages.haskell)
        d[".ruby"] = RubyLanguage(config=languages.ruby)
        d[".go"] = GoLanguage(config=languages.go)
        d[".java"] = JavaLanguage(config=languages.java)
        d[".rs"] = RustLanguage(config=languages.rust)

        for ext, lang_config in languages.__pydantic_extra__.items():
            d["." + ext] = UserDefinedLanguage(extension=ext, config=lang_config)

        return d
