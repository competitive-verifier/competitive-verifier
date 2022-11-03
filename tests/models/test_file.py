import pathlib
from typing import Any

import pytest

from competitive_verifier.models.command import DummyCommand
from competitive_verifier.models.file import VerificationFile

parse_VerificationFile_params: list[
    tuple[VerificationFile, dict[str, Any], dict[str, Any]]
] = [
    (
        VerificationFile(
            path=pathlib.Path("foo/bar"),
        ),
        {
            "path": "foo/bar",
        },
        {
            "dependencies": [],
            "display_path": None,
            "path": pathlib.Path("foo/bar"),
            "verification": [],
        },
    ),
    (
        VerificationFile(
            path=pathlib.Path("foo/bar"),
            dependencies=[
                pathlib.Path("bar1"),
                pathlib.Path("bar2"),
            ],
        ),
        {
            "path": "foo/bar",
            "dependencies": [
                "bar1",
                "bar2",
            ],
        },
        {
            "dependencies": [
                pathlib.Path("bar1"),
                pathlib.Path("bar2"),
            ],
            "display_path": None,
            "path": pathlib.Path("foo/bar"),
            "verification": [],
        },
    ),
    (
        VerificationFile(
            path=pathlib.Path("foo/bar"),
            display_path=pathlib.Path("bar"),
        ),
        {
            "path": "foo/bar",
            "display_path": "bar",
        },
        {
            "dependencies": [],
            "path": pathlib.Path("foo/bar"),
            "display_path": pathlib.Path("bar"),
            "verification": [],
        },
    ),
    (
        VerificationFile(
            path=pathlib.Path("foo/bar"),
            verification=[DummyCommand()],
        ),
        {
            "path": "foo/bar",
            "verification": [{"type": "dummy"}],
        },
        {
            "dependencies": [],
            "path": pathlib.Path("foo/bar"),
            "display_path": None,
            "verification": [DummyCommand()],
        },
    ),
    (
        VerificationFile(
            path=pathlib.Path("foo/bar"),
            verification=[DummyCommand()],
        ),
        {
            "path": "foo/bar",
            "verification": {"type": "dummy"},
        },
        {
            "dependencies": [],
            "path": pathlib.Path("foo/bar"),
            "display_path": None,
            "verification": [DummyCommand()],
        },
    ),
]


@pytest.mark.parametrize("obj, raw_dict, output_dict", parse_VerificationFile_params)
def test_parse_VerificationFile(
    obj: VerificationFile,
    raw_dict: dict[str, Any],
    output_dict: dict[str, Any],
):
    assert obj == VerificationFile.parse_obj(raw_dict)
    assert obj.dict() == output_dict
