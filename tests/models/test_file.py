import pathlib
from typing import Any

import pytest

from competitive_verifier.models import (
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
            "dependencies": [],
            "document_title": None,
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
            "document_title": None,
            "verification": [],
        },
    ),
    (
        VerificationFile(
            document_title="Bar bar",
        ),
        {
            "document_title": "Bar bar",
        },
        {
            "dependencies": [],
            "document_title": "Bar bar",
            "verification": [],
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
            "dependencies": [],
            "document_title": None,
            "verification": [ConstVerification(status=ResultStatus.SUCCESS)],
        },
    ),
    (
        VerificationFile(
            verification=[ConstVerification(status=ResultStatus.SUCCESS)],
        ),
        {
            "verification": {
                "type": "const",
                "status": "success",
            },
        },
        {
            "dependencies": [],
            "document_title": None,
            "verification": [ConstVerification(status=ResultStatus.SUCCESS)],
        },
    ),
]


@pytest.mark.parametrize(
    "obj, raw_dict, output_dict",
    test_parse_VerificationFile_params,
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
    "obj, is_verification, is_skippable_verification", test_is_verification_params
)
def test_is_verification(
    obj: VerificationFile,
    is_verification: bool,
    is_skippable_verification: bool,
):
    assert obj.is_verification() == is_verification
    assert obj.is_skippable_verification() == is_skippable_verification
