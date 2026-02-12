# Python Version: 3.x
import functools
import pathlib
from collections.abc import Generator
from logging import getLogger

from pydantic import BaseModel, Field

from competitive_verifier.oj.verify.models import (
    Language,
    LanguageEnvironment,
    OjVerifyLanguageConfig,
)
from competitive_verifier.util import read_text_normalized

logger = getLogger(__name__)

DEFAULT_COMPILE_TO = "cpp"
DEFAULT_NIM_FLAGS = ["-d:release", "--opt:speed"]


class OjVerifyNimConfigEnv(BaseModel):
    compile_to: str | None
    NIMFLAGS: list[str] | None


class OjVerifyNimConfig(OjVerifyLanguageConfig):
    environments: list[OjVerifyNimConfigEnv] = Field(
        default_factory=list[OjVerifyNimConfigEnv]
    )


class NimLanguageEnvironment(LanguageEnvironment):
    compile_to: str
    nim_flags: list[str]

    def __init__(self, *, compile_to: str, nim_flags: list[str]):
        self.compile_to = compile_to
        self.nim_flags = nim_flags

    @property
    def name(self) -> str:
        return "Nim"

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> list[str]:
        return [
            "nim",
            self.compile_to,
            "-p:.",
            f"-o:{tempdir / 'a.out'!s}",
            f"--nimcache:{tempdir!s}",
            *self.nim_flags,
            str(path),
        ]

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return str(tempdir / "a.out")


def _parse_path(lines: list[str]) -> Generator[str, None, None]:
    for line in lines:
        l = line.strip()
        if l.startswith("include"):
            yield from l[7:].strip().split(",")
        elif l.startswith("import"):
            l = l[6:]
            i = l.find(" except ")
            if i >= 0:
                l = l[:i]
            yield from l.split(",")
        elif l.startswith("from"):
            i = l.find(" import ")
            if i >= 0:
                yield l[4 : i - 1]


def _unquote_path(p: str) -> pathlib.Path:
    p = p.strip()
    if p.startswith('"'):
        p = p[1 : len(p) - 1]
    else:
        p += ".nim"
    return pathlib.Path(p)


@functools.cache
def _list_direct_dependencies(
    path: pathlib.Path,
    *,
    basedir: pathlib.Path,
) -> list[pathlib.Path]:
    dependencies = [path.resolve()]
    for item in _parse_path(read_text_normalized(basedir / path).splitlines()):
        item_ = _unquote_path(item)
        if item_.exists():
            dependencies.append(item_)
    return list(set(dependencies))


class NimLanguage(Language):
    config: OjVerifyNimConfig

    def __init__(self, *, config: OjVerifyNimConfig | None):
        self.config = config or OjVerifyNimConfig()

    def list_dependencies(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[pathlib.Path]:
        dependencies: list[pathlib.Path] = []
        visited: set[pathlib.Path] = set()
        stk = [path.resolve()]
        while stk:
            path = stk.pop()
            if path in visited:
                continue
            visited.add(path)
            for child in _list_direct_dependencies(path, basedir=basedir):
                dependencies.append(child)
                stk.append(child)
        return list(set(dependencies))

    def list_environments(
        self, path: pathlib.Path, *, basedir: pathlib.Path
    ) -> list[NimLanguageEnvironment]:
        if self.config.environments:
            return [
                NimLanguageEnvironment(
                    compile_to=DEFAULT_COMPILE_TO,
                    nim_flags=DEFAULT_NIM_FLAGS,
                )
            ]
        return [
            NimLanguageEnvironment(
                compile_to=env.compile_to or DEFAULT_COMPILE_TO,
                nim_flags=env.NIMFLAGS or DEFAULT_NIM_FLAGS,
            )
            for env in self.config.environments
        ]
