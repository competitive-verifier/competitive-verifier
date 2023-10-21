import pathlib
from logging import getLogger
from typing import Optional

from competitive_verifier.models import VerificationFile

from . import front_matter
from .type import FrontMatter, PageRenderJob

logger = getLogger(__name__)


def get_markdown_paths(*, basedir: pathlib.Path) -> list[pathlib.Path]:
    return [p for p in basedir.glob("**/*.md") if not p.name.startswith(".")]


def resolve_documentation_of(
    documentation_of: str,
    *,
    basepath: pathlib.Path,
    check_exists: bool = True,
) -> Optional[pathlib.Path]:
    if documentation_of.startswith("."):
        # a relative path
        path = basepath.parent / pathlib.Path(documentation_of)
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

    path = basepath.parent / pathlib.Path(documentation_of)
    if path.exists() or not check_exists:
        return path

    return None


def build_markdown_job(
    path: pathlib.Path,
    *,
    source_paths: set[pathlib.Path],
) -> Optional[PageRenderJob]:
    content = path.read_bytes()

    fm, content = front_matter.split_front_matter(content)
    # move the location if documentation_of field exists
    documentation_of = fm.documentation_of
    if documentation_of is None:
        return PageRenderJob(
            path=path,
            document_path=None,
            front_matter=fm,
            content=content,
        )

    documentation_of_path = resolve_documentation_of(documentation_of, basepath=path)
    if documentation_of_path is None:
        logger.warning(
            "the `documentation_of` path of %s is not found: %s",
            path.as_posix(),
            documentation_of,
        )
        return None
    documentation_of_relative_path = documentation_of_path.resolve().relative_to(
        pathlib.Path.cwd()
    )
    if documentation_of_relative_path not in source_paths:
        logger.warning(
            "the `documentation_of` path of %s is not target: %s",
            path.as_posix(),
            documentation_of,
        )
        return None
    fm.documentation_of = documentation_of_relative_path.as_posix()
    mdpath = documentation_of_relative_path.with_suffix(
        documentation_of_relative_path.suffix + ".md"
    )

    return PageRenderJob(
        path=mdpath,
        document_path=path,
        front_matter=fm,
        content=content,
    )


def build_source_job(
    path: pathlib.Path, file: VerificationFile
) -> Optional[PageRenderJob]:
    mdpath = path.with_suffix(path.suffix + ".md")

    # add title specified as a attributes
    title = file.document_attributes.get("TITLE")
    if not title:
        title = file.document_attributes.get("document_title")

    return PageRenderJob(
        path=mdpath,
        title=title,
        document_path=None,
        front_matter=FrontMatter(
            documentation_of=path.as_posix(),
            title=title or path.as_posix(),
        ),
    )


def build_index_job(index_md_path: pathlib.Path) -> PageRenderJob:
    content = b""
    if index_md_path.exists():
        content = index_md_path.read_bytes()
    return PageRenderJob(
        path=pathlib.Path("index.md"),
        document_path=None,
        front_matter=FrontMatter(layout="toppage"),
        content=content,
    )
