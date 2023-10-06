import pathlib
from typing import Optional

import pytest

from competitive_verifier.documents.job import build_markdown_job
from competitive_verifier.documents.type import FrontMatter, PageRenderJob

txt_paths = set(pathlib.Path("tests/documents/data").glob("**/*.txt"))

test_build_markdown_job_params: list[
    tuple[pathlib.Path, set[pathlib.Path], Optional[PageRenderJob]]
] = [
    (
        pathlib.Path("tests/documents/data/A.md"),
        txt_paths,
        PageRenderJob(
            path=pathlib.Path("tests/documents/data/A.txt.md"),
            document_path=pathlib.Path("tests/documents/data/A.md"),
            content=b"# A",
            front_matter=FrontMatter(
                title="Test of A",
                documentation_of="tests/documents/data/A.txt",
            ),
        ),
    ),
    (
        pathlib.Path("tests/documents/data/B.md"),
        txt_paths,
        PageRenderJob(
            path=pathlib.Path("tests/documents/data/B.txt.md"),
            document_path=pathlib.Path("tests/documents/data/B.md"),
            content=b"# B",
            front_matter=FrontMatter(
                title="Test of B",
                documentation_of="tests/documents/data/B.txt",
            ),
        ),
    ),
    (
        pathlib.Path("tests/documents/data/C.md"),
        txt_paths,
        PageRenderJob(
            path=pathlib.Path("tests/documents/data/C.txt.md"),
            document_path=pathlib.Path("tests/documents/data/C.md"),
            content=b"# C",
            front_matter=FrontMatter(
                title="Test of C",
                documentation_of="tests/documents/data/C.txt",
            ),
        ),
    ),
    (
        pathlib.Path("tests/documents/data/sub/D.md"),
        txt_paths,
        PageRenderJob(
            path=pathlib.Path("tests/documents/data/D.txt.md"),
            document_path=pathlib.Path("tests/documents/data/sub/D.md"),
            content=b"# D",
            front_matter=FrontMatter(
                title="Test of D",
                documentation_of="tests/documents/data/D.txt",
            ),
        ),
    ),
    (
        pathlib.Path("tests/documents/data/sub/E.md"),
        txt_paths,
        PageRenderJob(
            path=pathlib.Path("tests/documents/data/E.txt.md"),
            document_path=pathlib.Path("tests/documents/data/sub/E.md"),
            content=b"# E",
            front_matter=FrontMatter(
                title="Test of E",
                documentation_of="tests/documents/data/E.txt",
            ),
        ),
    ),
    (
        pathlib.Path("tests/documents/data/F.md"),
        txt_paths,
        PageRenderJob(
            path=pathlib.Path("tests/documents/data/F.txt.md"),
            document_path=pathlib.Path("tests/documents/data/F.md"),
            content=b"# F",
            front_matter=FrontMatter(
                title="Test of F",
                documentation_of="tests/documents/data/F.txt",
            ),
        ),
    ),
]


@pytest.mark.parametrize(
    "path, source_paths, expected",
    test_build_markdown_job_params,
)
def test_build_markdown_job(
    path: pathlib.Path,
    source_paths: set[pathlib.Path],
    expected: Optional[PageRenderJob],
):
    assert build_markdown_job(path, source_paths=source_paths) == expected
