import importlib.resources
import pathlib
from itertools import chain
from logging import getLogger
from typing import Any, Iterable

from competitive_verifier import git, github
from competitive_verifier.models import (
    SourceCodeStat,
    VerificationInput,
    VerificationStatus,
    VerifyCommandResult,
    resolve_dependency,
)

from .front_matter import merge_front_matter
from .ghpage import check_pushed_to_github_head_branch, push_documents_to_gh_pages
from .job import build_index_job, build_markdown_job, build_source_job
from .render import load_render_config, markdown_dir
from .type import PageRenderJob, SiteRenderConfig

logger = getLogger(__name__)


_RESOURCE_PACKAGE = "competitive_verifier_resources"
_DOC_USAGE_PATH = "doc_usage.txt"


class DocumentBuilder:
    input: VerificationInput
    result: VerifyCommandResult

    def __init__(self, input: VerificationInput, result: VerifyCommandResult) -> None:
        self.input = input
        self.result = result

    def build(self) -> bool:
        logger.info("Generate documents...")
        result = self.impl()
        logger.info("Generated.")

        if github.env.is_in_github_actions():
            workspace = github.env.get_workspace_path()
            assert workspace is not None
            if pathlib.Path.cwd().resolve() != workspace.resolve():
                logger.warning(
                    "Working directory should be git root. " "Working directory: %s",
                    pathlib.Path.cwd().as_posix(),
                )
                result = False
            elif check_pushed_to_github_head_branch():
                # Push gh-pages when in GitHub head branch
                if not push_documents_to_gh_pages(srcdir=markdown_dir):
                    result = False
        else:
            logger.info(
                importlib.resources.read_text(
                    _RESOURCE_PACKAGE, _DOC_USAGE_PATH
                ).replace("{{{{{markdown_dir_path}}}}}", markdown_dir.as_posix())
            )

        return result

    def impl(self) -> bool:
        config = load_render_config()
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
        import sys

        sys.exit()
        return True

        logger.info("list static files...")
        static_files = build.load_static_files(site_render_config=config)

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

        markdown_jobs = {
            job.path: job
            for job in map(build_markdown_job, markdown_paths)
            if job is not None
        }
        logger.debug("markdown_jobs=%s", markdown_jobs.values())

        index_job = build_index_job(index_md)
        logger.debug("index_job=%s", index_job)

        return list(
            ({index_job.path: index_job} | source_jobs | markdown_jobs).values()
        )


def _build_page_title_dict(
    *, render_jobs: list[PageRenderJob]
) -> dict[pathlib.Path, str]:
    page_title_dict: dict[pathlib.Path, str] = {}
    for job in render_jobs:
        assert job.path.suffix == ".md"
        title = job.front_matter.title or job.path.with_suffix("").as_posix()
        page_title_dict[job.path] = title
        page_title_dict[job.path.parent / job.path.stem] = title
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


def _render_source_code_stat(
    stat: SourceCodeStat, *, basedir: pathlib.Path
) -> dict[str, Any]:
    with open(basedir / stat.path, "rb") as fh:
        code = fh.read().decode()
    
    bundled_code = "TODO: bundled https://github.com/competitive-verifier/competitive-verifier/issues/4"
    return {
        "path": str(stat.path),
        "code": code,
        "bundledCode": bundled_code,
        "isVerificationFile": stat.is_verification,
        "verificationStatus": stat.verification_status.value,
        "timestamp": str(stat.timestamp),
        "dependsOn": [str(path) for path in stat.depends_on],
        "requiredBy": [str(path) for path in stat.required_by],
        "verifiedWith": [str(path) for path in stat.verified_with],
        "attributes": stat.attributes,
    }


def _render_source_code_stat_for_page(
    path: pathlib.Path,
    *,
    stats: dict[pathlib.Path, SourceCodeStat],
    page_title_dict: dict[pathlib.Path, str],
) -> dict[str, Any]:
    relative_path = (basedir / path).resolve().relative_to(basedir)
    stat = stats[relative_path]
    data = _render_source_code_stat(stat, basedir=basedir)
    data["_pathExtension"] = path.suffix.lstrip(".")
    data["_verificationStatusIcon"] = stat.verification_status.icon
    data["_isVerificationFailed"] = stat.verification_status.is_failed

    def ext(relative_path: pathlib.Path) -> dict[str, Any]:
        stat = stats[relative_path]
        return {
            "path": str(relative_path),
            "title": page_title_dict[relative_path],
            "icon": _get_verification_status_icon(stat.verification_status),
        }

    data["_extendedDependsOn"] = [
        ext(path) for path in sorted(stat.depends_on, key=str)
    ]
    data["_extendedRequiredBy"] = [
        ext(path) for path in sorted(stat.required_by, key=str)
    ]
    data["_extendedVerifiedWith"] = [
        ext(path) for path in sorted(stat.verified_with, key=str)
    ]

    return data
