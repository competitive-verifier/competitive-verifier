import pathlib
from functools import cached_property
from logging import getLogger
from typing import Any, Optional, Union

from pydantic import BaseModel, Field, StrBytes, validator

from competitive_verifier.util import to_relative

from ._scc import SccGraph
from .verification import Verification

logger = getLogger(__name__)

_DependencyEdges = dict[pathlib.Path, set[pathlib.Path]]


class AddtionalSource(BaseModel):
    name: str
    """Source type
    """
    path: pathlib.Path
    """Source file path
    """


class VerificationFile(BaseModel):
    dependencies: set[pathlib.Path] = Field(default_factory=set)
    verification: list[Verification] = Field(default_factory=list)
    document_attributes: dict[str, Any] = Field(default_factory=dict)
    """Attributes for documentation
    """
    additonal_sources: list[AddtionalSource] = Field(default_factory=list)
    """Addtional source paths
    """

    class Config:
        json_encoders = {pathlib.Path: lambda v: v.as_posix()}  # type: ignore

    @validator("verification", pre=True)
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


# NOTE: computed fields  https://github.com/pydantic/pydantic/pull/2625
class VerificationInputImpl(BaseModel):
    files: dict[pathlib.Path, VerificationFile] = Field(default_factory=dict)

    def json(self, **kwargs: Any) -> str:
        class WithStrDict(BaseModel):
            files: dict[str, VerificationFile] = Field(default_factory=dict)

            class Config:
                json_encoders = {pathlib.Path: lambda v: v.as_posix()}  # type: ignore

        return WithStrDict(
            files={k.as_posix(): v for k, v in self.files.items()},
        ).json(**kwargs)


class VerificationInput:
    impl: VerificationInputImpl

    def __init__(
        self,
        impl: Optional[VerificationInputImpl] = None,
        *,
        files: Optional[dict[pathlib.Path, VerificationFile]] = None,
    ) -> None:
        if not impl:
            impl = VerificationInputImpl(
                files=files,  # type: ignore
            )
        self.impl = impl

    def merge(self, other: "VerificationInput") -> "VerificationInput":
        return VerificationInput(files=self.files | other.files)

    @property
    def files(self) -> dict[pathlib.Path, VerificationFile]:
        return self.impl.files

    def __repr__(self) -> str:
        return "VerificationInput" + repr(self.impl)[len("VerificationInputImpl") :]

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VerificationInput):
            return self.impl == other.impl
        elif isinstance(other, VerificationInputImpl):
            return self.impl == other
        return NotImplemented

    def dict(self, **kwargs: Any) -> dict[str, Any]:
        return self.impl.dict(**kwargs)

    def json(self, **kwargs: Any) -> str:
        return self.impl.json(**kwargs)

    @staticmethod
    def parse_raw(b: StrBytes, **kwargs: Any) -> "VerificationInput":
        return VerificationInput(VerificationInputImpl.parse_raw(b, **kwargs))

    @staticmethod
    def parse_file_relative(
        path: Union[str, pathlib.Path], **kwargs: Any
    ) -> "VerificationInput":
        impl = VerificationInputImpl.parse_file(path, **kwargs)
        new_files: dict[pathlib.Path, VerificationFile] = {}
        for p, f in impl.files.items():
            p = to_relative(p)
            if not p:
                continue
            f.dependencies = set(d for d in map(to_relative, f.dependencies) if d)
            new_files[p] = f

        impl.files = new_files
        return VerificationInput(impl)

    @staticmethod
    def parse_obj(obj: Any) -> "VerificationInput":
        return VerificationInput(VerificationInputImpl.parse_obj(obj))

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
