import json
import pathlib
import tempfile
from typing import Any

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.models import (
    AddtionalSource,
    CommandVerification,
    ConstVerification,
    DocumentOutputMode,
    FileResult,
    ForcePosixPath,
    ResultStatus,
    Verification,
    VerificationFile,
    VerificationInput,
)


@pytest.mark.parametrize(
    ("attributes", "expected"),
    [
        ({"NOTITLE": "title"}, None),
        ({"TITLE": "TitleValue"}, "TitleValue"),
        ({"document_title": "DocTitle"}, "DocTitle"),
        ({"document_title": "DocTitle", "TITLE": "TitleValue"}, "TitleValue"),
    ],
    ids=repr,
)
def test_title_attribute(attributes: dict[str, Any], expected: str | None):
    assert VerificationFile(document_attributes=attributes).title == expected


@pytest.mark.parametrize(
    ("display", "expected"),
    [
        ("visible", DocumentOutputMode.visible),
        (DocumentOutputMode.visible, DocumentOutputMode.visible),
        ("hidden", DocumentOutputMode.hidden),
        (DocumentOutputMode.hidden, DocumentOutputMode.hidden),
        ("never", DocumentOutputMode.never),
        (DocumentOutputMode.never, DocumentOutputMode.never),
        ("no-index", DocumentOutputMode.no_index),
        ("no_index", DocumentOutputMode.no_index),
        (DocumentOutputMode.no_index, DocumentOutputMode.no_index),
        ("no-match", None),
        (1, None),
    ],
    ids=str,
)
def test_display_attribute(
    display: str | DocumentOutputMode,
    expected: DocumentOutputMode | None,
):
    assert (
        VerificationFile(document_attributes={"DISPLAY": display}).display == expected
    )


@pytest.mark.parametrize(
    ("verification", "expected"),
    [
        (None, []),
        ([], []),
        (
            ConstVerification(status=ResultStatus.FAILURE),
            [ConstVerification(status=ResultStatus.FAILURE)],
        ),
        (
            [
                ConstVerification(status=ResultStatus.FAILURE),
                ConstVerification(status=ResultStatus.SUCCESS),
            ],
            [
                ConstVerification(status=ResultStatus.FAILURE),
                ConstVerification(status=ResultStatus.SUCCESS),
            ],
        ),
    ],
    ids=str,
)
def test_verification_list(
    verification: list[Verification] | Verification | None, expected: list[Verification]
):
    assert VerificationFile(verification=verification).verification_list == expected


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
            dependencies={
                pathlib.Path("bar1"),
                pathlib.Path("bar2"),
            },
        ),
        {
            "dependencies": [
                "bar1",
                "bar2",
            ],
        },
        {
            "dependencies": {
                pathlib.Path("bar1"),
                pathlib.Path("bar2"),
            },
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
    ("obj", "raw_dict", "output_dict"),
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
    ("obj", "is_verification", "is_lightweight_verification"),
    test_is_verification_params,
    ids=range(len(test_is_verification_params)),
)
def test_is_verification(
    obj: VerificationFile,
    is_verification: bool,
    is_lightweight_verification: bool,
):
    assert obj.is_verification() == is_verification
    assert obj.is_lightweight_verification() == is_lightweight_verification


def test_parse_file_relative(mocker: MockerFixture):
    mocker.patch.object(pathlib.Path, "cwd", return_value=pathlib.Path("/foo/rootdir"))
    with tempfile.TemporaryDirectory() as td:
        tmp = pathlib.Path(td) / "verify.json"
        with tmp.open("w") as fp:
            json.dump(
                {
                    "files": {
                        "/foo/rootdir/libfile.py": {
                            "dependencies": [
                                "/foo/rootdir/libfile2.py",
                            ]
                        },
                        "/foo/rootdir/libfile2.py": {"dependencies": []},
                        "/foo/other/libfile.py": {"dependencies": []},
                        "/foo/rootdir/test/test.py": {
                            "dependencies": ["/foo/other/libfile.py", "../libfile.py"]
                        },
                    }
                },
                fp,
            )
        assert (
            VerificationInput.parse_file_relative(tmp).model_dump()
            == VerificationInput(
                files={
                    pathlib.Path("libfile.py"): VerificationFile(
                        dependencies={pathlib.Path("libfile2.py")}
                    ),
                    pathlib.Path("libfile2.py"): VerificationFile(),
                    pathlib.Path("test/test.py"): VerificationFile(),
                }
            ).model_dump()
        )


@pytest.mark.parametrize(
    ("obj", "results", "expected"),
    [
        (
            VerificationInput(
                files={
                    pathlib.Path("both/b1.c"): VerificationFile(),
                    pathlib.Path("both/b2.c"): VerificationFile(),
                    pathlib.Path("input/in1.c"): VerificationFile(),
                    pathlib.Path("input/in2.c"): VerificationFile(),
                }
            ),
            {
                pathlib.Path("both/b1.c"): FileResult(),
                pathlib.Path("both/b2.c"): FileResult(),
                pathlib.Path("result/res1.c"): FileResult(),
                pathlib.Path("result/res2.c"): FileResult(),
            },
            [
                (pathlib.Path("both/b1.c"), FileResult()),
                (pathlib.Path("both/b2.c"), FileResult()),
            ],
        ),
        (
            VerificationInput(
                files={
                    pathlib.Path("input/in1.c"): VerificationFile(),
                    pathlib.Path("input/in2.c"): VerificationFile(),
                }
            ),
            {
                pathlib.Path("result/res1.c"): FileResult(),
                pathlib.Path("result/res2.c"): FileResult(),
            },
            [],
        ),
    ],
)
def test_filterd_files(
    obj: VerificationInput,
    results: dict[ForcePosixPath, FileResult],
    expected: list[tuple[ForcePosixPath, FileResult]],
):
    assert list(obj.filterd_files(results)) == expected


def test_transitive_depends_on():
    obj = VerificationInput(
        files={
            pathlib.Path("fileA.c"): VerificationFile(
                dependencies={pathlib.Path("fileB.c"), pathlib.Path("other.c")}
            ),
            pathlib.Path("fileB.c"): VerificationFile(
                dependencies={pathlib.Path("fileA.c")}
            ),
            pathlib.Path("file1.c"): VerificationFile(),
            pathlib.Path("file2.c"): VerificationFile(
                dependencies={pathlib.Path("file1.c")}
            ),
            pathlib.Path("file3.c"): VerificationFile(
                dependencies={pathlib.Path("file1.c")}
            ),
            pathlib.Path("file4.c"): VerificationFile(
                dependencies={pathlib.Path("file2.c")}
            ),
        }
    )
    assert obj.transitive_depends_on == {
        pathlib.Path("fileA.c"): {pathlib.Path("fileA.c"), pathlib.Path("fileB.c")},
        pathlib.Path("fileB.c"): {pathlib.Path("fileA.c"), pathlib.Path("fileB.c")},
        pathlib.Path("file1.c"): {pathlib.Path("file1.c")},
        pathlib.Path("file2.c"): {pathlib.Path("file1.c"), pathlib.Path("file2.c")},
        pathlib.Path("file3.c"): {pathlib.Path("file1.c"), pathlib.Path("file3.c")},
        pathlib.Path("file4.c"): {
            pathlib.Path("file1.c"),
            pathlib.Path("file2.c"),
            pathlib.Path("file4.c"),
        },
    }
