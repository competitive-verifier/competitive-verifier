import json
import pathlib
from typing import Any

import pytest

from competitive_verifier.verify import main

from .data.integration_data import IntegrationData
from .types import ConfigDirSetter, FilePaths


class CompileFailureData(IntegrationData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    @classmethod
    def input_name(cls) -> str:
        return "CompileFailure"

    def expected_verify_result(self) -> dict[str, Any]:
        return dict(
            {
                "total_seconds": 1312.56,
                "files": {
                    "verify.json": {
                        "newest": True,
                        "verifications": [
                            {
                                "verification_name": "Compile Failure",
                                "elapsed": 8351.0,
                                "last_execution_time": "1995-04-15T15:40:58.150000+03:00",
                                "status": "failure",
                            },
                            {
                                "verification_name": "Command Failure",
                                "elapsed": 1010.0,
                                "heaviest": 40.0,
                                "last_execution_time": "1989-12-16T21:45:15.390000+02:00",
                                "slowest": 101.0,
                                "status": "failure",
                                "testcases": [
                                    {
                                        "elapsed": 5.59,
                                        "memory": 33.3,
                                        "name": "example_00",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 8.91,
                                        "memory": 23.16,
                                        "name": "example_01",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 5.67,
                                        "memory": 10.76,
                                        "name": "random_00",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 3.37,
                                        "memory": 92.99,
                                        "name": "random_01",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 0.81,
                                        "memory": 69.34,
                                        "name": "random_02",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 8.9,
                                        "memory": 99.46,
                                        "name": "random_03",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 9.87,
                                        "memory": 22.2,
                                        "name": "random_04",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 6.55,
                                        "memory": 53.74,
                                        "name": "random_05",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 9.07,
                                        "memory": 51.0,
                                        "name": "random_06",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 2.73,
                                        "memory": 40.89,
                                        "name": "random_07",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 4.05,
                                        "memory": 54.04,
                                        "name": "random_08",
                                        "status": "RE",
                                    },
                                    {
                                        "elapsed": 1.0,
                                        "memory": 62.53,
                                        "name": "random_09",
                                        "status": "RE",
                                    },
                                ],
                            },
                        ],
                    }
                },
            }
        )


@pytest.fixture
def compile_failure_integration_data(
    monkeypatch: pytest.MonkeyPatch,
    file_paths: FilePaths,
    set_config_dir: ConfigDirSetter,
) -> IntegrationData:
    return CompileFailureData(monkeypatch, set_config_dir, file_paths)


@pytest.mark.integration
@pytest.mark.order(-500)
@pytest.mark.usefixtures("additional_path")
@pytest.mark.usefixtures("mock_verification")
def test_compile_failure(
    compile_failure_integration_data: IntegrationData,
):
    verify = compile_failure_integration_data.targets_path / "verify.json"
    result = compile_failure_integration_data.config_dir_path / "result.json"
    main.main(["--verify-json", str(verify), "--output", str(result)])

    assert (
        json.loads(pathlib.Path(result).read_bytes())
        == compile_failure_integration_data.expected_verify_result()
    )
