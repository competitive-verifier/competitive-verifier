import json
import pathlib
import tempfile
from typing import Any

import pytest
from pydantic import ValidationError

from competitive_verifier.app import MergeInput
from competitive_verifier.models import (
    ConstVerification,
    ResultStatus,
    VerificationFile,
    VerificationInput,
)

test_merge_input_params: list[tuple[dict[str, VerificationInput], dict[str, Any]]] = [
    (
        {
            "file1.json": VerificationInput(
                files={
                    pathlib.Path("file1.txt"): VerificationFile(
                        dependencies={pathlib.Path("file2.txt")},
                        verification=ConstVerification(status=ResultStatus.SUCCESS),
                    ),
                    pathlib.Path("file2.txt"): VerificationFile(
                        document_attributes={"TITLE": "file2", "JSON": "file1"},
                    ),
                }
            ),
        },
        {
            "files": {
                "file1.txt": {
                    "dependencies": ["file2.txt"],
                    "verification": {"type": "const", "status": "success"},
                    "document_attributes": {},
                    "additonal_sources": [],
                },
                "file2.txt": {
                    "dependencies": [],
                    "verification": [],
                    "document_attributes": {"TITLE": "file2", "JSON": "file1"},
                    "additonal_sources": [],
                },
            }
        },
    ),
    (
        {
            "file1.json": VerificationInput(
                files={
                    pathlib.Path("file1.txt"): VerificationFile(
                        dependencies={pathlib.Path("file2.txt")},
                        verification=ConstVerification(status=ResultStatus.SUCCESS),
                    ),
                    pathlib.Path("file2.txt"): VerificationFile(
                        document_attributes={"TITLE": "file2", "JSON": "file1"},
                    ),
                }
            ),
            "file2.json": VerificationInput(
                files={
                    pathlib.Path("{base}/fileA.txt"): VerificationFile(
                        dependencies={pathlib.Path("file2.txt")},
                        verification=ConstVerification(status=ResultStatus.SUCCESS),
                    ),
                    pathlib.Path("{base}/file2.txt"): VerificationFile(
                        document_attributes={"NAME": "FILE2", "JSON": "file2"},
                    ),
                }
            ),
        },
        {
            "files": {
                "file1.txt": {
                    "dependencies": ["file2.txt"],
                    "verification": {"type": "const", "status": "success"},
                    "document_attributes": {},
                    "additonal_sources": [],
                },
                "file2.txt": {
                    "dependencies": [],
                    "verification": [],
                    "document_attributes": {"NAME": "FILE2", "JSON": "file2"},
                    "additonal_sources": [],
                },
                "fileA.txt": {
                    "additonal_sources": [],
                    "dependencies": [
                        "file2.txt",
                    ],
                    "document_attributes": {},
                    "verification": {
                        "status": "success",
                        "type": "const",
                    },
                },
            }
        },
    ),
]


@pytest.mark.parametrize(("files", "expected"), test_merge_input_params)
def test_merge_input(
    files: dict[str, VerificationInput],
    expected: dict[str, Any],
    tempdir: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
):
    monkeypatch.chdir(tempdir)

    file_list: list[pathlib.Path] = []
    for k, v in files.items():
        p = tempdir / k
        file_list.append(p)
        j = v.model_dump_json()
        p.write_text(j.replace(r"{base}", tempdir.as_posix()), encoding="utf-8")

    assert MergeInput(verify_files_json=file_list).run()
    out, err = capsys.readouterr()
    assert err == ""
    assert json.loads(out) == expected


def test_merge_input_error():
    with tempfile.TemporaryDirectory() as tmpdir_s:
        tmpdir = pathlib.Path(tmpdir_s)
        (tmpdir / "ok.json").write_text(
            r"""{
    "files":{}
}"""
        )
        (tmpdir / "ng.json").write_text(
            r"""{
    "files":[]
}"""
        )
        with pytest.raises(
            ValidationError, match=r"validation error for VerificationInput"
        ):
            MergeInput(verify_files_json=[tmpdir / "ok.json", tmpdir / "ng.json"]).run()
