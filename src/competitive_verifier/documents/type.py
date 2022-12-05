import pathlib
from typing import Any, Optional

from pydantic import BaseModel


class FrontMatter(BaseModel):
    title: Optional[str] = None
    layout: Optional[str] = None
    documentation_of: Optional[str] = None
    data: Optional[dict[str, Any]] = None
    redirect_from: Optional[list[str]] = None
    """for jekyll-redirect-from plugin
    """

    def merge(self, other: "FrontMatter") -> "FrontMatter":
        result = self.copy()
        if not result.title:
            result.title = other.title
        if not result.layout:
            result.layout = other.layout
        if not result.documentation_of:
            result.documentation_of = other.documentation_of
        if not result.redirect_from:
            result.redirect_from = other.redirect_from

        if not result.data:
            result.data = other.data
        elif other.data:
            result.data |= other.data
        return result


class PageRenderJob(BaseModel):
    path: pathlib.Path
    """jekyll markdown path

    relative path from basedir
    """
    document_path: Optional[pathlib.Path]
    """original markdown path

    relative path from basedir
    """

    front_matter: FrontMatter
    content: bytes

    def merge(self, other: "PageRenderJob") -> "PageRenderJob":
        assert self.path == other.path
        result = self.copy()
        if not result.document_path:
            result.document_path = other.document_path
        if not result.content:
            result.content = other.content
        result.front_matter = result.front_matter.merge(other.front_matter)
        return result


class SiteRenderConfig(BaseModel):
    static_dir: pathlib.Path
    index_md: pathlib.Path
    destination_dir: pathlib.Path
    config_yml: dict[str, Any]
