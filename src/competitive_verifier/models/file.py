import pathlib
from functools import cached_property
from logging import getLogger
from typing import Any, Optional, Union

import competitive_verifier.models.command as command
from competitive_verifier.models.command import VerificationCommand
from competitive_verifier.models.scc import SccGraph

PathLike = Union[str, pathlib.Path]
logger = getLogger(__name__)


class VerificationFile:
    path: pathlib.Path
    display_path: pathlib.Path
    dependencies: list[pathlib.Path]
    verification: list[VerificationCommand]

    def __init__(
        self,
        path: PathLike,
        *,
        dependencies: Optional[list[PathLike]],
        verification: Optional[
            Union[VerificationCommand, list[VerificationCommand]]
        ] = None,
        display_path: Optional[PathLike] = None,
    ):
        self.path = pathlib.Path(path)
        self.display_path = pathlib.Path(display_path) if display_path else self.path
        self.dependencies = list(map(pathlib.Path, dependencies or []))

        if isinstance(verification, list):
            self.verification = verification
        elif isinstance(verification, VerificationCommand):
            self.verification = [verification]
        else:
            self.verification = []

    def __repr__(self) -> str:
        args = ",".join(
            (
                repr(str(self.path)),
                "dependencies=" + repr([list(map(str, self.dependencies))]),
                "verification=" + repr(self.verification),
            )
        )
        return f"VerificationFile({args})"

    @property
    def is_verification(self) -> bool:
        return bool(self.verification)


class VerificationInput:
    pre_command: str
    files: list[VerificationFile]
    _cached_resolve_dependencies: Optional[dict[pathlib.Path, set[pathlib.Path]]]

    def __init__(
        self,
        *,
        files: list[VerificationFile],
        pre_command: Optional[str] = None,
    ):
        self.pre_command = pre_command or ""
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


def decode_verification_files(d: dict[Any, Any]) -> VerificationInput:
    def decode_verification(
        d: Optional[dict[Any, Any]]
    ) -> Optional[VerificationCommand]:
        return command.decode(d) if d else None

    return VerificationInput(
        pre_command=d.get("pre_command"),
        files=[
            VerificationFile(
                pathlib.Path(f["path"]),
                dependencies=f.get("dependencies"),
                verification=decode_verification(f.get("verification")),
            )
            for f in d["files"]
        ],
    )
