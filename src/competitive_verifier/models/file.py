import pathlib
from functools import cached_property
from typing import AbstractSet, Any, Callable, Literal, Mapping, Optional, Union

from pydantic import BaseModel, Field, Protocol, StrBytes, validator

from competitive_verifier.models._scc import SccGraph
from competitive_verifier.models.command import Command

_IntStr = Union[int, str]
_AbstractSetIntStr = AbstractSet[_IntStr]
_MappingIntStrAny = Mapping[_IntStr, Any]


class VerificationFile(BaseModel):
    path: pathlib.Path
    display_path: Union[pathlib.Path, Literal[False], None] = None
    dependencies: list[pathlib.Path] = Field(default_factory=list)
    verification: list[Command] = Field(default_factory=list)

    @validator("verification", pre=True)
    def verification_list(cls, v: Any) -> list[Any]:
        if isinstance(v, list):
            return v  # type: ignore
        return [v]

    def is_verification(self) -> bool:
        return bool(self.verification)


# NOTE: computed fields  https://github.com/pydantic/pydantic/pull/2625
class VerificationInputImpl(BaseModel):
    pre_command: Optional[list[str]] = None
    files: list[VerificationFile] = Field(default_factory=list)

    @validator("pre_command", pre=True)
    def pre_command_list(cls, v: Any) -> list[Any]:
        if isinstance(v, list):
            return v  # type: ignore
        return [v]


class VerificationInput:
    impl: VerificationInputImpl

    def __init__(
        self,
        impl: Optional[VerificationInputImpl] = None,
        *,
        pre_command: Union[str, list[str], None] = None,
        files: Optional[list[VerificationFile]] = None,
    ) -> None:
        if impl:
            self.impl = impl
        else:
            self.impl = VerificationInputImpl(
                pre_command=pre_command,  # type: ignore
                files=files,  # type: ignore
            )

    def __repr__(self) -> str:
        return repr(self.impl)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, VerificationInput):
            return self.impl == other.impl
        elif isinstance(other, VerificationInputImpl):
            return self.impl == other
        return NotImplemented

    def dict(
        self,
        *,
        include: Optional[Union[_AbstractSetIntStr, _MappingIntStrAny]] = None,
        exclude: Optional[Union[_AbstractSetIntStr, _MappingIntStrAny]] = None,
        by_alias: bool = False,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
    ) -> dict[str, Any]:
        return self.impl.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

    def json(
        self,
        *,
        include: Optional[Union[_AbstractSetIntStr, _MappingIntStrAny]] = None,
        exclude: Optional[Union[_AbstractSetIntStr, _MappingIntStrAny]] = None,
        by_alias: bool = False,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        encoder: Optional[Callable[[Any], Any]] = None,
        models_as_dict: bool = True,
        **dumps_kwargs: Any,
    ) -> str:
        return self.impl.json(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
            encoder=encoder,
            models_as_dict=models_as_dict,
            **dumps_kwargs,
        )

    @staticmethod
    def parse_raw(
        b: StrBytes,
        *,
        content_type: str = None,  # type: ignore
        encoding: str = "utf8",
        proto: Protocol = None,  # type: ignore
        allow_pickle: bool = False,
    ) -> "VerificationInput":
        return VerificationInput(
            VerificationInputImpl.parse_raw(
                b,
                content_type=content_type,
                encoding=encoding,
                proto=proto,
                allow_pickle=allow_pickle,
            )
        )

    @staticmethod
    def parse_file(
        path: Union[str, pathlib.Path],
        *,
        content_type: str = None,  # type: ignore
        encoding: str = "utf8",
        proto: Protocol = None,  # type: ignore
        allow_pickle: bool = False,
    ) -> "VerificationInput":
        return VerificationInput(
            VerificationInputImpl.parse_file(
                path,
                content_type=content_type,
                encoding=encoding,
                proto=proto,
                allow_pickle=allow_pickle,
            )
        )

    @staticmethod
    def parse_obj(obj: Any) -> "VerificationInput":
        return VerificationInput(VerificationInputImpl.parse_obj(obj))

    @property
    def pre_command(self) -> Optional[list[str]]:
        return self.impl.pre_command

    @property
    def files(self) -> list[VerificationFile]:
        return self.impl.files

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
        return self._all_dependencies[path]

    @cached_property
    def files_dict(self) -> "dict[pathlib.Path, VerificationFile]":
        return {f.path: f for f in self.files}

    @cached_property
    def _all_dependencies(self) -> "dict[pathlib.Path, set[pathlib.Path]]":
        d = dict[pathlib.Path, set[pathlib.Path]]()
        g = self._scc()
        for group in g:
            result = group.copy()
            for p in group:
                for dep in self.files_dict[p].dependencies:
                    if dep not in result:
                        resolved = d.get(dep)
                        if resolved is not None:
                            result.update(resolved)
            for p in group:
                d[p] = result

        return d
