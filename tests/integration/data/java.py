import shutil
from typing import Any

import pytest

from ..types import ConfigDirSetter, FilePaths
from .integration_data import IntegrationData


class JavaData(IntegrationData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    def check_envinronment(self) -> bool:
        return bool(shutil.which("javac"))

    def expected_verify_json(self) -> dict[str, Any]:
        return dict(
            {
                "files": {
                    "examples/Aplutb_test.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplutb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb"
                        },
                        "verification": [
                            {
                                "command": "java examples.Aplutb_test",
                                "compile": f"javac {self.targets_path/'examples/Aplutb_test.java'}",
                                "name": "Java",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            }
                        ],
                    },
                    "examples/HelloWorld.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplutb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {},
                        "verification": [],
                    },
                    "examples/HelloWorld_test.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplutb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
                        },
                        "verification": [
                            {
                                "command": "java examples.HelloWorld_test",
                                "compile": f"javac {self.targets_path/'examples/HelloWorld_test.java'}",
                                "name": "Java",
                                "problem": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
                                "type": "problem",
                            }
                        ],
                    },
                },
            },
        )

    def expected_verify_result(self) -> dict[str, Any]:
        return {
            "files": {
                "examples/Aplutb_test.java": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 5673.0,
                            "heaviest": 12.0,
                            "last_execution_time": "2029-07-26T03:21:57.010000-11:00",
                            "slowest": 567.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 6.24,
                                    "memory": 23.23,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.85,
                                    "memory": 85.03,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.51,
                                    "memory": 66.88,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.94,
                                    "memory": 18.9,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.27,
                                    "memory": 9.41,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.34,
                                    "memory": 26.78,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.34,
                                    "memory": 2.03,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.24,
                                    "memory": 36.55,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.52,
                                    "memory": 51.34,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.22,
                                    "memory": 30.05,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.38,
                                    "memory": 35.4,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.03,
                                    "memory": 68.16,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "Java",
                        }
                    ],
                },
                "examples/HelloWorld_test.java": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 8002.0,
                            "heaviest": 302.0,
                            "last_execution_time": "2007-06-15T09:14:19.970000+10:00",
                            "slowest": 800.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 3.73,
                                    "memory": 70.0,
                                    "name": "judge_data",
                                    "status": "AC",
                                }
                            ],
                            "verification_name": "Java",
                        }
                    ],
                },
            },
            "total_seconds": 2547.12,
        }
