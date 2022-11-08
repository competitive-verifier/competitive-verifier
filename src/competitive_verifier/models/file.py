import pathlib
from functools import cached_property
from logging import getLogger
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, StrBytes, validator

from ._scc import SccGraph
from .verification import Verification

logger = getLogger(__name__)


class VerificationFile(BaseModel):
    display_path: Union[pathlib.Path, Literal[False], None] = None
    dependencies: list[pathlib.Path] = Field(default_factory=list)
    verification: list[Verification] = Field(default_factory=list)

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
    def parse_file(
        path: Union[str, pathlib.Path], **kwargs: Any
    ) -> "VerificationInput":
        return VerificationInput(VerificationInputImpl.parse_file(path, **kwargs))

    @staticmethod
    def parse_obj(obj: Any) -> "VerificationInput":
        return VerificationInput(VerificationInputImpl.parse_obj(obj))

    def _scc(self) -> list[set[pathlib.Path]]:
        paths = list(p for p in self.files.keys())
        vers_rev = {v: i for i, v in enumerate(paths)}
        g = SccGraph(len(paths))
        for p, file in self.files.items():
            for e in file.dependencies:
                t = vers_rev.get(e, -1)
                if 0 <= t:
                    g.add_edge(vers_rev[p], t)
        return [set(paths[ix] for ix in ls) for ls in reversed(g.scc())]

    @cached_property
    def _all_dependencies(self) -> "dict[pathlib.Path, set[pathlib.Path]]":
        d = dict[pathlib.Path, set[pathlib.Path]]()
        g = self._scc()
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

    def transitive_depends_on(self, path: pathlib.Path) -> set[pathlib.Path]:
        return self._all_dependencies[path]

    def _build_dependency_graph(
        self,
    ) -> """tuple[
        dict[pathlib.Path, set[pathlib.Path]],
        dict[pathlib.Path, set[pathlib.Path]],
        dict[pathlib.Path, set[pathlib.Path]],
    ]""":
        """
        :returns: graphs from absolute paths to relative paths
        """
        depends_on: dict[pathlib.Path, set[pathlib.Path]] = {}
        required_by: dict[pathlib.Path, set[pathlib.Path]] = {}
        verified_with: dict[pathlib.Path, set[pathlib.Path]] = {}

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

    def depends_on(self, path: pathlib.Path) -> set[pathlib.Path]:
        try:
            d = self._depends_on
        except AttributeError:
            self._init_dependency_graph()
            d = self._depends_on
        return d[path]

    def required_by(self, path: pathlib.Path) -> set[pathlib.Path]:
        try:
            d = self._required_by
        except AttributeError:
            self._init_dependency_graph()
            d = self._required_by
        return d[path]

    def verified_with(self, path: pathlib.Path) -> set[pathlib.Path]:
        try:
            d = self._verified_with
        except AttributeError:
            self._init_dependency_graph()
            d = self._verified_with
        return d[path]
