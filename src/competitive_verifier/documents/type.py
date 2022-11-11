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


class PageRenderJob(BaseModel):
    path: pathlib.Path
    """a relative path from basedir
    """
    front_matter: FrontMatter
    content: bytes


class SiteRenderConfig(BaseModel):
    static_dir: pathlib.Path
    index_md: pathlib.Path
    destination_dir: pathlib.Path
    config_yml: dict[str, Any]
