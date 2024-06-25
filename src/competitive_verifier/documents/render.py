import datetime
import enum
import pathlib
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cached_property
from itertools import chain
from logging import getLogger
from typing import AbstractSet, BinaryIO, Iterable, Optional

from pydantic import BaseModel

import competitive_verifier.git as git
import competitive_verifier.log as log
from competitive_verifier.models import (
    DocumentOutputMode,
    ForcePosixPath,
    ProblemVerification,
    ResultStatus,
    SortedPathSet,
    VerificationFile,
    VerificationInput,
    VerificationResult,
    VerifyCommandResult,
)
from competitive_verifier.util import normalize_bytes_text, read_text_normalized

from .config import ConfigYaml
from .front_matter import FrontMatter, Markdown
from .render_data import (
    CategorizedIndex,
    CodePageData,
    Dependency,
    EmbeddedCode,
    EnvTestcaseResult,
    IndexFiles,
    IndexRenderData,
    MultiCodePageData,
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


def _paths_to_render_links(
    paths: SortedPathSet, page_jobs: dict[pathlib.Path, "PageRenderJob"]
) -> list[RenderLink]:
    def get_link(path: pathlib.Path) -> Optional[RenderLink]:
        job = page_jobs.get(path)
        if not job:
            return None
        return job.to_render_link()

    return [
        link
        for link in map(
            get_link, sorted(paths, key=lambda p: str.casefold(p.as_posix()))
        )
        if link
    ]


class MultiTargetMarkdown(Markdown):
    path: ForcePosixPath  # pyright: ignore
    front_matter: FrontMatter  # pyright: ignore
    multi_documentation_of: list[pathlib.Path]


@dataclass
class UserMarkdowns:
    single: dict[pathlib.Path, Markdown]
    multi: list[MultiTargetMarkdown]

    @staticmethod
    def select_markdown(sources: set[pathlib.Path]) -> "UserMarkdowns":
        single: dict[pathlib.Path, Markdown] = {}
        multi: list[MultiTargetMarkdown] = []
        markdowns = [Markdown.load_file(t) for t in sources if t.suffix == ".md"]
        for md in markdowns:
            if not (md.path and md.front_matter and md.front_matter.documentation_of):
                continue

            if isinstance(md.front_matter.documentation_of, str):
                source_path = resolve_documentation_of(
                    md.front_matter.documentation_of,
                    basedir=md.path.parent,
                )
                if source_path in sources:
                    md.front_matter.documentation_of = source_path.as_posix()
                    single[source_path] = md
                else:
                    logger.warning(
                        "Markdown(%s) documentation_of: %s is not found.",
                        md.path,
                        md.front_matter.documentation_of,
                    )
            else:
                multi_documentation_of: list[pathlib.Path] = []
                for d in md.front_matter.documentation_of:
                    source_path = resolve_documentation_of(
                        d,
                        basedir=md.path.parent,
                    )
                    if source_path in sources:
                        multi_documentation_of.append(source_path)
                    else:
                        logger.warning(
                            "Markdown(%s) documentation_of: %s is not found.",
                            md.path,
                            d,
                        )
                if multi_documentation_of:
                    multi.append(
                        MultiTargetMarkdown(
                            path=md.path,
                            front_matter=md.front_matter,
                            content=md.content,
                            multi_documentation_of=multi_documentation_of,
                        )
                    )
                else:
                    logger.warning(
                        "Markdown(%s) documentation_of have no valid files.",
                        md.path,
                    )

        for m in multi:
            if m.front_matter and m.front_matter.keep_single:
                continue
            for source in m.multi_documentation_of:
                redirect_to = f"/{m.path.with_suffix('').as_posix()}"
                s = single.get(source)
                if s:
                    if s.front_matter:
                        s.front_matter.display = DocumentOutputMode.no_index
                        s.front_matter.redirect_to = redirect_to
                    else:
                        s.front_matter = FrontMatter(
                            redirect_to=redirect_to,
                            display=DocumentOutputMode.no_index,
                        )
                else:
                    s = Markdown(
                        content=b"",
                        front_matter=FrontMatter(
                            redirect_to=redirect_to,
                            display=DocumentOutputMode.no_index,
                        ),
                    )
                single[source] = s
        return UserMarkdowns(
            single=single,
            multi=multi,
        )


class _VerificationStatusFlag(enum.Flag):
    IS_LIBRARY = 0
    NOTHING = 0
    LIBRARY_NOTHING = IS_LIBRARY
    TEST_NOTHING = enum.auto()
    IS_TEST = TEST_NOTHING
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

    TEST_AC_WA_SKIP = IS_TEST | HAVE_AC | HAVE_WA | HAVE_SKIP
    TEST_AC_WA = IS_TEST | HAVE_AC | HAVE_WA
    TEST_AC_SKIP = IS_TEST | HAVE_AC | HAVE_SKIP
    TEST_AC = IS_TEST | HAVE_AC
    TEST_WA_SKIP = IS_TEST | HAVE_WA | HAVE_SKIP
    TEST_WA = IS_TEST | HAVE_WA
    TEST_SKIP = IS_TEST | HAVE_SKIP

    def to_status(self) -> StatusIcon:
        d = {
            self.LIBRARY_AC_WA_SKIP: StatusIcon.LIBRARY_SOME_WA,
            self.LIBRARY_AC_WA: StatusIcon.LIBRARY_SOME_WA,
            self.LIBRARY_AC_SKIP: StatusIcon.LIBRARY_PARTIAL_AC,
            self.LIBRARY_AC: StatusIcon.LIBRARY_ALL_AC,
            self.LIBRARY_WA_SKIP: StatusIcon.LIBRARY_ALL_WA,
            self.LIBRARY_WA: StatusIcon.LIBRARY_ALL_WA,
            self.LIBRARY_SKIP: StatusIcon.LIBRARY_NO_TESTS,
            self.LIBRARY_NOTHING: StatusIcon.LIBRARY_NO_TESTS,
            self.TEST_AC_WA_SKIP: StatusIcon.TEST_WRONG_ANSWER,
            self.TEST_AC_WA: StatusIcon.TEST_WRONG_ANSWER,
            self.TEST_AC_SKIP: StatusIcon.TEST_WAITING_JUDGE,
            self.TEST_AC: StatusIcon.TEST_ACCEPTED,
            self.TEST_WA_SKIP: StatusIcon.TEST_WRONG_ANSWER,
            self.TEST_WA: StatusIcon.TEST_WRONG_ANSWER,
            self.TEST_SKIP: StatusIcon.TEST_WAITING_JUDGE,
            self.TEST_NOTHING: StatusIcon.TEST_WAITING_JUDGE,
        }
        return d[self]

    @classmethod
    def from_status(cls, status: StatusIcon) -> "_VerificationStatusFlag":
        d = {
            StatusIcon.LIBRARY_SOME_WA: cls.LIBRARY_AC_WA,
            StatusIcon.LIBRARY_PARTIAL_AC: cls.LIBRARY_AC_SKIP,
            StatusIcon.LIBRARY_ALL_AC: cls.LIBRARY_AC,
            StatusIcon.LIBRARY_ALL_WA: cls.LIBRARY_WA,
            StatusIcon.LIBRARY_NO_TESTS: cls.LIBRARY_NOTHING,
            StatusIcon.TEST_ACCEPTED: cls.TEST_AC,
            StatusIcon.TEST_WRONG_ANSWER: cls.TEST_WA,
            StatusIcon.TEST_WAITING_JUDGE: cls.TEST_NOTHING,
        }
        return d[status]


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
            p: _VerificationStatusFlag.NOTHING for p in input.files.keys()
        }
        verification_results_dict: dict[pathlib.Path, list[VerificationResult]] = {}

        for p, r in result.files.items():
            if p not in included_files:
                continue
            st = _VerificationStatusFlag.NOTHING
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

            group_status = _VerificationStatusFlag.NOTHING

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

                flag_status = group_status | (
                    _VerificationStatusFlag.IS_TEST
                    if is_verification
                    else _VerificationStatusFlag.IS_LIBRARY
                )

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


