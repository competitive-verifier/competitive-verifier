import importlib.resources
import pathlib
from functools import cache
from logging import getLogger
from typing import Any, Iterable, Optional, Union

import yaml

from competitive_verifier import git, github, log
from competitive_verifier.models import (
    ProblemVerification,
    SourceCodeStat,
    VerificationInput,
    VerifyCommandResult,
    resolve_dependency,
)
from competitive_verifier.models.dependency import SourceCodeStatSlim
from competitive_verifier.util import read_text_normalized

from .builder_type import (
    Dependency,
    EmbeddedCode,
    EnvTestcaseResult,
    RenderForPage,
    RenderPage,
    RenderSourceCodeStat,
    RenderTopPage,
    TopPageCategory,
    TopPageFiles,
)
from .front_matter import merge_front_matter
from .job import build_index_job, build_markdown_job, build_source_job
from .render import load_render_config
from .type import PageRenderJob, SiteRenderConfig

logger = getLogger(__name__)


_RESOURCE_PACKAGE = "competitive_verifier_resources"
_DOC_USAGE_PATH = "doc_usage.txt"
_RESOURCE_STATIC_FILE_PATHS: list[str] = [
    "_layouts/page.html",
    "_layouts/document.html",
    "_layouts/toppage.html",
    "_includes/head-custom.html",
    "_includes/head-custom2.html",
    "_includes/mathjax/mathjax.html",
    "_includes/mathjax/mathjax2.html",
    "_includes/mathjax/mathjax3.html",
    "_includes/code.html",
    "_includes/highlight_additional.html",
    "_includes/highlight/highlight_header.html",
    "_includes/document_header.html",
    "_includes/document_body.html",
    "_includes/document_footer.html",
    "_includes/toppage_header.html",
    "_includes/toppage_body.html",
    "assets/css/default.scss",
    "assets/css/code.scss",
    "assets/js/code.js",
    "Gemfile",
]


class ExcludedPaths:
    def __init__(self, excluded_paths: list[Union[str, pathlib.Path]]) -> None:
        self.excluded_paths = [pathlib.Path(p) for p in excluded_paths]

    @cache
    def is_excluded(self, relative_path: pathlib.Path) -> bool:
        for excluded in self.excluded_paths:
            if relative_path == excluded or excluded in relative_path.parents:
                return True
        return False


