# Python Version: 3.x
import functools
import pathlib
from logging import getLogger
from typing import Optional

from pydantic import BaseModel, Field

import competitive_verifier.oj.verify.shlex2 as shlex
from competitive_verifier.oj.verify.models import (
    Language,
    LanguageEnvironment,
    OjVerifyLanguageConfig,
)
from competitive_verifier.oj.verify.utils import read_text_normalized

logger = getLogger(__name__)


class OjVerifyNimConfigEnv(BaseModel):
    compile_to: Optional[str]
    NIMFLAGS: Optional[list[str]]


class OjVerifyNimConfig(OjVerifyLanguageConfig):
    environments: list[OjVerifyNimConfigEnv] = Field(default_factory=list)


class NimLanguageEnvironment(LanguageEnvironment):
    compile_to: str
    nim_flags: list[str]

    def __init__(self, *, compile_to: str, NIMFLAGS: list[str]):
        self.compile_to = compile_to
        self.nim_flags = NIMFLAGS

    @property
    def name(self) -> str:
        return "Nim"

    def get_compile_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return shlex.join(
            [
                "nim",
                self.compile_to,
                "-p:.",
                f"-o:{str(tempdir / 'a.out')}",
                f"--nimcache:{str(tempdir)}",
            ]
            + self.nim_flags
            + [str(path)]
        )

    def get_execute_command(
        self, path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return str(tempdir / "a.out")


@functools.lru_cache(maxsize=None)
def _list_direct_dependencies(
    path: pathlib.Path, *, basedir: pathlib.Path
) -> list[pathlib.Path]:
    items: list[str] = []
    for line in read_text_normalized(basedir / path).splitlines():
        line = line.strip()
        if line.startswith("include"):
            items += line[7:].strip().split(",")
        elif line.startswith("import"):
            line = line[6:]
            i = line.find(" except ")
            if i >= 0:
                line = line[:i]
            items += line.split(",")
        elif line.startswith("from"):
            i = line.find(" import ")
            if i >= 0:
                items += line[4 : i - 1]
    dependencies = [path.resolve()]
    for item in items:
        item = item.strip()
        if item.startswith('"'):
            item = item[1 : len(item) - 1]
        else:
            item += ".nim"
        item_ = pathlib.Path(item)
        if item_.exists():
            dependencies.append(item_)
    return list(set(dependencies))


class NimLanguage(Language):
    config: OjVerifyNimConfig

    def __init__(self, *, config: Optional[OjVerifyNimConfig]):
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
        default_compile_to = "cpp"
        default_NIMFLAGS = ["-d:release", "--opt:speed"]
        if self.config.environments:
            return [
                NimLanguageEnvironment(
                    compile_to=default_compile_to,
                    NIMFLAGS=default_NIMFLAGS,
                )
            ]
        else:
            return [
                NimLanguageEnvironment(
                    compile_to=env.compile_to or default_compile_to,
                    NIMFLAGS=env.NIMFLAGS or default_NIMFLAGS,
                )
                for env in self.config.environments
            ]
