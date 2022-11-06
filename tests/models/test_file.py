import pathlib
from typing import Any

import pytest

from competitive_verifier.models import (
    DummyCommand,
    VerificationCommand,
    VerificationFile,
)

test_parse_VerificationFile_params: list[
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


@pytest.mark.parametrize(
    "obj, raw_dict, output_dict", test_parse_VerificationFile_params
)
def test_parse_VerificationFile(
    obj: VerificationFile,
    raw_dict: dict[str, Any],
    output_dict: dict[str, Any],
):
    assert obj == VerificationFile.parse_obj(raw_dict)
    assert obj.dict() == output_dict


test_is_verification_params = [
    (
        VerificationFile(
            verification=[DummyCommand()],
        ),
        True,
        True,
    ),
    (
        VerificationFile(
            verification=[DummyCommand(), DummyCommand()],
        ),
        True,
        True,
    ),
    (
        VerificationFile(
            verification=[VerificationCommand(command="true")],
        ),
        True,
        False,
    ),
    (
        VerificationFile(
            verification=[DummyCommand(), VerificationCommand(command="true")],
        ),
        True,
        False,
    ),
    (
        VerificationFile(
            verification=[],
        ),
        False,
        False,
    ),
]


@pytest.mark.parametrize(
    "obj, is_verification, is_dummy_verification", test_is_verification_params
)
def test_is_verification(
    obj: VerificationFile,
    is_verification: bool,
    is_dummy_verification: bool,
):
    assert obj.is_verification() == is_verification
    assert obj.is_dummy_verification() == is_dummy_verification
