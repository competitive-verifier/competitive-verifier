# Python Version: 3.x
import functools
import os
import pathlib
import platform
import shutil
from logging import getLogger
from typing import Any, Optional

from pydantic import BaseModel

import competitive_verifier.oj.verify.languages.special_comments as special_comments
import competitive_verifier.oj.verify.shlex2 as shlex
from competitive_verifier.oj.verify.languages.cplusplus_bundle import Bundler
from competitive_verifier.oj.verify.models import (
    Language,
    LanguageEnvironment,
    OjVerifyLanguageConfig,
)
from competitive_verifier.oj.verify.utils import exec_command

logger = getLogger(__name__)


class OjVerifyCPlusPlusConfigEnv(BaseModel):
    CXX: str
    CXXFLAGS: Optional[list[str]] = None


class OjVerifyCPlusPlusConfig(OjVerifyLanguageConfig):
    environments: Optional[list[OjVerifyCPlusPlusConfigEnv]] = None


class CPlusPlusLanguageEnvironment(LanguageEnvironment):
    cxx: pathlib.Path
    cxx_flags: list[str]

    def __init__(self, *, CXX: pathlib.Path, CXXFLAGS: list[str]):
        self.cxx = CXX
        self.cxx_flags = CXXFLAGS

    @property
    def name(self) -> str:
        return self.cxx.name

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return shlex.join(
            [
                str(self.cxx),
                *self.cxx_flags,
                "-I",
                str(basedir),
                "-o",
                str(tempdir / "a.out"),
                str(path),
            ]
        )

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return str(tempdir / "a.out")

    def is_clang(self) -> bool:
        return "clang++" in self.cxx.name

    def is_gcc(self) -> bool:
        return not self.is_clang() and "g++" in self.cxx.name


@functools.lru_cache(maxsize=None)
def _cplusplus_list_depending_files(
    path: pathlib.Path, *, CXX: pathlib.Path, joined_CXXFLAGS: str
) -> list[pathlib.Path]:
    is_windows = platform.uname().system == "Windows"
    command = [str(CXX), *shlex.split(joined_CXXFLAGS), "-MM", str(path)]
    try:
        data = exec_command(command).stdout
    except Exception:
        logger.error(
            "failed to analyze dependencies with %s: %s  (hint: Please check #include directives of the file and its dependencies. The paths must exist, must not contain '\\', and must be case-sensitive.)",
            CXX,
            str(path),
        )
        raise
    logger.debug("dependencies of %s: %s", str(path), repr(data))
    makefile_rule = shlex.split(
        data.decode().strip().replace("\\\n", "").replace("\\\r\n", ""),
        posix=not is_windows,
    )
    return [pathlib.Path(path).resolve() for path in makefile_rule[1:]]


@functools.lru_cache(maxsize=None)
def _cplusplus_list_defined_macros(
    path: pathlib.Path, *, CXX: pathlib.Path, joined_CXXFLAGS: str
) -> dict[str, str]:
    command = [str(CXX), *shlex.split(joined_CXXFLAGS), "-dM", "-E", str(path)]
    data = exec_command(command).stdout
    define: dict[str, str] = {}
    for line in data.decode().splitlines():
        assert line.startswith("#define ")
        a, _, b = line[len("#define ") :].partition(" ")
        if (b.startswith('"') and b.endswith('"')) or (
            b.startswith("'") and b.endswith("'")
        ):
            b = b[1:-1]
        define[a] = b
    return define


_NOT_SPECIAL_COMMENTS = "*NOT_SPECIAL_COMMENTS*"
_PROBLEM = "PROBLEM"
_IGNORE = "IGNORE"
_IGNORE_IF_CLANG = "IGNORE_IF_CLANG"
_IGNORE_IF_GCC = "IGNORE_IF_GCC"
_ERROR = "ERROR"
_STANDALONE = "STANDALONE"


