import pathlib
from functools import cached_property
from logging import getLogger
from typing import Any, Optional

import competitive_verifier.models.command as command
from competitive_verifier.models.command import VerificationCommand
from competitive_verifier.models.scc import SccGraph

logger = getLogger(__name__)


class VerificationFile:
    path: pathlib.Path
    dependencies: list[pathlib.Path]
    verification: Optional[VerificationCommand]

    def __init__(
        self,
        path: pathlib.Path,
        *,
        dependencies: list[pathlib.Path],
        verification: Optional[VerificationCommand] = None,
    ):
        self.path = path
        self.dependencies = dependencies
        self.verification = verification


class VerificationFiles:
    files: list[VerificationFile]
    _cached_resolve_dependencies: Optional[dict[pathlib.Path, set[pathlib.Path]]]

    def __init__(self, *, files: list[VerificationFile]):
        self.files = files
        self._cached_resolve_dependencies = None

    @cached_property
    def files_dict(self) -> dict[pathlib.Path, VerificationFile]:
        return {f.path: f for f in self.files}

    def _scc(self) -> list[set[pathlib.Path]]:
        vers_rev = {v.path: i for i, v in enumerate(self.files)}
        g = SccGraph(len(self.files))
        for file in self.files:
            for e in file.dependencies:
                t = vers_rev.get(e, -1)
                if 0 <= t:
                    g.add_edge(vers_rev[file.path], t)
        return [set(self.files[ix].path for ix in ls) for ls in reversed(g.scc())]

    def resolve_dependencies(self, path: pathlib.Path) -> set[pathlib.Path]:
        cached = self._cached_resolve_dependencies
        if cached:
            return cached[path]

        self._cached_resolve_dependencies = dict()
        g = self._scc()
        for group in g:
            result = group.copy()
            for p in group:
                for dep in self.files_dict[p].dependencies:
                    if dep not in result:
                        resolved = self._cached_resolve_dependencies.get(dep)
                        if resolved is not None:
                            result.update(resolved)
            for p in group:
                self._cached_resolve_dependencies[p] = result

        return self._cached_resolve_dependencies[path]


def decode_verification_files(d: dict[Any, Any]) -> VerificationFiles:
    def decode_verification(
        d: Optional[dict[Any, Any]]
    ) -> Optional[VerificationCommand]:
        return command.decode(d) if d else None

    return VerificationFiles(
        files=[
            VerificationFile(
                f["path"],
                dependencies=f["dependencies"],
                verification=decode_verification(f.get("verification")),
            )
            for f in d["files"]
        ]
    )
