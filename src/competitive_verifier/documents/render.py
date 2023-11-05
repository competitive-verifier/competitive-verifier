import datetime
import enum
import pathlib
from abc import ABC, abstractmethod, abstractproperty
from dataclasses import dataclass
from functools import cached_property
from logging import getLogger
from typing import AbstractSet, BinaryIO, Iterable, Optional

from pydantic import BaseModel

import competitive_verifier.git as git
import competitive_verifier.log as log
from competitive_verifier.models import (
    ForcePosixPath,
    ProblemVerification,
    ResultStatus,
    SortedPathSet,
    VerificationFile,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.util import read_text_normalized

from .front_matter import DocumentOutputMode, FrontMatter, Markdown
from .render_data import (
    CategorizedIndex,
    Dependency,
    EmbeddedCode,
    EnvTestcaseResult,
    IndexFiles,
    IndexRenderData,
    PageRenderData,
    RenderLink,
    StatusIcon,
)

logger = getLogger(__name__)


def resolve_documentation_of(
    documentation_of: str,
    *,
    basedir: pathlib.Path,
) -> Optional[pathlib.Path]:
    def inner():
        if documentation_of.startswith("."):
            # a relative path
            path = basedir / pathlib.Path(documentation_of)
            if path.exists():
                return path
        elif documentation_of.startswith("//"):
            # from the document root
            path = pathlib.Path(documentation_of[2:])
            if path.exists():
                return path

        path = pathlib.Path(documentation_of)
        if path.exists():
            return path

        path = basedir / pathlib.Path(documentation_of)
        if path.exists():
            return path

    path = inner()
    if path:
        path = path.resolve()
        if path.is_relative_to(pathlib.Path.cwd()):
            return path.relative_to(pathlib.Path.cwd())
    return None


def select_markdown(sources: set[pathlib.Path]) -> dict[pathlib.Path, Markdown]:
    d: dict[pathlib.Path, Markdown] = {}
    markdowns = [Markdown.load_file(t) for t in sources if t.suffix == ".md"]
    for md in markdowns:
        if md.path and md.front_matter and md.front_matter.documentation_of:
            documentation_of = resolve_documentation_of(
                md.front_matter.documentation_of,
                basedir=md.path.parent,
            )
            if documentation_of in sources:
                md.front_matter.documentation_of = documentation_of.as_posix()
                d[documentation_of] = md
            else:
                logger.warning(
                    "Markdown(%s) documentation_of: %s is not found.",
                    md.path,
                    md.front_matter.documentation_of,
                )
    return d


class _VerificationStatusFlag(enum.Flag):
    TEST_NOTHING = 0
    IS_LIBRARY = enum.auto()
    HAVE_AC = enum.auto()
    HAVE_WA = enum.auto()
    HAVE_SKIP = enum.auto()

    LIBRARY_AC_WA_SKIP = IS_LIBRARY | HAVE_AC | HAVE_WA | HAVE_SKIP
    LIBRARY_AC_WA = IS_LIBRARY | HAVE_AC | HAVE_WA
    LIBRARY_AC_SKIP = IS_LIBRARY | HAVE_AC | HAVE_SKIP
    LIBRARY_AC = IS_LIBRARY | HAVE_AC
    LIBRARY_WA_SKIP = IS_LIBRARY | HAVE_WA | HAVE_SKIP
    LIBRARY_WA = IS_LIBRARY | HAVE_WA
    LIBRARY_SKIP = IS_LIBRARY | HAVE_SKIP
    LIBRARY_NOTHING = IS_LIBRARY

    TEST_AC_WA_SKIP = HAVE_AC | HAVE_WA | HAVE_SKIP
    TEST_AC_WA = HAVE_AC | HAVE_WA
    TEST_AC_SKIP = HAVE_AC | HAVE_SKIP
    TEST_AC = HAVE_AC
    TEST_WA_SKIP = HAVE_WA | HAVE_SKIP
    TEST_WA = HAVE_WA
    TEST_SKIP = HAVE_SKIP

    @classmethod
    @property
    def _conv_dict(cls) -> dict["_VerificationStatusFlag", StatusIcon]:
        try:
            d: dict["_VerificationStatusFlag", StatusIcon] = cls._conv_dict_attr
        except AttributeError:
            d = {
                cls.LIBRARY_AC_WA_SKIP: StatusIcon.LIBRARY_SOME_WA,
                cls.LIBRARY_AC_WA: StatusIcon.LIBRARY_SOME_WA,
                cls.LIBRARY_AC_SKIP: StatusIcon.LIBRARY_PARTIAL_AC,
                cls.LIBRARY_AC: StatusIcon.LIBRARY_ALL_AC,
                cls.LIBRARY_WA_SKIP: StatusIcon.LIBRARY_ALL_WA,
                cls.LIBRARY_WA: StatusIcon.LIBRARY_ALL_WA,
                cls.LIBRARY_SKIP: StatusIcon.LIBRARY_NO_TESTS,
                cls.LIBRARY_NOTHING: StatusIcon.LIBRARY_NO_TESTS,
                cls.TEST_AC_WA_SKIP: StatusIcon.TEST_WRONG_ANSWER,
                cls.TEST_AC_WA: StatusIcon.TEST_WRONG_ANSWER,
                cls.TEST_AC_SKIP: StatusIcon.TEST_WAITING_JUDGE,
                cls.TEST_AC: StatusIcon.TEST_ACCEPTED,
                cls.TEST_WA_SKIP: StatusIcon.TEST_WRONG_ANSWER,
                cls.TEST_WA: StatusIcon.TEST_WRONG_ANSWER,
                cls.TEST_SKIP: StatusIcon.TEST_WAITING_JUDGE,
                cls.TEST_NOTHING: StatusIcon.TEST_WAITING_JUDGE,
            }
            cls._conv_dict_attr = d
        return d

    def to_status(self) -> StatusIcon:
        return self._conv_dict[self]


class SourceCodeStat(BaseModel):
    path: ForcePosixPath
    is_verification: bool
    verification_status: StatusIcon
    file_input: VerificationFile
    timestamp: datetime.datetime
    depends_on: SortedPathSet
    required_by: SortedPathSet
    verified_with: SortedPathSet
    verification_results: Optional[list[VerificationResult]] = None

    @staticmethod
    def resolve_dependency(
        *,
        input: VerificationInput,
        result: VerifyCommandResult,
        included_files: AbstractSet[pathlib.Path],
    ) -> dict[pathlib.Path, "SourceCodeStat"]:
        d: dict[pathlib.Path, SourceCodeStat] = {}
        statuses: dict[pathlib.Path, _VerificationStatusFlag] = {
            p: _VerificationStatusFlag.TEST_NOTHING for p in input.files.keys()
        }
        verification_results_dict: dict[pathlib.Path, list[VerificationResult]] = {}

        for p, r in result.files.items():
            if p not in included_files:
                continue
            st = _VerificationStatusFlag.TEST_NOTHING
            for v in r.verifications:
                if v.status == ResultStatus.SUCCESS:
                    st |= _VerificationStatusFlag.HAVE_AC
                elif v.status == ResultStatus.FAILURE:
                    st |= _VerificationStatusFlag.HAVE_WA
                elif v.status == ResultStatus.SKIPPED:
                    st |= _VerificationStatusFlag.HAVE_SKIP
            statuses[p] = st
            verification_results_dict[p] = r.verifications

        for group in input.scc():
            group &= included_files
            if not group:
                continue

            group_status = _VerificationStatusFlag.TEST_NOTHING

            for path in group:
                assert path in statuses
                group_status |= statuses[path]

            for path in group:
                depends_on = input.depends_on[path] & included_files
                required_by = input.required_by[path] & included_files
                verified_with = input.verified_with[path] & included_files

                for dep in depends_on:
                    statuses[dep] |= group_status

                timestamp = git.get_commit_time(input.transitive_depends_on[path])
                file_input = input.files[path]
                is_verification = file_input.is_verification()

                verification_results = verification_results_dict.get(path)

                assert not is_verification or verification_results is not None

                flag_status = group_status
                if not is_verification:
                    flag_status |= _VerificationStatusFlag.IS_LIBRARY

                d[path] = SourceCodeStat(
                    path=path,
                    file_input=file_input,
                    is_verification=is_verification,
                    depends_on=depends_on,
                    required_by=required_by,
                    verified_with=verified_with,
                    timestamp=timestamp,
                    verification_status=flag_status.to_status(),
                    verification_results=verification_results,
                )
        return d


@dataclass
class RenderJob(ABC):
    def render(self, dst: pathlib.Path):
        file = dst / self.destination_name
        file.mkdir(parents=True, exist_ok=True)
        with file.open("rb") as fp:
            self.write_to(fp)

    @abstractproperty
    def destination_name(self) -> pathlib.Path:
        ...

    @abstractmethod
    def write_to(self, fp: BinaryIO):
        ...

    @staticmethod
    def enumerate_jobs(
        *,
        sources: set[pathlib.Path],
        input: VerificationInput,
        result: VerifyCommandResult,
        index_md: Optional[Markdown] = None,
    ) -> list["RenderJob"]:
        def plain_content(source: pathlib.Path) -> Optional[RenderJob]:
            if source.suffix == ".md":
                md = Markdown.load_file(source)
                if md.front_matter is None or md.front_matter.documentation_of is None:
                    return MarkdownRenderJob(
                        source_path=source,
                        markdown=md,
                    )
                return None
            elif source.suffix == ".html":
                return PlainRenderJob(
                    source_path=source,
                    content=source.read_bytes(),
                )
            return None

        markdown_dict = select_markdown(sources)

        logger.info(" %s source files...", len(sources))

        class SourceForDebug(BaseModel):
            sources: SortedPathSet
            markdowns: dict[ForcePosixPath, Markdown]

        logger.debug(
            "source: %s",
            SourceForDebug(
                sources=sources,
                markdowns=markdown_dict,
            ),
        )
        with log.group("Resolve dependency"):
            stats_dict = SourceCodeStat.resolve_dependency(
                input=input,
                result=result,
                included_files=sources,
            )

        page_jobs: dict[pathlib.Path, PageRenderJob] = {}
        jobs: list[RenderJob] = []
        for source in sources:
            markdown = markdown_dict.get(source) or Markdown.make_default(source)
            stat = stats_dict.get(source)
            if not stat:
                plain_job = plain_content(source)
                if plain_job is not None:
                    jobs.append(plain_job)
                elif source.suffix != ".md":
                    logger.info("Skip file: %s", source.as_posix())
                continue
            if (
                markdown.front_matter
                and markdown.front_matter.display == DocumentOutputMode.never
            ):
                continue
            pj = PageRenderJob(
                source_path=source,
                markdown=markdown,
                stat=stat,
                input=input,
                result=result,
                page_jobs=page_jobs,
            )
            page_jobs[pj.source_path] = pj
            jobs.append(pj)

        jobs.append(
            IndexRenderJob(
                page_jobs=page_jobs,
                index_md=index_md,
            )
        )
        return jobs


@dataclass
class PlainRenderJob(RenderJob):
    source_path: ForcePosixPath
    content: bytes

    @property
    def destination_name(self):
        return self.source_path

    def write_to(self, fp: BinaryIO):
        fp.write(self.content)


@dataclass
class MarkdownRenderJob(RenderJob):
    source_path: ForcePosixPath
    markdown: Markdown

    @property
    def destination_name(self):
        return self.source_path

    def write_to(self, fp: BinaryIO):
        self.markdown.dump_merged(fp)


@dataclass
class PageRenderJob(RenderJob):
    source_path: ForcePosixPath
    markdown: Markdown
    stat: SourceCodeStat
    input: VerificationInput
    result: VerifyCommandResult
    page_jobs: dict[pathlib.Path, "PageRenderJob"]

    def __str__(self) -> str:
        return f"PageRenderJob(source_path={repr(self.source_path)},markdown={repr(self.markdown)},stat={repr(self.stat)})"

    def validate_front_matter(self):
        front_matter = self.markdown.front_matter
        if (
            front_matter
            and front_matter.documentation_of
            and self.source_path != pathlib.Path(front_matter.documentation_of)
        ):
            raise ValueError(
                "PageRenderJob.path must equal front_matter.documentation_of."
            )

    def to_render_link(self) -> RenderLink:
        return RenderLink(
            path=self.source_path,
            title=self.get_title(),
            icon=self.stat.verification_status,
        )

    def get_title(self):
        front_matter = self.front_matter
        if front_matter.title:
            return front_matter.title

        input_file = self.input.files.get(self.source_path)
        if input_file and input_file.title:
            return input_file.title
        return None

    @cached_property
    def front_matter(self) -> FrontMatter:
        if self.markdown.front_matter:
            front_matter = self.markdown.front_matter.model_copy()
        else:
            front_matter = FrontMatter()
        front_matter.documentation_of = self.source_path.as_posix()
        if not front_matter.layout:
            front_matter.layout = "document"
        return front_matter

    @property
    def destination_name(self):
        return self.source_path.with_suffix(self.source_path.suffix + ".md")

    def write_to(self, fp: BinaryIO):
        self.validate_front_matter()
        front_matter = self.front_matter
        front_matter.data = self.get_page_data()
        if not front_matter.title:
            front_matter.title = self.get_title()
        Markdown(
            path=self.source_path,
            front_matter=front_matter,
            content=self.markdown.content,
        ).dump_merged(fp)

    def get_page_data(self) -> PageRenderData:
        def get_link(path: pathlib.Path) -> Optional[RenderLink]:
            job = self.page_jobs.get(path)
            if not job:
                return None
            if (
                job.front_matter.display == DocumentOutputMode.hidden
                or job.front_matter.display == DocumentOutputMode.never
            ):
                return None
            return job.to_render_link()

        depends_on = [
            link
            for link in map(get_link, sorted(self.stat.depends_on, key=str))
            if link
        ]
        required_by = [
            link
            for link in map(get_link, sorted(self.stat.required_by, key=str))
            if link
        ]
        verified_with = [
            link
            for link in map(get_link, sorted(self.stat.verified_with, key=str))
            if link
        ]

        attributes = self.stat.file_input.document_attributes.copy()
        problem = next(
            (
                v.problem
                for v in self.stat.file_input.verification_list
                if isinstance(v, ProblemVerification)
            ),
            None,
        )
        if problem:
            attributes.setdefault("PROBLEM", problem)

        code = read_text_normalized(self.source_path)

        embedded = [EmbeddedCode(name="default", code=code)]
        for s in self.stat.file_input.additonal_sources:
            embedded.append(
                EmbeddedCode(name=s.name, code=read_text_normalized(s.path))
            )

        return PageRenderData(
            path=self.source_path,
            embedded=embedded,
            timestamp=self.stat.timestamp,
            attributes=attributes,
            testcases=[
                EnvTestcaseResult(
                    name=c.name,
                    status=c.status,
                    elapsed=c.elapsed,
                    memory=c.memory,
                    environment=v.verification_name,
                )
                for v in self.stat.verification_results
                for c in (v.testcases or [])
            ]
            if self.stat.verification_results
            else None,
            verification_status=self.stat.verification_status,
            is_verification_file=self.stat.is_verification,
            path_extension=self.source_path.suffix.lstrip("."),
            is_failed=self.stat.verification_status.is_failed,
            document_path=self.markdown.path,
            dependencies=[
                Dependency(type="Depends on", files=depends_on),
                Dependency(type="Required by", files=required_by),
                Dependency(type="Verified with", files=verified_with),
            ],
            depends_on=[link.path for link in depends_on],
            required_by=[link.path for link in required_by],
            verified_with=[link.path for link in verified_with],
        )


@dataclass
class IndexRenderJob(RenderJob):
    page_jobs: dict[pathlib.Path, "PageRenderJob"]
    index_md: Optional[Markdown] = None

    def __str__(self) -> str:
        @dataclass
        class _IndexRenderJob:
            job_paths: Iterable[pathlib.Path]

        s = repr(
            _IndexRenderJob(
                job_paths=self.page_jobs.keys(),
            )
        )
        index = s.find("_IndexRenderJob")
        return s[index + 1 :]

    @property
    def destination_name(self):
        return pathlib.Path("index.md")

    def write_to(self, fp: BinaryIO):
        Markdown(
            path=self.destination_name,
            front_matter=FrontMatter(
                layout="toppage",
                data=self.get_page_data(),
            ),
            content=self.index_md.content if self.index_md else b"",
        ).dump_merged(fp)

    def get_page_data(self) -> IndexRenderData:
        library_categories: dict[str, list[RenderLink]] = {}
        verification_categories: dict[str, list[RenderLink]] = {}
        for job in self.page_jobs.values():
            if (
                job.front_matter.display
                and job.front_matter.display != DocumentOutputMode.visible
            ):
                continue
            stat = job.stat
            if stat.is_verification:
                categories = verification_categories
            else:
                categories = library_categories

            directory = job.source_path.parent
            category = directory.as_posix()
            if category == ".":
                category = ""
            elif not category.endswith("/"):
                category = f"{category}/"

            if category not in categories:
                categories[category] = []

            categories[category].append(
                RenderLink(
                    path=stat.path,
                    icon=stat.verification_status,
                    title=job.get_title(),
                ),
            )

        def _build_categories_list(
            categories: dict[str, list[RenderLink]]
        ) -> list[CategorizedIndex]:
            return sorted(
                (
                    CategorizedIndex(
                        name=category,
                        pages=sorted(pages, key=lambda p: p.path.as_posix()),
                    )
                    for category, pages in categories.items()
                ),
                key=lambda d: d.name,
            )

        return IndexRenderData(
            top=[
                IndexFiles(
                    type="Library Files",
                    categories=_build_categories_list(library_categories),
                ),
                IndexFiles(
                    type="Verification Files",
                    categories=_build_categories_list(verification_categories),
                ),
            ],
        )
