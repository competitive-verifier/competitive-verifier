import pathlib
from functools import cached_property
from typing import Any, Literal, Optional, Union

from pydantic import BaseModel, Field, StrBytes, validator

from ._scc import SccGraph
from .command import Command, DummyCommand


class VerificationFile(BaseModel):
    display_path: Union[pathlib.Path, Literal[False], None] = None
    dependencies: list[pathlib.Path] = Field(default_factory=list)
    verification: list[Command] = Field(default_factory=list)

    @validator("verification", pre=True)
    def verification_list(cls, v: Any) -> list[Any]:
        if v is None:
            return []
        elif isinstance(v, list):
            return v  # type: ignore
        return [v]

    def is_verification(self) -> bool:
        return bool(self.verification)

    def is_dummy_verification(self) -> bool:
        return self.is_verification() and all(
            isinstance(c, DummyCommand) for c in self.verification
        )


# NOTE: computed fields  https://github.com/pydantic/pydantic/pull/2625
class VerificationInputImpl(BaseModel):
    pre_command: Optional[list[str]] = None
    files: dict[pathlib.Path, VerificationFile] = Field(default_factory=dict)

    @validator("pre_command", pre=True)
    def pre_command_list(cls, v: Any) -> list[Any]:
        if v is None or isinstance(v, list):
            return v  # type: ignore
        return [v]

    def json(self, **kwargs: Any) -> str:
        class WithStrDict(BaseModel):
            pre_command: Optional[list[str]] = None
            files: dict[str, VerificationFile] = Field(default_factory=dict)

        return WithStrDict(
            pre_command=self.pre_command,
            files={k.as_posix(): v for k, v in self.files.items()},
        ).json(**kwargs)


class VerificationInput:
    impl: VerificationInputImpl

    def __init__(
        self,
        impl: Optional[VerificationInputImpl] = None,
        *,
        pre_command: Union[str, list[str], None] = None,
        files: Optional[dict[pathlib.Path, VerificationFile]] = None,
    ) -> None:
        if not impl:
            impl = VerificationInputImpl(
                pre_command=pre_command,  # type: ignore
                files=files,  # type: ignore
            )
        self.impl = impl

    @property
    def pre_command(self) -> Optional[list[str]]:
        return self.impl.pre_command

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
        paths = list(self.files.keys())
        vers_rev = {v: i for i, v in enumerate(paths)}
        g = SccGraph(len(self.files))
        for p, file in self.files.items():
            for e in file.dependencies:
                t = vers_rev.get(e, -1)
                if 0 <= t:
                    g.add_edge(vers_rev[p], t)
        return [set(paths[ix] for ix in ls) for ls in reversed(g.scc())]

    def resolve_dependencies(self, path: pathlib.Path) -> set[pathlib.Path]:
        return self._all_dependencies[path]

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
