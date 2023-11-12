import importlib.resources
from typing import Iterable

_RESOURCE_PACKAGE = "competitive_verifier_resources"
_RESOURCE_STATIC_FILE_PATHS: list[str] = [
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


def default_resource_files() -> Iterable[tuple[str, bytes]]:
    for path in _RESOURCE_STATIC_FILE_PATHS:
        yield path, (
            importlib.resources.files(_RESOURCE_PACKAGE) / "jekyll" / path
        ).read_bytes()
