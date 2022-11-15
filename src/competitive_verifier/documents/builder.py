import importlib.resources
import pathlib
from itertools import chain
from logging import getLogger
from typing import Any, Iterable

import yaml

from competitive_verifier import git, github
from competitive_verifier.models import (
    ProblemVerification,
    SourceCodeStat,
    VerificationInput,
    VerifyCommandResult,
    resolve_dependency,
)

from .front_matter import merge_front_matter
from .job import build_index_job, build_markdown_job, build_source_job
from .render import load_render_config
from .type import PageRenderJob, SiteRenderConfig

logger = getLogger(__name__)


_RESOURCE_PACKAGE = "competitive_verifier_resources"
_DOC_USAGE_PATH = "doc_usage.txt"
_COPIED_STATIC_FILE_PATHS: list[str] = [
    "_layouts/page.html",
    "_layouts/document.html",
    "_layouts/toppage.html",
    "_includes/mathjax.html",
    "_includes/theme_fix.html",
    "_includes/highlight.html",
    "_includes/document_header.html",
    "_includes/document_body.html",
    "_includes/document_footer.html",
    "_includes/toppage_header.html",
    "_includes/toppage_body.html",
    "assets/css/copy-button.css",
    "assets/js/copy-button.js",
    "Gemfile",
]


class DocumentBuilder:
    input: VerificationInput
    result: VerifyCommandResult
    destination_dir: pathlib.Path

    def __init__(
        self,
        input: VerificationInput,
        result: VerifyCommandResult,
        destination_dir: pathlib.Path,
    ) -> None:
        self.input = input
        self.result = result
        self.destination_dir = destination_dir

    def build(self) -> bool:
        if not _working_directory_is_in_git_root():
            logger.warning(
                "Working directory should be git root. " "Working directory: %s",
                pathlib.Path.cwd().as_posix(),
            )
            return False

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
        config = load_render_config(destination_dir=self.destination_dir)
        logger.debug("lender config=%s", config)

        excluded_files = set(
            chain.from_iterable(
                ex.glob("**/*")
                for ex in map(pathlib.Path, config.config_yml.get("exclude", []))
            )
        )
        logger.debug(
            "excluded_files=%s",
            " ".join(p.as_posix() for p in excluded_files),
        )

        render_jobs = self.enumerate_rendering_jobs(config.index_md, excluded_files)

        logger.info("render %s files...", len(render_jobs))
        stats = resolve_dependency(
            input=self.input,
            result=self.result,
            excluded_files=excluded_files,
        )
        rendered_pages = self.render_pages(
            stats=stats,
            render_jobs=render_jobs,
            site_render_config=config,
        )

        logger.info("list static files...")
        static_files = load_static_files(config=config)

        # make install
        logger.info("writing %s files...", len(rendered_pages))
        for path, content in rendered_pages.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(content)

        logger.info("writing %s static files...", len(static_files))
        for path, content in static_files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(content)
        return True

    def render_pages(
        self,
        *,
        stats: dict[pathlib.Path, SourceCodeStat],
        render_jobs: list[PageRenderJob],
        site_render_config: SiteRenderConfig,
    ) -> dict[pathlib.Path, bytes]:
        """
        :returns: mapping from absolute paths to file contents
        """

        page_title_dict = _build_page_title_dict(render_jobs=render_jobs)

        rendered_pages: dict[pathlib.Path, bytes] = {}
        for job in render_jobs:
            documentation_of = job.front_matter.documentation_of

            front_matter = job.front_matter.copy(deep=True)
            if front_matter.layout == "toppage":
                data = _render_source_code_stats_for_top_page(
                    stats_iter=stats.values(),
                    page_title_dict=page_title_dict,
                )
                front_matter.data = data

            elif documentation_of is not None:
                if not front_matter.layout:
                    front_matter.layout = "document"
                data = _render_source_code_stat_for_page(
                    pathlib.Path(documentation_of),
                    stats=stats,
                    page_title_dict=page_title_dict,
                )
                if not front_matter.data:
                    front_matter.data = data

            path = site_render_config.destination_dir / job.path
            content = merge_front_matter(front_matter, job.content)
            rendered_pages[path] = content

        return rendered_pages

    def enumerate_rendering_jobs(
        self,
        index_md: pathlib.Path,
        excluded_files: set[pathlib.Path],
    ) -> list[PageRenderJob]:
        markdown_paths = set(
            p
            for p in git.ls_files()
            if p.suffix == ".md" and not p.name.startswith(".")
        )
        markdown_paths -= excluded_files
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

        return list(
            ({index_job.path: index_job} | source_jobs | markdown_jobs).values()
        )


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
        title = job.front_matter.title or job.path.with_suffix("").as_posix()
        page_title_dict[job.path] = title
        page_title_dict[job.path.with_suffix("")] = title
    return page_title_dict