class DocumentBuilder:
    input: VerificationInput
    result: VerifyCommandResult
    docs_dir: Optional[pathlib.Path]
    destination_dir: pathlib.Path

    def __init__(
        self,
        input: VerificationInput,
        result: VerifyCommandResult,
        docs_dir: Optional[pathlib.Path],
        destination_dir: pathlib.Path,
    ) -> None:
        self.input = input
        self.result = result
        self.docs_dir = docs_dir
        self.destination_dir = destination_dir

    def build(self) -> bool:
        if not _working_directory_is_in_git_root():
            logger.info(
                "Working directory %s is not git root.",
                pathlib.Path.cwd().as_posix(),
            )

        logger.info("Generate documents...")
        result = self.impl()
        logger.info("Generated.")
        logger.info(
            (importlib.resources.files(_RESOURCE_PACKAGE) / _DOC_USAGE_PATH)
            .read_text(encoding="utf-8")
            .replace("{{{{{markdown_dir_path}}}}}", self.destination_dir.as_posix())
            .replace(
                "{{{{{repository}}}}}",
                github.env.get_repository()
                or "competitive-verifier/competitive-verifier",
            )
        )

        return result

    def impl(self) -> bool:
        config, rendered_pages = self.render_pages()

        # make install
        logger.info("writing %s files...", len(rendered_pages))
        for path, content in rendered_pages.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug("writing to %s", path.as_posix())
            path.write_bytes(content)

        logger.info("list static files...")
        static_files = load_static_files(config=config)

        logger.info("writing %s static files...", len(static_files))
        for path, content in static_files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            logger.debug("writing to %s", path.as_posix())
            path.write_bytes(content)
        return True

    def render_pages(self) -> tuple[SiteRenderConfig, dict[pathlib.Path, bytes]]:
        config = load_render_config(
            docs_dir=self.docs_dir,
            destination_dir=self.destination_dir,
        )
        logger.debug("lender config=%s", config)

        excluded_paths = ExcludedPaths(config.config_yml.get("exclude", []))
        included_files = set(
            f for f in git.ls_files() if not excluded_paths.is_excluded(f)
        )
        logger.debug(
            "included_files=%s",
            " ".join(p.as_posix() for p in included_files),
        )

        render_jobs = self.enumerate_rendering_jobs(config.index_md, included_files)

        logger.info("render %s files...", len(render_jobs))
        with log.group("Resolve dependency"):
            stats = resolve_dependency(
                input=self.input,
                result=self.result,
                included_files=included_files,
            )
        return config, self._render_pages_impl(
            stats=stats,
            render_jobs=render_jobs,
            site_render_config=config,
            excluded_paths=excluded_paths,
        )

    def _render_pages_impl(
        self,
        *,
        stats: dict[pathlib.Path, SourceCodeStat],
        render_jobs: list[PageRenderJob],
        site_render_config: SiteRenderConfig,
        excluded_paths: ExcludedPaths,
    ) -> dict[pathlib.Path, bytes]:
        """
        :returns: mapping from absolute paths to file contents
        """

        page_title_dict = _build_page_title_dict(render_jobs=render_jobs)

        rendered_pages: dict[pathlib.Path, bytes] = {}
        for job in render_jobs:
            documentation_of = job.front_matter.documentation_of

            front_matter = job.front_matter.model_copy(deep=True)
            if front_matter.layout == "toppage":
                front_matter.data = render_source_code_stats_for_top_page(
                    stats_iter=stats.values(),
                    page_title_dict=page_title_dict,
                )

            elif documentation_of is not None:
                documentation_of_path = pathlib.Path(documentation_of)
                if not documentation_of_path.exists():
                    logger.warning(
                        "Skip %s because %s doesn't exist.",
                        job.path,
                        documentation_of,
                    )
                    continue
                if excluded_paths.is_excluded(documentation_of_path):
                    logger.info(
                        "Skip %s because %s is excluded.",
                        job.path,
                        documentation_of,
                    )
                    continue
                if not front_matter.layout:
                    front_matter.layout = "document"
                if not front_matter.data:
                    front_matter.data = render_source_code_stat_for_page(
                        job,
                        documentation_of_path,
                        stats[documentation_of_path],
                        links={
                            p: RenderPage(
                                path=p,
                                title=page_title_dict.get(p),
                                icon=s.verification_status,
                            )
                            for p, s in stats.items()
                        },
                    )

            path = site_render_config.destination_dir / job.path
            content = merge_front_matter(front_matter, job.content)
            rendered_pages[path] = content

        return rendered_pages

    def enumerate_rendering_jobs(
        self,
        index_md: pathlib.Path,
        included_files: set[pathlib.Path],
    ) -> list[PageRenderJob]:
        markdown_paths = set(
            p
            for p in git.ls_files()
            if p.suffix == ".md" and not p.name.startswith(".")
        )
        markdown_paths &= included_files
        logger.debug(
            "markdown_paths=%s",
            " ".join(p.as_posix() for p in markdown_paths),
        )

        logger.info("list rendering jobs...")

        source_jobs = {
            job.path: job
            for job in (build_source_job(p, f) for p, f in self.input.files.items())
            if job is not None
        }
        logger.debug("source_jobs=%s", source_jobs.values())

        source_paths = set(self.input.files.keys())
        markdown_jobs = {
            job.path: job
            for job in map(
                lambda p: build_markdown_job(p, source_paths=source_paths),
                markdown_paths,
            )
            if job is not None
        }
        logger.debug("markdown_jobs=%s", markdown_jobs.values())

        index_job = build_index_job(index_md)
        logger.debug("index_job=%s", index_job)

        result: dict[pathlib.Path, PageRenderJob] = {index_job.path: index_job}
        for path, job in source_jobs.items():
            prev = result.get(path)
            if prev:
                result[path] = job.merge(prev)
            else:
                result[path] = job
        for path, job in markdown_jobs.items():
            prev = result.get(path)
            if prev:
                result[path] = job.merge(prev)
            else:
                result[path] = job
        return list(result.values())


def _working_directory_is_in_git_root() -> bool:
    working_directory = pathlib.Path.cwd()
    if github.env.is_in_github_actions():
        workspace = github.env.get_workspace_path()
        assert workspace is not None
        return working_directory.resolve() == workspace.resolve()
    else:
        return working_directory.resolve() == git.get_root_directory().resolve()


def _build_page_title_dict(
    *, render_jobs: list[PageRenderJob]
) -> dict[pathlib.Path, str]:
    page_title_dict: dict[pathlib.Path, str] = {}
    for job in render_jobs:
        assert job.path.suffix == ".md"
        path = job.path.with_suffix("")
        title = job.front_matter.title
        if title and path.as_posix() != title:
            page_title_dict[path] = title
    return page_title_dict


