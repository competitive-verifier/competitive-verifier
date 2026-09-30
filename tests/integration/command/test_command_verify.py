import datetime
import json
import pathlib
import random
import shutil

import pytest

from competitive_verifier import app
from competitive_verifier.models import (
    FileResult,
    JudgeStatus,
    ResultStatus,
    VerificationResult,
)
from competitive_verifier.models import TestcaseResult as _TestcaseResult
from competitive_verifier.verify import verifier

from .data.integration_data import IntegrationData


@pytest.mark.integration
@pytest.mark.usefixtures("additional_path")
@pytest.mark.order(-500)
class TestCommandVerfy:
    @pytest.mark.usefixtures("mock_verification")
    def test_mock_dump(self):
        for _ in range(20):
            command_result = verifier.VerifyCommandResult(
                total_seconds=3,
                files={
                    pathlib.Path("foo/bar.py"): FileResult(
                        verifications=[
                            VerificationResult(
                                verification_name="name1",
                                elapsed=random.randint(10, 242),
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime.datetime.fromtimestamp(
                                    random.randint(1000000000, 3000000000)
                                ),
                            ),
                            VerificationResult(
                                verification_name="name2",
                                elapsed=random.randint(10, 242),
                                status=ResultStatus.SKIPPED,
                                heaviest=random.randint(1000, 3000),
                                slowest=random.randint(234, 1234),
                                last_execution_time=datetime.datetime.fromtimestamp(
                                    random.randint(1000000000, 3000000000)
                                ),
                                testcases=[
                                    _TestcaseResult(
                                        name="case01",
                                        status=JudgeStatus.AC,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                    _TestcaseResult(
                                        name="case02",
                                        status=JudgeStatus.RE,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                    _TestcaseResult(
                                        name="case03",
                                        status=JudgeStatus.WA,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                    _TestcaseResult(
                                        name="case04",
                                        status=JudgeStatus.TLE,
                                        elapsed=random.randint(12, 24),
                                        memory=random.randint(100, 1000),
                                    ),
                                ],
                            ),
                        ]
                    ),
                    pathlib.Path("foo/baz2.py"): FileResult(
                        verifications=[
                            VerificationResult(
                                verification_name="name1",
                                elapsed=random.randint(10, 242),
                                status=ResultStatus.SUCCESS,
                                last_execution_time=datetime.datetime.fromtimestamp(
                                    random.randint(1000000000, 3000000000)
                                ),
                            ),
                        ]
                    ),
                },
            )
            assert json.loads(command_result.model_dump_json(exclude_none=True)) == {
                "total_seconds": 2547.12,
                "files": {
                    "foo/bar.py": {
                        "verifications": [
                            {
                                "verification_name": "name1",
                                "status": "success",
                                "elapsed": 9948.0,
                                "last_execution_time": "2004-10-09T00:26:13.890000+02:00",
                            },
                            {
                                "verification_name": "name2",
                                "status": "skipped",
                                "elapsed": 2238.0,
                                "slowest": 223.0,
                                "heaviest": 753.0,
                                "testcases": [
                                    {
                                        "name": "case01",
                                        "status": "AC",
                                        "elapsed": 1.33,
                                        "memory": 32.38,
                                    },
                                    {
                                        "name": "case02",
                                        "status": "RE",
                                        "elapsed": 4.73,
                                        "memory": 9.88,
                                    },
                                    {
                                        "name": "case03",
                                        "status": "WA",
                                        "elapsed": 2.4,
                                        "memory": 35.43,
                                    },
                                    {
                                        "name": "case04",
                                        "status": "TLE",
                                        "elapsed": 2.42,
                                        "memory": 22.41,
                                    },
                                ],
                                "last_execution_time": "2026-11-12T22:34:03.760000-11:00",
                            },
                        ],
                        "newest": True,
                    },
                    "foo/baz2.py": {
                        "verifications": [
                            {
                                "verification_name": "name1",
                                "status": "success",
                                "elapsed": 1239.0,
                                "last_execution_time": "1975-10-05T09:39:58.780000-09:00",
                            }
                        ],
                        "newest": True,
                    },
                },
            }

    @pytest.mark.usefixtures("mock_verification")
    def test_verify(
        self,
        integration_data: IntegrationData,
    ):
        verify = integration_data.config_dir_path / "verify.json"
        result = integration_data.config_dir_path / "result.json"
        shutil.rmtree(integration_data.config_dir_path / "cache", ignore_errors=True)

        parsed = app.ArgumentParser().parse(
            ["verify", "--verify-json", str(verify), "--output", str(result)]
        )
        assert isinstance(parsed, app.Verify)
        assert parsed.run()

        assert (
            json.loads(pathlib.Path(result).read_bytes())
            == integration_data.expected_verify_result()
        )

    @pytest.mark.usefixtures("mock_verification")
    def test_verify_from_other_cwd(
        self,
        integration_data: IntegrationData,
        monkeypatch: pytest.MonkeyPatch,
    ):
        """`verify` chdirs to `basedir` of verify.json, so it can be run from anywhere."""
        verify = integration_data.config_dir_path / "verify.json"
        other_cwd = integration_data.config_dir_path / "other_cwd"
        other_cwd.mkdir(parents=True, exist_ok=True)
        shutil.rmtree(integration_data.config_dir_path / "cache", ignore_errors=True)

        monkeypatch.chdir(other_cwd)
        parsed = app.ArgumentParser().parse(
            [
                "verify",
                "--verify-json",
                str(verify),
                "--output",
                "result_other_cwd.json",
            ]
        )
        assert isinstance(parsed, app.Verify)
        assert parsed.run()

        assert pathlib.Path.cwd() == integration_data.targets_path
        result = other_cwd / "result_other_cwd.json"
        assert (
            json.loads(result.read_bytes()) == integration_data.expected_verify_result()
        )

    def test_merge_input_from_other_cwd(
        self,
        integration_data: IntegrationData,
        monkeypatch: pytest.MonkeyPatch,
        capfd: pytest.CaptureFixture[str],
    ):
        verify = integration_data.config_dir_path / "verify.json"
        other_cwd = integration_data.config_dir_path / "other_cwd"
        other_cwd.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(verify, other_cwd / "a.json")
        shutil.copyfile(verify, other_cwd / "b.json")

        monkeypatch.chdir(other_cwd)
        parsed = app.ArgumentParser().parse(["merge-input", "a.json", "b.json"])
        assert isinstance(parsed, app.MergeInput)
        assert parsed.run()

        assert pathlib.Path.cwd() == integration_data.targets_path
        merged = json.loads(capfd.readouterr().out)
        assert merged == integration_data.expected_verify_json()

    def test_merge_input_different_basedir(
        self,
        integration_data: IntegrationData,
        monkeypatch: pytest.MonkeyPatch,
    ):
        verify = integration_data.config_dir_path / "verify.json"
        other_cwd = integration_data.config_dir_path / "other_cwd"
        other_cwd.mkdir(parents=True, exist_ok=True)
        conflict = json.loads(verify.read_bytes())
        conflict["basedir"] = other_cwd.as_posix()
        (other_cwd / "conflict.json").write_text(json.dumps(conflict))

        monkeypatch.chdir(other_cwd)
        parsed = app.ArgumentParser().parse(
            ["merge-input", str(verify), "conflict.json"]
        )
        assert isinstance(parsed, app.MergeInput)
        with pytest.raises(ValueError, match="different basedir"):
            parsed.run()
