import pytest

from competitive_verifier.documents.front_matter import (
    merge_front_matter,
    split_front_matter,
)
from competitive_verifier.documents.type import FrontMatter

test_split_FrontMatter_params: list[tuple[bytes, FrontMatter, bytes]] = [
    (
        b"""---
title: A + B
documentation_of: //examples/awk/aplusb2.awk
---
# aplusb2

String $A + B$""",
        FrontMatter(documentation_of="//examples/awk/aplusb2.awk", title="A + B"),
        b"""# aplusb2

String $A + B$""",
    ),
]


@pytest.mark.parametrize(
    "content, front_matter, markdown_content",
    test_split_FrontMatter_params,
)
def test_split_FrontMatter(
    content: bytes,
    front_matter: FrontMatter,
    markdown_content: bytes,
):
    front_matter, actual_content = split_front_matter(content)
    assert front_matter == front_matter
    assert actual_content == markdown_content


test_merge_FrontMatter_params: list[tuple[FrontMatter, bytes, bytes]] = [
    (
        FrontMatter(documentation_of="//examples/awk/aplusb2.awk", title="A + B"),
        b"""# aplusb2

String $A + B$""",
        b"""---
documentation_of: //examples/awk/aplusb2.awk
title: A + B
---
# aplusb2

String $A + B$""",
    ),
]


@pytest.mark.parametrize(
    "front_matter, markdown_content, expected",
    test_merge_FrontMatter_params,
)
def test_merge_FrontMatter(
    front_matter: FrontMatter,
    markdown_content: bytes,
    expected: bytes,
):
    assert merge_front_matter(front_matter, markdown_content) == expected