def render_source_code_stats_for_top_page(
    *,
    stats_iter: Iterable[SourceCodeStatSlim],
    page_title_dict: dict[pathlib.Path, str],
) -> dict[str, Any]:
    library_categories: dict[str, list[RenderPage]] = {}
    verification_categories: dict[str, list[RenderPage]] = {}
    for stat in stats_iter:
        if stat.is_verification:
            categories = verification_categories
        else:
            categories = library_categories
        category = stat.path.parent.as_posix()
        if category not in categories:
            categories[category] = []

        categories[category].append(
            RenderPage(
                path=stat.path,
                icon=stat.verification_status,
                title=page_title_dict.get(stat.path),
            ),
        )

    def _build_categories_list(
        categories: dict[str, list[RenderPage]]
    ) -> list[TopPageCategory]:
        return sorted(
            (
                TopPageCategory(
                    name=category, pages=sorted(pages, key=lambda p: p.path.as_posix())
                )
                for category, pages in categories.items()
            ),
            key=lambda d: d.name,
        )

    return RenderTopPage(
        top=[
            TopPageFiles(
                type="Library Files",
                categories=_build_categories_list(library_categories),
            ),
            TopPageFiles(
                type="Verification Files",
                categories=_build_categories_list(verification_categories),
            ),
        ],
    ).model_dump(mode="json", by_alias=True, exclude_none=True)


def _render_source_code_stat(stat: SourceCodeStat) -> RenderSourceCodeStat:
    code = read_text_normalized(stat.path)

    attributes = stat.file_input.document_attributes.copy()
    problem = next(
        (
            v.problem
            for v in stat.file_input.verification
            if isinstance(v, ProblemVerification)
        ),
        None,
    )
    if problem:
        attributes.setdefault("PROBLEM", problem)

    embedded = [EmbeddedCode(name="default", code=code)]
    for s in stat.file_input.additonal_sources:
        embedded.append(EmbeddedCode(name=s.name, code=read_text_normalized(s.path)))

    return RenderSourceCodeStat(
        path=stat.path,
        embedded=embedded,
        is_verification_file=stat.is_verification,
        verification_status=stat.verification_status,
        timestamp=stat.timestamp,
        depends_on=[path for path in stat.depends_on],
        required_by=[path for path in stat.required_by],
        verified_with=[path for path in stat.verified_with],
        attributes=attributes,
        testcases=[
            EnvTestcaseResult(
                name=c.name,
                status=c.status,
                elapsed=c.elapsed,
                memory=c.memory,
                environment=v.verification_name,
            )
            for v in stat.verification_results
            for c in (v.testcases or [])
        ]
        if stat.verification_results
        else None,
    )


def render_source_code_stat_for_page(
    job: PageRenderJob,
    path: pathlib.Path,
    stat: SourceCodeStat,
    *,
    links: dict[pathlib.Path, RenderPage],
) -> dict[str, Any]:
    data = _render_source_code_stat(stat)

    def extend_dependencies(type: str, paths: Iterable[pathlib.Path]) -> Dependency:
        return Dependency(
            type=type,
            files=[links[path] for path in sorted(paths, key=str)],
        )

    return RenderForPage(
        path_extension=path.suffix.lstrip("."),
        is_failed=stat.verification_status.is_failed,
        dependencies=[
            extend_dependencies("Depends on", stat.depends_on),
            extend_dependencies("Required by", stat.required_by),
            extend_dependencies("Verified with", stat.verified_with),
        ],
        document_path=job.document_path,
        **data.model_dump(),
    ).model_dump(mode="json", by_alias=True, exclude_none=True)


def load_static_files(*, config: SiteRenderConfig) -> dict[pathlib.Path, bytes]:
    files: dict[pathlib.Path, bytes] = {}

    # write merged config.yml
    files[config.destination_dir / "_config.yml"] = yaml.safe_dump(
        config.config_yml
    ).encode()

    # load files in resource/*
    for path in _RESOURCE_STATIC_FILE_PATHS:
        files[config.destination_dir / path] = (
            importlib.resources.files(_RESOURCE_PACKAGE) / "jekyll" / path
        ).read_bytes()

    # overwrite with docs/static
    for src in config.static_dir.glob("**/*"):
        if src.is_file():
            dst = config.destination_dir / src.relative_to(config.static_dir)
            files[dst] = src.read_bytes()
    return files
