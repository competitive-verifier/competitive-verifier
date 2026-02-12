import importlib.resources
import pathlib
from typing import cast

_DOC_USAGE_PATH = "doc_usage.txt"


_ROOT = importlib.resources.files(cast("str", __package__))


def doc_usage(
    *,
    markdown_dir_path: pathlib.Path,
    repo_name: str,
) -> str:
    template = _ROOT / _DOC_USAGE_PATH
    return (
        template.read_text(encoding="utf-8")
        .replace("{{{{{markdown_dir_path}}}}}", markdown_dir_path.as_posix())
        .replace("{{{{{repository}}}}}", repo_name)
    )


def jekyll_files() -> dict[str, bytes]:
    return {
        path: (_ROOT / "jekyll" / path).read_bytes()
        for path in [
            "_layouts/page.html",
            "_layouts/document.html",
            "_layouts/multidoc.html",
            "_layouts/toppage.html",
            "_includes/head-custom.html",
            "_includes/head-custom2.html",
            "_includes/mathjax/mathjax.html",
            "_includes/mathjax/mathjax2.html",
            "_includes/mathjax/mathjax3.html",
            "_includes/code.html",
            "_includes/code_and_testcases.html",
            "_includes/highlight_additional.html",
            "_includes/highlight/highlight_header.html",
            "_includes/dependencies.html",
            "_includes/document_header.html",
            "_includes/document_body.html",
            "_includes/document_footer.html",
            "_includes/multidoc_body.html",
            "_includes/multidoc_header.html",
            "_includes/toppage_header.html",
            "_includes/toppage_body.html",
            "assets/css/default.scss",
            "assets/css/code.scss",
            "assets/js/code.js",
            "Gemfile",
        ]
    }
