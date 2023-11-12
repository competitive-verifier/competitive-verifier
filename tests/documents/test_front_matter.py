import datetime
import pathlib
import textwrap
from io import BytesIO
from typing import Any, Optional

import pytest
import yaml

from competitive_verifier.documents.front_matter import (
    DocumentOutputMode,
    FrontMatter,
    Markdown,
    merge_front_matter,
    split_front_matter,
)
from competitive_verifier.documents.render_data import (
    CategorizedIndex,
    Dependency,
    EmbeddedCode,
    EnvTestcaseResult,
    IndexFiles,
    IndexRenderData,
    PageRenderData,
    RenderLink,
    StatusIcon,
)
from competitive_verifier.models import JudgeStatus

test_markdown_params: list[tuple[bytes, Optional[dict[str, Any]], bytes]] = [
    (
        b"""---
---""",
        {},
        b"",
    ),
    (
        b"""---
title: A + B
documentation_of: //examples/awk/aplusb2.awk
---""",
        {
            "documentation_of": "//examples/awk/aplusb2.awk",
            "title": "A + B",
        },
        b"",
    ),
    (
        b"""---
---
""",
        {},
        b"",
    ),
    (
        b"""---
title: A + B
documentation_of: //examples/awk/aplusb2.awk
---
""",
        {
            "documentation_of": "//examples/awk/aplusb2.awk",
            "title": "A + B",
        },
        b"",
    ),
    (
        b"""---
---
# aplusb2

String $A + B$""",
        {},
        b"""# aplusb2

String $A + B$""",
    ),
    (
        b"""---
title: A + B
documentation_of: //examples/awk/aplusb2.awk
---
# aplusb2

String $A + B$""",
        {
            "documentation_of": "//examples/awk/aplusb2.awk",
            "title": "A + B",
        },
        b"""# aplusb2

String $A + B$""",
    ),
    (
        b"""---
title: A + B
documentation_of: //examples/awk/aplusb2.awk""",
        None,
        b"""---
title: A + B
documentation_of: //examples/awk/aplusb2.awk""",
    ),
    (
        b"""
title: A + B
documentation_of: //examples/awk/aplusb2.awk""",
        None,
        b"""
title: A + B
documentation_of: //examples/awk/aplusb2.awk""",
    ),
    (
        b"""---
title: A + B
display: no-index
additional-extra-property: "CDE"
---
""",
        {
            "title": "A + B",
            "display": "no-index",
            "additional-extra-property": "CDE",
        },
        b"",
    ),
]


@pytest.mark.parametrize(
    "content, front_matter, markdown_content",
    test_markdown_params,
    ids=range(len(test_markdown_params)),
)
def test_markdown(
    content: bytes,
    front_matter: Optional[dict[str, Any]],
    markdown_content: bytes,
):
    with BytesIO(content) as fp:
        md = Markdown.load(fp)
    expected = Markdown(
        front_matter=front_matter,  # pyright:ignore
        content=markdown_content,
    )
    assert md == expected

    actual_front_matter, actual_content = split_front_matter(content)
    assert actual_content == markdown_content

    if actual_front_matter:
        assert yaml.safe_load(actual_front_matter.model_dump_yml()) == front_matter
    else:
        assert actual_front_matter is None and front_matter is None

    with BytesIO() as fp:
        merge_front_matter(fp, front_matter=actual_front_matter, content=actual_content)
        fp.seek(0)
        merged = fp.read()
        assert merged.endswith(markdown_content)
        if front_matter is not None:
            front = merged[: -len(markdown_content)] if markdown_content else merged
            assert front.startswith(b"---\n")
            assert front.endswith(b"---\n")
            seplen = len(b"---\n")
            assert yaml.safe_load(front[seplen:-seplen]) == front_matter

    with BytesIO() as fp:
        md.dump_merged(fp)
        fp.seek(0)
        assert fp.read() == merged


