import pathlib

import pytest

from competitive_verifier.documents.type import FrontMatter, PageRenderJob

test_merge_FrontMatter_params: list[tuple[FrontMatter, FrontMatter, FrontMatter]] = [
    (
        FrontMatter(),
        FrontMatter(),
        FrontMatter(),
    ),
    (
        FrontMatter(
            data={"foo": 1},
            documentation_of="prog",
            layout="tt",
            redirect_from=["bar"],
            title="NAME",
        ),
        FrontMatter(),
        FrontMatter(
            data={"foo": 1},
            documentation_of="prog",
            layout="tt",
            redirect_from=["bar"],
            title="NAME",
        ),
    ),
    (
        FrontMatter(
            data={"foo": 1},
            documentation_of="prog",
            layout="tt",
            redirect_from=["bar"],
            title="NAME",
        ),
        FrontMatter(
            data={"bar": 2},
            documentation_of="other",
            layout="aa",
            redirect_from=["fizz"],
            title="MAIN",
        ),
        FrontMatter(
            data={"foo": 1, "bar": 2},
            documentation_of="prog",
            layout="tt",
            redirect_from=["bar"],
            title="NAME",
        ),
    ),
]


@pytest.mark.parametrize(
    "obj, other, merged",
    test_merge_FrontMatter_params,
)
def test_merge_FrontMatter(
    obj: FrontMatter,
    other: FrontMatter,
    merged: FrontMatter,
):
    assert obj.merge(other) == merged


test_merge_PageRenderJob_params: list[
    tuple[PageRenderJob, PageRenderJob, PageRenderJob]
] = [
    (
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"",
            document_path=None,
            front_matter=FrontMatter(title="MAIN"),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"",
            document_path=None,
            front_matter=FrontMatter(
                title="Name",
                documentation_of="prog",
            ),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"",
            document_path=None,
            front_matter=FrontMatter(
                title="MAIN",
                documentation_of="prog",
            ),
        ),
    ),
    (
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"foo",
            document_path=pathlib.Path("/foo/bar.md"),
            front_matter=FrontMatter(title="MAIN"),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"",
            document_path=None,
            front_matter=FrontMatter(
                title="Name",
                documentation_of="prog",
            ),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"foo",
            document_path=pathlib.Path("/foo/bar.md"),
            front_matter=FrontMatter(
                title="MAIN",
                documentation_of="prog",
            ),
        ),
    ),
    (
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"",
            document_path=None,
            front_matter=FrontMatter(
                title="Name",
                documentation_of="prog",
            ),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"fizz",
            document_path=pathlib.Path("/foo/buzz.md"),
            front_matter=FrontMatter(title="MAIN"),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"fizz",
            document_path=pathlib.Path("/foo/buzz.md"),
            front_matter=FrontMatter(
                title="Name",
                documentation_of="prog",
            ),
        ),
    ),
    (
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"foo",
            document_path=pathlib.Path("/foo/bar.md"),
            front_matter=FrontMatter(title="MAIN"),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"",
            document_path=None,
            front_matter=FrontMatter(
                title="Name",
                documentation_of="prog",
            ),
        ),
        PageRenderJob(
            path=pathlib.Path("/foo/bar"),
            content=b"foo",
            document_path=pathlib.Path("/foo/bar.md"),
            front_matter=FrontMatter(
                title="MAIN",
                documentation_of="prog",
            ),
        ),
    ),
]


@pytest.mark.parametrize(
    "obj, other, merged",
    test_merge_PageRenderJob_params,
)
def test_merge_PageRenderJob(
    obj: PageRenderJob,
    other: PageRenderJob,
    merged: PageRenderJob,
):
    assert obj.merge(other) == merged