# config.toml example:
#     [[languages.cpp.environments]]
#     CXX = "g++"
#     CXXFALGS = ["-std=c++17", "-Wall"]
class CPlusPlusLanguage(Language):
    config: OjVerifyCPlusPlusConfig

    def __init__(self, *, config: Optional[OjVerifyCPlusPlusConfig]):
        self.config = config or OjVerifyCPlusPlusConfig()

    def _list_environments(self) -> list[CPlusPlusLanguageEnvironment]:
        default_CXXFLAGS = ["--std=c++17", "-O2", "-Wall", "-g"]
        if platform.system() == "Windows" or "CYGWIN" in platform.system():
            default_CXXFLAGS.append("-Wl,-stack,0x10000000")
        if platform.system() == "Darwin":
            default_CXXFLAGS.append("-Wl,-stack_size,0x10000000")
        if (
            platform.uname().system == "Linux"
            and "Microsoft" in platform.uname().release
        ):
            default_CXXFLAGS.append("-fsplit-stack")

        if "CXXFLAGS" in os.environ and not self.config.environments:
            logger.warning(
                "Usage of $CXXFLAGS envvar to specify options is deprecated and will be removed soon"
            )
            default_CXXFLAGS = shlex.split(os.environ["CXXFLAGS"])

        envs: list[CPlusPlusLanguageEnvironment] = []
        if self.config.environments:
            # configured: use specified CXX & CXXFLAGS
            for env in self.config.environments:
                CXX = env.CXX
                envs.append(
                    CPlusPlusLanguageEnvironment(
                        CXX=pathlib.Path(CXX),
                        CXXFLAGS=env.CXXFLAGS or default_CXXFLAGS,
                    )
                )

        elif "CXX" in os.environ:
            # old-style: 以前は $CXX を使ってたけど設定ファイルに移行したい
            logger.warning(
                "Usage of $CXX envvar to restrict compilers is deprecated and will be removed soon"
            )
            envs.append(
                CPlusPlusLanguageEnvironment(
                    CXX=pathlib.Path(os.environ["CXX"]), CXXFLAGS=default_CXXFLAGS
                )
            )

        else:
            # default: use found compilers
            for name in ("g++", "clang++"):
                path = shutil.which(name)
                if path is not None:
                    envs.append(
                        CPlusPlusLanguageEnvironment(
                            CXX=pathlib.Path(path), CXXFLAGS=default_CXXFLAGS
                        )
                    )

        if not envs:
            raise RuntimeError("No C++ compilers found")
        return envs

    def list_attributes(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> dict[str, Any]:
        attributes: dict[str, Any] = {}

        comments = special_comments.list_special_comments(path.resolve())
        if comments:
            attributes.update(comments)
        else:
            # use old-style if special comments not found
            # #define PROBLEM "https://..." の形式は複数 environments との相性がよくない。あと遅い
            attributes[_NOT_SPECIAL_COMMENTS] = ""
            all_ignored = True
            for env in self._list_environments():
                joined_CXXFLAGS = " ".join(
                    map(shlex.quote, [*env.cxx_flags, "-I", str(basedir)])
                )
                macros = _cplusplus_list_defined_macros(
                    path.resolve(), CXX=env.cxx, joined_CXXFLAGS=joined_CXXFLAGS
                )

                # convert macros to attributes
                if _IGNORE not in macros:
                    if _STANDALONE in macros:
                        attributes[_STANDALONE] = ""

                    for key in [_PROBLEM, _ERROR]:
                        if all_ignored:
                            # the first non-ignored environment
                            if key in macros:
                                attributes[key] = macros[key]
                        else:
                            assert attributes.get(key) == macros.get(key)
                    all_ignored = False
                else:
                    if env.is_gcc():
                        attributes[_IGNORE_IF_GCC] = ""
                    elif env.is_clang():
                        attributes[_IGNORE_IF_CLANG] = ""
                    else:
                        attributes[_IGNORE] = ""
            if all_ignored:
                attributes[_IGNORE] = ""

        attributes.setdefault("links", [])
        attributes["links"].extend(special_comments.list_embedded_urls(path))
        return attributes

    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        env = self._list_environments()[0]
        joined_CXXFLAGS = " ".join(
            map(shlex.quote, [*env.cxx_flags, "-I", str(basedir)])
        )
        return _cplusplus_list_depending_files(
            path.resolve(), CXX=env.cxx, joined_CXXFLAGS=joined_CXXFLAGS
        )

    def bundle(self, path: pathlib.Path, *, basedir: pathlib.Path) -> Optional[bytes]:
        include_paths: list[pathlib.Path] = [basedir]
        assert isinstance(include_paths, list)
        bundler = Bundler(iquotes=include_paths)
        bundler.update(path)
        return bundler.get()

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[CPlusPlusLanguageEnvironment]:
        attributes = self.list_attributes(path, basedir=basedir)
        envs: list[CPlusPlusLanguageEnvironment] = []
        for env in self._list_environments():
            if env.is_gcc() and _IGNORE_IF_GCC in attributes:
                continue
            if env.is_clang() and _IGNORE_IF_CLANG in attributes:
                continue
            envs.append(env)
        return envs