test_front_matter_dump_yml_params: list[tuple[FrontMatter, bytes]] = [
    (
        FrontMatter(),
        textwrap.dedent(
            """{}
            """
        )
        .lstrip()
        .encode("utf-8"),
    ),
    (
        FrontMatter(
            documentation_of="../foo.txt",
            layout="document",
            redirect_from=["bar.txt"],
            title="Foooo",
            data=IndexRenderData(
                top=[
                    IndexFiles(
                        type="Lib",
                        categories=[
                            CategorizedIndex(
                                name="/a/b/1",
                                pages=[
                                    RenderLink(
                                        path=pathlib.Path("/a/b/1/d.txt"),
                                        filename="d.txt",
                                        title="D(text)",
                                        icon=StatusIcon.LIBRARY_ALL_AC,
                                    ),
                                    RenderLink(
                                        path=pathlib.Path("/a/b/1/e.txt"),
                                        filename="e.txt",
                                        icon=StatusIcon.LIBRARY_NO_TESTS,
                                    ),
                                    RenderLink(
                                        path=pathlib.Path("/a/b/1/f.txt"),
                                        filename="f.txt",
                                        icon=StatusIcon.LIBRARY_PARTIAL_AC,
                                    ),
                                ],
                            ),
                            CategorizedIndex(
                                name="/a/b/c",
                                pages=[
                                    RenderLink(
                                        path=pathlib.Path("/a/b/c/d.txt"),
                                        filename="d.txt",
                                        title="D(text)",
                                        icon=StatusIcon.LIBRARY_SOME_WA,
                                    ),
                                    RenderLink(
                                        path=pathlib.Path("/a/b/c/e.txt"),
                                        filename="e.txt",
                                        icon=StatusIcon.LIBRARY_ALL_WA,
                                    ),
                                ],
                            ),
                        ],
                    ),
                    IndexFiles(
                        type="Verification",
                        categories=[
                            CategorizedIndex(
                                name="/z/b/1",
                                pages=[
                                    RenderLink(
                                        path=pathlib.Path("/z/b/1/d.txt"),
                                        filename="d.txt",
                                        title="D(text)",
                                        icon=StatusIcon.TEST_ACCEPTED,
                                    ),
                                    RenderLink(
                                        path=pathlib.Path("/z/b/1/e.txt"),
                                        filename="e.txt",
                                        icon=StatusIcon.TEST_WAITING_JUDGE,
                                    ),
                                    RenderLink(
                                        path=pathlib.Path("/z/b/1/f.txt"),
                                        filename="f.txt",
                                        icon=StatusIcon.TEST_WAITING_JUDGE,
                                    ),
                                ],
                            ),
                            CategorizedIndex(
                                name="/z/b/c",
                                pages=[
                                    RenderLink(
                                        path=pathlib.Path("/z/b/c/d.txt"),
                                        filename="d.txt",
                                        title="D(text)",
                                        icon=StatusIcon.TEST_WRONG_ANSWER,
                                    ),
                                    RenderLink(
                                        path=pathlib.Path("/z/b/c/e.txt"),
                                        filename="e.txt",
                                        icon=StatusIcon.TEST_WAITING_JUDGE,
                                    ),
                                ],
                            ),
                        ],
                    ),
                ]
            ),
        ),
        textwrap.dedent(
            """
            data:
              top:
              - categories:
                - name: /a/b/1
                  pages:
                  - filename: d.txt
                    icon: LIBRARY_ALL_AC
                    path: /a/b/1/d.txt
                    title: D(text)
                  - filename: e.txt
                    icon: LIBRARY_NO_TESTS
                    path: /a/b/1/e.txt
                  - filename: f.txt
                    icon: LIBRARY_PARTIAL_AC
                    path: /a/b/1/f.txt
                - name: /a/b/c
                  pages:
                  - filename: d.txt
                    icon: LIBRARY_SOME_WA
                    path: /a/b/c/d.txt
                    title: D(text)
                  - filename: e.txt
                    icon: LIBRARY_ALL_WA
                    path: /a/b/c/e.txt
                type: Lib
              - categories:
                - name: /z/b/1
                  pages:
                  - filename: d.txt
                    icon: TEST_ACCEPTED
                    path: /z/b/1/d.txt
                    title: D(text)
                  - filename: e.txt
                    icon: TEST_WAITING_JUDGE
                    path: /z/b/1/e.txt
                  - filename: f.txt
                    icon: TEST_WAITING_JUDGE
                    path: /z/b/1/f.txt
                - name: /z/b/c
                  pages:
                  - filename: d.txt
                    icon: TEST_WRONG_ANSWER
                    path: /z/b/c/d.txt
                    title: D(text)
                  - filename: e.txt
                    icon: TEST_WAITING_JUDGE
                    path: /z/b/c/e.txt
                type: Verification
            documentation_of: ../foo.txt
            layout: document
            redirect_from:
            - bar.txt
            title: Foooo
            """
        )
        .lstrip()
        .encode("utf-8"),
    ),
    (
        FrontMatter(
            documentation_of="../foo.txt",
            layout="document",
            redirect_from=["bar.txt"],
            title="Foooo",
            data=PageRenderData(
                title=None,
                path=pathlib.Path("root/foo.txt"),
                path_extension="txt",
                document_path=pathlib.Path("root/docs/foo.md"),
                embedded=[
                    EmbeddedCode(
                        name="default",
                        code="👍",
                    ),
                ],
                timestamp=datetime.datetime(
                    2006,
                    1,
                    2,
                    13,
                    46,
                    57,
                    433,
                    tzinfo=datetime.timezone(datetime.timedelta(hours=9)),
                ),
                attributes={
                    "PROBLEM": "http://example.com",
                },
                testcases=[
                    EnvTestcaseResult(
                        name="test1",
                        status=JudgeStatus.AC,
                        elapsed=1.2,
                        environment="tx",
                        memory=120.2,
                    ),
                ],
                is_failed=False,
                is_verification_file=True,
                verification_status=StatusIcon.TEST_ACCEPTED,
                dependencies=[
                    Dependency(
                        type="depends_on",
                        files=[
                            RenderLink(
                                path=pathlib.Path("dep/a.txt"),
                                filename="a.txt",
                                icon=StatusIcon.LIBRARY_ALL_AC,
                                title="A(txt)",
                            ),
                            RenderLink(
                                path=pathlib.Path("dep/b.txt"),
                                filename="b.txt",
                                icon=StatusIcon.LIBRARY_ALL_AC,
                            ),
                        ],
                    ),
                    Dependency(
                        type="required_by",
                        files=[
                            RenderLink(
                                path=pathlib.Path("req/a.txt"),
                                filename="a.txt",
                                icon=StatusIcon.TEST_ACCEPTED,
                                title="A(txt)",
                            ),
                            RenderLink(
                                path=pathlib.Path("req/b.txt"),
                                filename="b.txt",
                                icon=StatusIcon.TEST_WAITING_JUDGE,
                            ),
                        ],
                    ),
                    Dependency(
                        type="verified_with",
                        files=[
                            RenderLink(
                                path=pathlib.Path("ver/a.txt"),
                                filename="a.txt",
                                icon=StatusIcon.TEST_ACCEPTED,
                                title="A(txt)",
                            ),
                            RenderLink(
                                path=pathlib.Path("ver/b.txt"),
                                filename="b.txt",
                                icon=StatusIcon.TEST_WAITING_JUDGE,
                            ),
                        ],
                    ),
                ],
                depends_on=[
                    pathlib.Path("dep/a.txt"),
                    pathlib.Path("dep/b.txt"),
                ],
                required_by=[
                    pathlib.Path("req/a.txt"),
                    pathlib.Path("req/b.txt"),
                ],
                verified_with=[
                    pathlib.Path("ver/a.txt"),
                    pathlib.Path("ver/b.txt"),
                ],
            ),
        ),
        textwrap.dedent(
            """
            data:
              attributes:
                PROBLEM: http://example.com
              dependencies:
              - files:
                - filename: a.txt
                  icon: LIBRARY_ALL_AC
                  path: dep/a.txt
                  title: A(txt)
                - filename: b.txt
                  icon: LIBRARY_ALL_AC
                  path: dep/b.txt
                type: depends_on
              - files:
                - filename: a.txt
                  icon: TEST_ACCEPTED
                  path: req/a.txt
                  title: A(txt)
                - filename: b.txt
                  icon: TEST_WAITING_JUDGE
                  path: req/b.txt
                type: required_by
              - files:
                - filename: a.txt
                  icon: TEST_ACCEPTED
                  path: ver/a.txt
                  title: A(txt)
                - filename: b.txt
                  icon: TEST_WAITING_JUDGE
                  path: ver/b.txt
                type: verified_with
              dependsOn:
              - dep/a.txt
              - dep/b.txt
              documentPath: root/docs/foo.md
              embedded:
              - code: "\\U0001F44D"
                name: default
              isFailed: false
              isVerificationFile: true
              path: root/foo.txt
              pathExtension: txt
              requiredBy:
              - req/a.txt
              - req/b.txt
              testcases:
              - elapsed: 1.2
                environment: tx
                memory: 120.2
                name: test1
                status: AC
              timestamp: '2006-01-02 13:46:57.000433+09:00'
              verificationStatus: TEST_ACCEPTED
              verifiedWith:
              - ver/a.txt
              - ver/b.txt
            documentation_of: ../foo.txt
            layout: document
            redirect_from:
            - bar.txt
            title: Foooo
            """
        )
        .lstrip()
        .encode("utf-8"),
    ),
    (
        FrontMatter(display=DocumentOutputMode.visible),
        textwrap.dedent(
            """display: visible
            """
        )
        .lstrip()
        .encode("utf-8"),
    ),
    (
        FrontMatter(display=DocumentOutputMode.hidden),
        textwrap.dedent(
            """display: hidden
            """
        )
        .lstrip()
        .encode("utf-8"),
    ),
    (
        FrontMatter(display=DocumentOutputMode.no_index),
        textwrap.dedent(
            """display: no-index
            """
        )
        .lstrip()
        .encode("utf-8"),
    ),
    (
        FrontMatter(display=DocumentOutputMode.never),
        textwrap.dedent(
            """display: never
            """
        )
        .lstrip()
        .encode("utf-8"),
    ),
]


@pytest.mark.parametrize(
    "front_matter, expected",
    test_front_matter_dump_yml_params,
    ids=range(len(test_front_matter_dump_yml_params)),
)
def test_front_matter_dump_yml(front_matter: FrontMatter, expected: bytes):
    assert front_matter.model_dump_yml() == expected
