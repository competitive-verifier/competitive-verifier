import enum
import pathlib
from functools import cached_property
from logging import getLogger
from typing import TYPE_CHECKING, Any, NamedTuple, Optional, Union

from pydantic import BaseModel, Field

from competitive_verifier.util import to_relative

from ._scc import SccGraph
from .path import ForcePosixPath, SortedPathSet
from .result import FileResult
from .verification import Verification

if TYPE_CHECKING:
    from _typeshed import StrPath
logger = getLogger(__name__)

_DependencyEdges = dict[pathlib.Path, set[pathlib.Path]]


class _DependencyGraph(NamedTuple):
    depends_on: _DependencyEdges
    required_by: _DependencyEdges
    verified_with: _DependencyEdges


class DocumentOutputMode(str, enum.Enum):
    visible = "visible"
    """The document will be output. (default)
    """

    hidden = "hidden"
    """The document will be output but will not linked from other pages.
    """

    no_index = "no-index"
    """The document will be output but will not linked from index page.
    """

    never = "never"
    """The document will be never output.
    """


class AddtionalSource(BaseModel):
    name: str = Field(
        examples=["source_name"],
        description="The name of source file.",
    )
    """The name of source file.
    """
    path: ForcePosixPath = Field(
        description="The path source file.",
        examples=["relative_path_of_directory/file_name.cpp"],
    )
    """The path source file.
    """


class VerificationFile(BaseModel):
    dependencies: SortedPathSet = Field(
        default_factory=set,
        description="The list of dependent files as paths relative to root.",
    )
    """The list of dependent files as paths relative to root.
    """
    verification: Union[list[Verification], Verification, None] = Field(
        default_factory=list
    )
    document_attributes: dict[str, Any] = Field(
        default_factory=dict,
        description="The attributes for documentation.",
    )
    """The attributes for documentation.
    """
    additonal_sources: list[AddtionalSource] = Field(
        default_factory=list,
        description="The addtional source paths.",
        examples=[
            [
                AddtionalSource(
                    name="source_name",
                    path=pathlib.Path("relative_path_of_directory/file_name.cpp"),
                ),
            ],
        ],
    )
    """The addtional source paths
    """

    @property
    def title(self) -> Optional[str]:
        """The document title specified as a attributes"""
        title = self.document_attributes.get("TITLE")
        if not title:
            title = self.document_attributes.get("document_title")
        return title

    @property
    def display(self) -> Optional[DocumentOutputMode]:
        """The document output mode as a attributes"""

        d = self.document_attributes.get("DISPLAY")
        if not isinstance(d, str):
            return None
        try:
            return DocumentOutputMode[d.lower().replace("-", "_")]
        except KeyError:
            return None

    @property
    def verification_list(self) -> list[Verification]:
        if self.verification is None:
            return []
        elif isinstance(self.verification, list):
            return self.verification
        return [self.verification]

    def is_verification(self) -> bool:
        return bool(self.verification)

    def is_skippable_verification(self) -> bool:
        """If the effort required for verification is small, treat it as skippable."""
        return self.is_verification() and all(
            v.is_skippable for v in self.verification_list
        )


class VerificationInput(BaseModel):
    files: dict[ForcePosixPath, VerificationFile] = Field(
        default_factory=dict,
        description="The key is relative path from the root.",
    )

    def merge(self, other: "VerificationInput") -> "VerificationInput":
        return VerificationInput(files=self.files | other.files)

    @staticmethod
    def parse_file_relative(path: "StrPath", **kwargs: Any) -> "VerificationInput":
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

    @cached_property
    def _dependency_graph(
        self,
    ) -> _DependencyGraph:
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
        return _DependencyGraph(
            depends_on=depends_on,
            required_by=required_by,
            verified_with=verified_with,
        )

    @property
    def depends_on(self) -> _DependencyEdges:
        return self._dependency_graph.depends_on

    @property
    def required_by(self) -> _DependencyEdges:
        return self._dependency_graph.required_by

    @property
    def verified_with(self) -> _DependencyEdges:
        return self._dependency_graph.verified_with

    def filterd_files(self, files: dict[ForcePosixPath, "FileResult"]):
        for k, v in files.items():
            if k in self.files:
                yield k, v
