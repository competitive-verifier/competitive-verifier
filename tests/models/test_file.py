import pathlib
from typing import Any

import pytest

from competitive_verifier.models import (
    AddtionalSource,
    CommandVerification,
    ConstVerification,
    ResultStatus,
    VerificationFile,
)

test_parse_VerificationFile_params: list[
    tuple[VerificationFile, dict[str, Any], dict[str, Any]]
] = [
    (
        VerificationFile(),
        {},
        {
            "dependencies": set(),
            "document_attributes": {},
            "verification": [],
            "additonal_sources": [],
        },
    ),
    (
        VerificationFile(
            dependencies=set(
                [
                    pathlib.Path("bar1"),
                    pathlib.Path("bar2"),
                ]
            ),
        ),
        {
            "dependencies": [
                "bar1",
                "bar2",
            ],
        },
        {
            "dependencies": set(
                [
                    pathlib.Path("bar1"),
                    pathlib.Path("bar2"),
                ]
            ),
            "document_attributes": {},
            "verification": [],
            "additonal_sources": [],
        },
    ),
    (
        VerificationFile(
            document_attributes={
                "title": "Bar bar",
            },
        ),
        {
            "document_attributes": {
                "title": "Bar bar",
            },
        },
        {
            "dependencies": set(),
            "document_attributes": {
                "title": "Bar bar",
            },
            "verification": [],
            "additonal_sources": [],
        },
    ),
    (
        VerificationFile(
            verification=[ConstVerification(status=ResultStatus.SUCCESS)],
        ),
        {
            "verification": [
                {
                    "type": "const",
                    "status": "success",
                }
            ],
        },
        {
            "dependencies": set(),
            "document_attributes": {},
            "verification": [
                {
                    "type": "const",
                    "status": "success",
                }
            ],
            "additonal_sources": [],
        },
    ),
    (
        VerificationFile(
            verification=[ConstVerification(status=ResultStatus.SUCCESS)],
        ),
        {
            "verification": [
                {
                    "type": "const",
                    "status": "success",
                }
            ],
        },
        {
            "dependencies": set(),
            "document_attributes": {},
            "verification": [
                {
                    "type": "const",
                    "status": "success",
                }
            ],
            "additonal_sources": [],
        },
    ),
    (
        VerificationFile(
            additonal_sources=[
                AddtionalSource(name="dummy", path=pathlib.Path("tmp/dummy.sh"))
            ]
        ),
        {
            "additonal_sources": [{"name": "dummy", "path": "tmp/dummy.sh"}],
        },
        {
            "dependencies": set(),
            "document_attributes": {},
            "verification": [],
            "additonal_sources": [
                {"name": "dummy", "path": pathlib.Path("tmp/dummy.sh")}
            ],
        },
    ),
]


@pytest.mark.parametrize(
    "obj, raw_dict, output_dict",
    test_parse_VerificationFile_params,
    ids=range(len(test_parse_VerificationFile_params)),
)
def test_parse_VerificationFile(
    obj: VerificationFile,
    raw_dict: dict[str, Any],
    output_dict: dict[str, Any],
):
    assert obj == VerificationFile.model_validate(raw_dict)
    assert obj.model_dump(exclude_none=True) == output_dict


test_is_verification_params = [
    (
        VerificationFile(
            verification=[ConstVerification(status=ResultStatus.SUCCESS)],
        ),
        True,
        True,
    ),
    (
        VerificationFile(
            verification=[
                ConstVerification(status=ResultStatus.SUCCESS),
                ConstVerification(status=ResultStatus.FAILURE),
            ],
        ),
        True,
        True,
    ),
    (
        VerificationFile(
            verification=[CommandVerification(command="true")],
        ),
        True,
        False,
    ),
    (
        VerificationFile(
            verification=[
                ConstVerification(status=ResultStatus.SUCCESS),
                CommandVerification(command="true"),
            ],
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
    "obj, is_verification, is_skippable_verification",
    test_is_verification_params,
    ids=range(len(test_is_verification_params)),
)
def test_is_verification(
    obj: VerificationFile,
    is_verification: bool,
    is_skippable_verification: bool,
):
    assert obj.is_verification() == is_verification
    assert obj.is_skippable_verification() == is_skippable_verification
