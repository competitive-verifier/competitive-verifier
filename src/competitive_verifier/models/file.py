import pathlib
from functools import cached_property
from logging import getLogger
from typing import Any, Union

from pydantic import BaseModel, Field, field_validator

from competitive_verifier.models.path import ForcePosixPath
from competitive_verifier.models.result import FileResult
from competitive_verifier.util import to_relative

from ._scc import SccGraph
from .verification import Verification

logger = getLogger(__name__)

_DependencyEdges = dict[pathlib.Path, set[pathlib.Path]]


class AddtionalSource(BaseModel):
    name: str
    """Source type
    """
    path: ForcePosixPath
    """Source file path
    """


class VerificationFile(BaseModel):
    dependencies: set[ForcePosixPath] = Field(default_factory=set)
    verification: list[Verification] = Field(default_factory=list)
    document_attributes: dict[str, Any] = Field(default_factory=dict)
    """Attributes for documentation
    """
    additonal_sources: list[AddtionalSource] = Field(default_factory=list)
    """Addtional source paths
    """

    @field_validator("verification", mode="before")
    @classmethod
    def verification_list(cls, v: Any) -> list[Any]:
        if v is None:
            return []
        elif isinstance(v, list):
            return v  # type: ignore
        return [v]

    def is_verification(self) -> bool:
        return bool(self.verification)

    def is_skippable_verification(self) -> bool:
        """
        If verification cost is small, it is skippable.
        """
        return self.is_verification() and all(v.is_skippable for v in self.verification)


class VerificationInput(BaseModel):
    files: dict[ForcePosixPath, VerificationFile] = Field(default_factory=dict)

    def merge(self, other: "VerificationInput") -> "VerificationInput":
        return VerificationInput(files=self.files | other.files)

    @staticmethod
    def parse_file_relative(
        path: Union[str, pathlib.Path], **kwargs: Any
    ) -> "VerificationInput":
        with pathlib.Path(path).open("rb") as p:
            impl = VerificationInput.model_validate_json(p.read(), **kwargs)
        new_files: dict[pathlib.Path, VerificationFile] = {}
        for p, f in impl.files.items():
            p = to_relative(p)
            if not p:
                continue
            f.dependencies = set(d for d in map(to_relative, f.dependencies) if d)
            new_files[p] = f

        impl.files = new_files
        return impl

    def scc(self, *, reversed: bool = False) -> list[set[pathlib.Path]]:
        """Strongly Connected Component

        Args:
            reversed bool: if True, libraries are ahead. otherwise, tests are ahead.

        Returns:
            list[set[pathlib.Path]]: Strongly Connected Component result
        """
        paths = list(p for p in self.files.keys())
        vers_rev = {v: i for i, v in enumerate(paths)}
        g = SccGraph(len(paths))
        for p, file in self.files.items():
            for e in file.dependencies:
                t = vers_rev.get(e, -1)
                if 0 <= t:
                    if reversed:
                        g.add_edge(t, vers_rev[p])
                    else:
                        g.add_edge(vers_rev[p], t)
        return [set(paths[ix] for ix in ls) for ls in g.scc()]

    @cached_property
    def transitive_depends_on(self) -> _DependencyEdges:
        d: _DependencyEdges = {}
        g = self.scc(reversed=True)
        for group in g:
            result = group.copy()
            for p in group:
                for dep in self.files[p].dependencies:
                    if dep not in result:
                        resolved = d.get(dep)
                        if resolved is not None:
                            result.update(resolved)
            for p in group:
                d[p] = result

        return d

    def _build_dependency_graph(
        self,
    ) -> tuple[_DependencyEdges, _DependencyEdges, _DependencyEdges]:
        """
        Returns: Dependency graphs
        """
        depends_on: _DependencyEdges = {}
        required_by: _DependencyEdges = {}
        verified_with: _DependencyEdges = {}

        # initialize
        for path in self.files.keys():
            depends_on[path] = set()
            required_by[path] = set()
            verified_with[path] = set()

        # build the graph
        for src, vf in self.files.items():
            for dst in vf.dependencies:
                if src == dst:
                    continue
                if dst not in depends_on:
                    msg = (
                        "The file `%s` which is depended from `%s` is ignored "
                        "because it's not listed as a source code file."
                    )
                    logger.warning(msg, dst, src)
                    continue

                depends_on[src].add(dst)
                if vf.is_verification():
                    verified_with[dst].add(src)
                else:
                    required_by[dst].add(src)

        return depends_on, required_by, verified_with

    def _init_dependency_graph(self) -> None:
        (
            self._depends_on,
            self._required_by,
            self._verified_with,
        ) = self._build_dependency_graph()

    @property
    def depends_on(self) -> _DependencyEdges:
        try:
            d = self._depends_on
        except AttributeError:
            self._init_dependency_graph()
            d = self._depends_on
        return d

    @property
    def required_by(self) -> _DependencyEdges:
        try:
            d = self._required_by
        except AttributeError:
            self._init_dependency_graph()
            d = self._required_by
        return d

    @property
    def verified_with(self) -> _DependencyEdges:
        try:
            d = self._verified_with
        except AttributeError:
            self._init_dependency_graph()
            d = self._verified_with
        return d

    def filterd_files(self, files: dict[ForcePosixPath, FileResult]):
        for k, v in files.items():
            if k in self.files:
                yield k, v