def _render_source_code_stats_for_top_page(
    *,
    stats_iter: Iterable[SourceCodeStat],
    page_title_dict: dict[pathlib.Path, str],
) -> dict[str, Any]:
    library_categories: dict[str, list[dict[str, str]]] = {}
    verification_categories: dict[str, list[dict[str, str]]] = {}
    for stat in stats_iter:
        if stat.is_verification:
            categories = verification_categories
        else:
            categories = library_categories
        category = stat.path.parent.as_posix()
        if category not in categories:
            categories[category] = []
        categories[category].append(
            {
                "path": stat.path.as_posix(),
                "title": page_title_dict[stat.path],
                "icon": stat.verification_status.icon,
            }
        )

    def _build_categories_list(
        categories: dict[str, list[dict[str, str]]]
    ) -> list[dict[str, Any]]:
        return [
            {
                "name": category,
                "pages": pages,
            }
            for category, pages in categories.items()
        ]

    return {
        "libraryCategories": _build_categories_list(library_categories),
        "verificationCategories": _build_categories_list(verification_categories),
    }


def _render_source_code_stat(stat: SourceCodeStat) -> dict[str, Any]:
    with stat.path.open("rb") as fh:
        code = fh.read().decode()

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

    bundled_code = "TODO: bundled https://github.com/competitive-verifier/competitive-verifier/issues/4"
    return {
        "path": stat.path.as_posix(),
        "code": code,
        "bundledCode": bundled_code,
        "isVerificationFile": stat.is_verification,
        "verificationStatus": stat.verification_status.value,
        "timestamp": str(stat.timestamp),
        "dependsOn": [path.as_posix() for path in stat.depends_on],
        "requiredBy": [path.as_posix() for path in stat.required_by],
        "verifiedWith": [path.as_posix() for path in stat.verified_with],
        "attributes": attributes,
    }


def _render_source_code_stat_for_page(
    path: pathlib.Path,
    *,
    stats: dict[pathlib.Path, SourceCodeStat],
    page_title_dict: dict[pathlib.Path, str],
) -> dict[str, Any]:
    stat = stats[path]
    data = _render_source_code_stat(stat)
    data["_pathExtension"] = path.suffix.lstrip(".")
    data["_verificationStatusIcon"] = stat.verification_status.icon
    data["_isVerificationFailed"] = stat.verification_status.is_failed

    def ext(path: pathlib.Path) -> dict[str, Any]:
        return {
            "path": path.as_posix(),
            "title": page_title_dict[path],
            "icon": stats[path].verification_status.icon,
        }

    def path_list(paths: Iterable[pathlib.Path]) -> list[dict[str, Any]]:
        return [ext(path) for path in sorted(paths, key=str)]

    data["_extendedDependsOn"] = path_list(stat.depends_on)
    data["_extendedRequiredBy"] = path_list(stat.required_by)
    data["_extendedVerifiedWith"] = path_list(stat.verified_with)

    return data


def load_static_files(*, config: SiteRenderConfig) -> dict[pathlib.Path, bytes]:
    files: dict[pathlib.Path, bytes] = {}

    # write merged config.yml
    files[config.destination_dir / "_config.yml"] = yaml.safe_dump(
        config.config_yml
    ).encode()

    # load files in resource/*
    for path in _COPIED_STATIC_FILE_PATHS:
        files[config.destination_dir / path] = (
            importlib.resources.files(_RESOURCE_PACKAGE) / path
        ).read_bytes()

    # overwrite with docs/static
    for src in config.static_dir.glob("**/*"):
        if src.is_file():
            dst = config.destination_dir / src.relative_to(config.static_dir)
            with open(src, "rb") as fh:
                files[dst] = fh.read()
    return files