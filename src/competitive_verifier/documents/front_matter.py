import pathlib
from typing import Annotated, BinaryIO, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field

from competitive_verifier.models import DocumentOutputMode, ForcePosixPath

from .render_data import IndexRenderData, MultiCodePageData, PageRenderData

_separator: bytes = b"---"


class FrontMatter(BaseModel):
    model_config = ConfigDict(extra="allow")

    display: DocumentOutputMode | None = None
    title: str | None = None
    layout: str | None = Field(
        default=None,
        examples=["toppage", "document", "multidoc"],
    )
    documentation_of: str | Annotated[list[str], Field(min_length=1)] | None = None
    keep_single: bool | None = None
    data: PageRenderData | MultiCodePageData | IndexRenderData | None = None
    redirect_from: list[str] | None = None
    """For jekyll-redirect-from plugin
    """
    redirect_to: str | None = None
    """For jekyll-redirect-from plugin
    """

    def model_dump_yml(self):
        d = self.model_dump(
            mode="json",
            by_alias=True,
            exclude_none=True,
        )
        return yaml.safe_dump(d, encoding="utf-8", line_break="\n")


class Markdown(BaseModel):
    path: ForcePosixPath | None = None
    front_matter: FrontMatter | None
    content: bytes

    @classmethod
    def make_default(cls, source_path: pathlib.Path):
        return cls(
            front_matter=FrontMatter(documentation_of=source_path.as_posix()),
            content=b"",
        )

    @classmethod
    def load_file(cls, path: pathlib.Path):
        with path.open("rb") as fp:
            return cls.load(fp, path)

    @classmethod
    def load(cls, fp: BinaryIO, path: pathlib.Path | None = None):
        front_matter, content = split_front_matter(fp.read())
        return Markdown(
            path=path,
            front_matter=front_matter,
            content=content,
        )

    def dump_merged(self, fp: BinaryIO):
        merge_front_matter(
            fp,
            front_matter=self.front_matter,
            content=self.content,
        )


def split_front_matter_raw(content: bytes) -> tuple[bytes | None, bytes]:
    lines = content.splitlines()
    if len(lines) == 0 or lines[0].rstrip() != _separator:
        return (None, content)
    for i, line in enumerate(lines):
        if i == 0:
            continue
        if line.rstrip() == _separator:
            break
    else:
        return None, content

    front_matter = b"\n".join(lines[1:i])
    content = b"\n".join(lines[i + 1 :])
    return front_matter, content


def split_front_matter(content: bytes) -> tuple[FrontMatter | None, bytes]:
    fm_bytes, content = split_front_matter_raw(content)
    if fm_bytes is None:
        return None, content
    fy = yaml.safe_load(fm_bytes)
    if fy:
        return FrontMatter.model_validate(fy), content
    else:
        return FrontMatter(), content


def merge_front_matter(
    fp: BinaryIO,
    *,
    front_matter: FrontMatter | None,
    content: bytes,
):
    if front_matter:
        fp.write(_separator)
        fp.write(b"\n")
        fp.write(front_matter.model_dump_yml())
        fp.write(_separator)
        fp.write(b"\n")
    fp.write(content)
