import sys
from typing import BinaryIO

from pydantic import BaseModel, ConfigDict, Field

from .base import (
    Language,
    LanguageEnvironment,
    OjVerifyLanguageConfig,
    OjVerifyUserDefinedConfig,
)
from .cplusplus import (
    CPlusPlusLanguage,
    OjVerifyCPlusPlusConfig,
)
from .go import GoLanguage, OjVerifyGoConfig
from .haskell import (
    HaskellLanguage,
    OjVerifyHaskellConfig,
)
from .java import (
    JavaLanguage,
    OjVerifyJavaConfig,
)
from .nim import NimLanguage, OjVerifyNimConfig
from .python import PythonLanguage
from .ruby import (
    OjVerifyRubyConfig,
    RubyLanguage,
)
from .rust import (
    OjVerifyRustConfig,
    OjVerifyRustListDependenciesBackend,
    RustLanguage,
)
from .user_defined import UserDefinedLanguage

if sys.version_info >= (3, 11):  # pragma: no cover
    import tomllib as tomli
else:  # pragma: no cover
    import tomli


class OjVerifyLanguageConfigDict(BaseModel):
    model_config = ConfigDict(extra="allow")
    __pydantic_extra__: dict[str, OjVerifyUserDefinedConfig] = Field(  # pyright: ignore[reportIncompatibleVariableOverride]
        default_factory=dict[str, OjVerifyUserDefinedConfig]
    )

    cpp: OjVerifyCPlusPlusConfig = Field(default_factory=OjVerifyCPlusPlusConfig)
    go: OjVerifyGoConfig = Field(default_factory=OjVerifyGoConfig)
    haskell: OjVerifyHaskellConfig = Field(default_factory=OjVerifyHaskellConfig)
    java: OjVerifyJavaConfig = Field(default_factory=OjVerifyJavaConfig)
    nim: OjVerifyNimConfig = Field(default_factory=OjVerifyNimConfig)
    ruby: OjVerifyRubyConfig = Field(default_factory=OjVerifyRubyConfig)
    rust: OjVerifyRustConfig = Field(default_factory=OjVerifyRustConfig)


class VerificationConfig(BaseModel):
    languages: OjVerifyLanguageConfigDict = Field(
        default_factory=OjVerifyLanguageConfigDict,
    )

    @classmethod
    def load(cls, fp: BinaryIO) -> "VerificationConfig":
        return VerificationConfig.model_validate(tomli.load(fp))

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


__all__ = [
    "CPlusPlusLanguage",
    "GoLanguage",
    "HaskellLanguage",
    "JavaLanguage",
    "Language",
    "LanguageEnvironment",
    "NimLanguage",
    "OjVerifyCPlusPlusConfig",
    "OjVerifyGoConfig",
    "OjVerifyHaskellConfig",
    "OjVerifyJavaConfig",
    "OjVerifyLanguageConfig",
    "OjVerifyNimConfig",
    "OjVerifyRubyConfig",
    "OjVerifyRustConfig",
    "OjVerifyRustListDependenciesBackend",
    "OjVerifyUserDefinedConfig",
    "PythonLanguage",
    "RubyLanguage",
    "RustLanguage",
    "UserDefinedLanguage",
    "VerificationConfig",
]
