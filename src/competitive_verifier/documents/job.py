import pathlib
from logging import getLogger
from typing import Optional

from competitive_verifier.models import VerificationFile

from . import front_matter
from .type import FrontMatter, PageRenderJob

logger = getLogger(__name__)


def get_markdown_paths(*, basedir: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in basedir.glob("**/*.md") if not p.name.startswith(".")]


def _resolve_documentation_of(
    documentation_of: str, *, markdown_path: pathlib.Path
) -> Optional[pathlib.Path]:
    if documentation_of.startswith("."):
        # a relative path
        path = markdown_path.parent / pathlib.Path(documentation_of)
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

    path = markdown_path.parent / pathlib.Path(documentation_of)
    if path.exists():
        return path

    return None


def build_markdown_job(
    path: pathlib.Path,
    *,
    source_paths: set[pathlib.Path],
) -> Optional[PageRenderJob]:
    with open(path, "rb") as fh:
        content = fh.read()

    fm, content = front_matter.split_front_matter(content)
    # move the location if documentation_of field exists
    documentation_of = fm.documentation_of
    if documentation_of is not None:
        documentation_of_path = _resolve_documentation_of(
            documentation_of, markdown_path=path
        )
        if documentation_of_path is None:
            logger.warning(
                "the `documentation_of` path of %s is not found: %s",
                path.as_posix(),
                documentation_of,
            )
            return None
        if documentation_of_path not in source_paths:
            logger.warning(
                "the `documentation_of` path of %s is not target: %s",
                path.as_posix(),
                documentation_of,
            )
            return None
        documentation_of_relative_path = documentation_of_path.resolve().relative_to(
            pathlib.Path.cwd()
        )
        fm.documentation_of = documentation_of_relative_path.as_posix()
        path = documentation_of_relative_path.with_suffix(
            documentation_of_relative_path.suffix + ".md"
        )

    return PageRenderJob(
        path=path,
        front_matter=fm,
        content=content,
    )


def build_source_job(
    path: pathlib.Path, file: VerificationFile
) -> Optional[PageRenderJob]:
    mdpath = path.with_suffix(path.suffix + ".md")

    # add redirects from old URLs
    old_directory = "/verify" if file.is_verification() else "/library"
    redirect_from = [
        old_directory + path.as_posix(),
        old_directory + path.with_suffix(".html").as_posix(),
    ]

    # add title specified as a attributes like @title
    front_matter = FrontMatter(
        documentation_of=path.as_posix(),
        redirect_from=redirect_from,
        title=file.document_attributes.get("document_title", path.as_posix()),
    )
    # treat @docs path/to.md directives
    content = b""
    # if '_deprecated_at_docs' in stat.attributes:
    #     at_docs_path = pathlib.Path(stat.attributes['_deprecated_at_docs'])
    #     try:
    #         with open(at_docs_path, 'rb') as fh:
    #             content = fh.read()
    #     except FileNotFoundError as e:
    #         logger.exception('failed to read markdown file specified by @docs in %s: %s', str(stat.path), e)

    return PageRenderJob(
        path=mdpath,
        front_matter=front_matter,
        content=content,
    )


def build_index_job(index_md_path: pathlib.Path) -> PageRenderJob:
    content = b""
    if index_md_path.exists():
        with index_md_path.open("rb") as fh:
            content = fh.read()
    return PageRenderJob(
        path=pathlib.Path("index.md"),
        front_matter=FrontMatter(layout="toppage"),
        content=content,
    )