class RenderJob(ABC):
    def render(self, dst: pathlib.Path):
        file = dst / self.destination_name
        file.mkdir(parents=True, exist_ok=True)
        with file.open("rb") as fp:
            self.write_to(fp)

    @property
    @abstractmethod
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
        config: ConfigYaml,
        index_md: Optional[Markdown] = None,
    ) -> list["RenderJob"]:
        def plain_content(source: pathlib.Path) -> Optional[RenderJob]:
            if source.suffix == ".md":
                md = Markdown.load_file(source)
                if md.front_matter and md.front_matter.documentation_of:
                    return None
            elif source.suffix == ".html":
                pass
            else:
                return None
            return PlainRenderJob(
                source_path=source,
                content=source.read_bytes(),
            )

        user_markdowns = UserMarkdowns.select_markdown(sources)

        logger.info(" %s source files...", len(sources))

        class SourceForDebug(BaseModel):
            sources: SortedPathSet
            markdowns: UserMarkdowns

        logger.debug(
            "source: %s",
            SourceForDebug(
                sources=sources,
                markdowns=user_markdowns,
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
            markdown = user_markdowns.single.get(source) or Markdown.make_default(
                source
            )
            stat = stats_dict.get(source)
            if not stat:
                plain_job = plain_content(source)
                if plain_job is not None:
                    jobs.append(plain_job)
                elif source.suffix != ".md":
                    logger.info("Skip file: %s", source.as_posix())
                continue
            group_dir = None
            if config.consolidate:
                consolidate = config.consolidate
                group_dir = next(
                    filter(lambda p: p in consolidate, source.parents), None
                )

            pj = PageRenderJob(
                source_path=source,
                group_dir=group_dir or source.parent,
                markdown=markdown,
                stat=stat,
                input=input,
                result=result,
                page_jobs=page_jobs,
            )

            if pj.display == DocumentOutputMode.never:
                continue

            page_jobs[pj.source_path] = pj
            jobs.append(pj)

        multis: list[MultiCodePageRenderJob] = []
        for md in user_markdowns.multi:
            group_dir = None
            if config.consolidate:
                consolidate = config.consolidate
                group_dir = next(
                    filter(lambda p: p in consolidate, md.path.parents), None
                )
            job = MultiCodePageRenderJob(
                markdown=md,
                group_dir=group_dir or md.path.parent,
                page_jobs=page_jobs,
            )

            multis.append(job)

            # if not md.front_matter.keep_single:
            #     for of in md.multi_documentation_of:
            #         pj = page_jobs.get(of)
            #         if pj:
            #             pj.render_link = job.to_render_link()

        jobs.extend(multis)
        jobs.append(
            IndexRenderJob(
                page_jobs=page_jobs,
                multicode_docs=multis,
                index_md=index_md,
            )
        )
        return jobs


@dataclass(frozen=True)
class PlainRenderJob(RenderJob):
    source_path: ForcePosixPath
    content: bytes

    @property
    def destination_name(self):
        return self.source_path

    def write_to(self, fp: BinaryIO):
        fp.write(self.content)


class MarkdownRenderJob(RenderJob):
    source_path: pathlib.Path
    markdown: Markdown

    @property
    def destination_name(self):
        return self.source_path

    def write_to(self, fp: BinaryIO):
        self.markdown.dump_merged(fp)


@dataclass(frozen=True)
class PageRenderJob(RenderJob):
    source_path: pathlib.Path
    group_dir: pathlib.Path
    markdown: Markdown
    stat: SourceCodeStat
    input: VerificationInput
    result: VerifyCommandResult
    page_jobs: dict[pathlib.Path, "PageRenderJob"]

    @property
    def is_verification(self):
        return self.stat.is_verification

    @property
    def display(self):
        return self.front_matter.display or DocumentOutputMode.visible

    def __str__(self) -> str:
        return f"PageRenderJob(source_path={repr(self.source_path)},markdown={repr(self.markdown)},stat={repr(self.stat)})"

    def validate_front_matter(self):
        front_matter = self.markdown.front_matter
        if front_matter and front_matter.documentation_of:
            if not isinstance(
                front_matter.documentation_of, str
            ) or self.source_path != pathlib.Path(front_matter.documentation_of):
                raise ValueError(
                    "PageRenderJob.path must equal front_matter.documentation_of."
                )

    def to_render_link(self, *, index: bool = False) -> Optional[RenderLink]:
        if (
            self.display == DocumentOutputMode.hidden
            or self.display == DocumentOutputMode.never
            or (index and self.display == DocumentOutputMode.no_index)
        ):
            return None
        return RenderLink(
            path=self.source_path,
            filename=self.source_path.relative_to(self.group_dir).as_posix(),
            title=self.front_matter.title,
            icon=self.stat.verification_status,
        )

    @cached_property
    def front_matter(self) -> FrontMatter:
        if self.markdown.front_matter:
            front_matter = self.markdown.front_matter.model_copy()
        else:
            front_matter = FrontMatter()
        front_matter.documentation_of = self.source_path.as_posix()
        if not front_matter.layout:
            front_matter.layout = "document"

        input_file = self.input.files.get(self.source_path)
        if not front_matter.title and (input_file and input_file.title):
            front_matter.title = input_file.title
        if not front_matter.display and (input_file and input_file.display):
            front_matter.display = input_file.display

        return front_matter

    @property
    def destination_name(self):
        return self.source_path.with_suffix(self.source_path.suffix + ".md")

    def write_to(self, fp: BinaryIO):
        self.validate_front_matter()
        front_matter = self.front_matter
        front_matter.data = self.get_page_data()
        Markdown(
            path=self.source_path,
            front_matter=front_matter,
            content=self.markdown.content,
        ).dump_merged(fp)

    def get_page_data(self) -> PageRenderData:
        depends_on = _paths_to_render_links(self.stat.depends_on, self.page_jobs)
        required_by = _paths_to_render_links(self.stat.required_by, self.page_jobs)
        verified_with = _paths_to_render_links(self.stat.verified_with, self.page_jobs)

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
            path_extension=self.source_path.suffix.lstrip("."),
            title=self.front_matter.title,
            embedded=embedded,
            timestamp=self.stat.timestamp,
            attributes=attributes,
            testcases=(
                [
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
                else None
            ),
            verification_status=self.stat.verification_status,
            is_verification_file=self.stat.is_verification,
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


@dataclass(frozen=True)
class MultiCodePageRenderJob(RenderJob):
    markdown: MultiTargetMarkdown
    group_dir: pathlib.Path
    page_jobs: dict[pathlib.Path, "PageRenderJob"]

    def __str__(self) -> str:
        return f"MultiCodePageRenderJob(multi_documentation_of={repr(self.markdown.multi_documentation_of)})"

    @cached_property
    def jobs(self) -> list[PageRenderJob]:
        jobs: list[PageRenderJob] = []
        for m in self.markdown.multi_documentation_of:
            job = self.page_jobs.get(m)
            if not job:
                continue
            jobs.append(job)
        return jobs

    @cached_property
    def verification_status(self) -> StatusIcon:
        flag = _VerificationStatusFlag.NOTHING
        for job in self.jobs:
            flag |= _VerificationStatusFlag.from_status(job.stat.verification_status)
        return flag.to_status()

    @property
    def is_verification(self):
        return self.verification_status.is_test

    @property
    def display(self):
        return self.markdown.front_matter.display or DocumentOutputMode.visible

    @property
    def destination_name(self) -> pathlib.Path:
        return self.markdown.path

    def to_render_link(self, *, index: bool = False) -> RenderLink:
        return RenderLink(
            path=self.markdown.path.with_suffix(""),
            filename=self.markdown.path.relative_to(self.group_dir).as_posix(),
            title=self.markdown.front_matter.title,
            icon=self.verification_status,
        )

    def write_to(self, fp: BinaryIO):
        front_matter = self.markdown.front_matter
        front_matter.layout = "multidoc"
        front_matter.data = self.get_page_data()
        Markdown(
            path=self.markdown.path,
            front_matter=front_matter,
            content=self.markdown.content,
        ).dump_merged(fp)

    def get_page_data(self) -> MultiCodePageData:
        codes = [
            CodePageData.model_validate(
                {"document_content": normalize_bytes_text(j.markdown.content)}
                | j.get_page_data().model_dump(),
            )
            for j in self.jobs
        ]

        multi_documentation_of_set = set(self.markdown.multi_documentation_of)
        multi_documentation_of_set.add(self.markdown.path)
        depends_on_paths = (
            set(chain.from_iterable(j.stat.depends_on for j in self.jobs))
            - multi_documentation_of_set
        )
        required_by_paths = (
            set(chain.from_iterable(j.stat.required_by for j in self.jobs))
            - multi_documentation_of_set
        )
        verified_with_paths = (
            set(chain.from_iterable(j.stat.verified_with for j in self.jobs))
            - multi_documentation_of_set
        )

        depends_on = _paths_to_render_links(depends_on_paths, self.page_jobs)
        required_by = _paths_to_render_links(required_by_paths, self.page_jobs)
        verified_with = _paths_to_render_links(verified_with_paths, self.page_jobs)

        return MultiCodePageData(
            path=self.markdown.path,
            verification_status=self.verification_status,
            is_failed=any(c.is_failed for c in codes),
            codes=codes,
            dependencies=[
                Dependency(type="Depends on", files=depends_on),
                Dependency(type="Required by", files=required_by),
                Dependency(type="Verified with", files=verified_with),
            ],
        )


@dataclass
class IndexRenderJob(RenderJob):
    page_jobs: dict[pathlib.Path, "PageRenderJob"]
    multicode_docs: list[MultiCodePageRenderJob]
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
        for job in chain.from_iterable([self.page_jobs.values(), self.multicode_docs]):
            if job.display != DocumentOutputMode.visible:
                continue
            if job.is_verification:
                categories = verification_categories
            else:
                categories = library_categories

            directory = job.group_dir
            category = directory.as_posix()
            if category == ".":
                category = ""
            elif not category.endswith("/"):
                category = f"{category}/"

            if category not in categories:
                categories[category] = []

            link = job.to_render_link(index=True)
            if link:
                categories[category].append(link)

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
