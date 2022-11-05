import pathlib
from typing import Any

import pytest

from competitive_verifier.models.command import DummyCommand
from competitive_verifier.models.file import VerificationFile

parse_VerificationFile_params: list[
    tuple[VerificationFile, dict[str, Any], dict[str, Any]]
] = [
    (
        VerificationFile(),
        {},
        {
            "dependencies": [],
            "display_path": None,
            "verification": [],
        },
    ),
    (
        VerificationFile(
            dependencies=[
                pathlib.Path("bar1"),
                pathlib.Path("bar2"),
            ],
        ),
        {
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
            "verification": [],
        },
    ),
    (
        VerificationFile(
            display_path=pathlib.Path("bar"),
        ),
        {
            "display_path": "bar",
        },
        {
            "dependencies": [],
            "display_path": pathlib.Path("bar"),
            "verification": [],
        },
    ),
    (
        VerificationFile(
            verification=[DummyCommand()],
        ),
        {
            "verification": [{"type": "dummy"}],
        },
        {
            "dependencies": [],
            "display_path": None,
            "verification": [DummyCommand()],
        },
    ),
    (
        VerificationFile(
            verification=[DummyCommand()],
        ),
        {
            "verification": {"type": "dummy"},
        },
        {
            "dependencies": [],
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
