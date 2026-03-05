import pathlib

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import app
from competitive_verifier.models import VerificationInput, VerifyCommandResult


@pytest.mark.parametrize("write_summary", [True, False])
def test_summary(
    write_summary: bool,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
    testtemp: pathlib.Path,
):
    caplog.set_level(0)

    dummy_return = object()
    mocker.patch(
        "competitive_verifier.documents.builder.DocumentBuilder.build",
        return_value=dummy_return,
    )
    mock_summary_result = mocker.patch(
        "competitive_verifier.arg.WriteSummaryArguments.write_result"
    )

    (verify_files_json := testtemp / "verify.json").write_text(
        VerificationInput().model_dump_json()
    )

    (testtemp / "result.json").write_text(
        VerifyCommandResult(total_seconds=1).model_dump_json()
    )

    assert (
        app.Docs(
            verify_files_json=verify_files_json,
            result_json=[testtemp / "result.json"],
            destination=testtemp / "out",
            write_summary=write_summary,
        ).run()
        is dummy_return
    )

    if write_summary:
        mock_summary_result.assert_called_once()
    else:
        mock_summary_result.assert_not_called()
