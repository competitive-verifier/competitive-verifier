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
                    "examples/Aplusb.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplusb.java",
                            "examples/Aplusb_main.java",
                            "examples/Aplusb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {},
                        "verification": [],
                    },
                    "examples/Aplusb_main.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplusb.java",
                            "examples/Aplusb_main.java",
                            "examples/Aplusb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {"STANDALONE": ""},
                        "verification": [
                            {
                                "command": "java " "examples.Aplusb_main",
                                "compile": f"javac {self.targets_path / 'examples/Aplusb_main.java'}",
                                "name": "Java",
                                "tempdir": f"{self.config_dir_path / 'cache/standalone/382841ad26b555d39a8784691c59fce8'}",
                                "type": "command",
                            }
                        ],
                    },
                    "examples/Aplusb_test.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplusb.java",
                            "examples/Aplusb_main.java",
                            "examples/Aplusb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb"
                        },
                        "verification": [
                            {
                                "command": "java examples.Aplusb_test",
                                "compile": f"javac {self.targets_path / 'examples/Aplusb_test.java'}",
                                "name": "Java",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            }
                        ],
                    },
                    "examples/HelloWorld.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplusb.java",
                            "examples/Aplusb_main.java",
                            "examples/Aplusb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {},
                        "verification": [],
                    },
                    "examples/HelloWorld_test.java": {
                        "additonal_sources": [],
                        "dependencies": [
                            "examples/Aplusb.java",
                            "examples/Aplusb_main.java",
                            "examples/Aplusb_test.java",
                            "examples/HelloWorld.java",
                            "examples/HelloWorld_test.java",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
                        },
                        "verification": [
                            {
                                "command": "java examples.HelloWorld_test",
                                "compile": f"javac {self.targets_path / 'examples/HelloWorld_test.java'}",
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
                "examples/Aplusb_main.java": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 5854.0,
                            "last_execution_time": "1973-11-01T17:29:53.180000+06:00",
                            "status": "success",
                            "verification_name": "Java",
                        }
                    ],
                },
                "examples/Aplusb_test.java": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 1440.0,
                            "heaviest": 331.0,
                            "last_execution_time": "2013-11-08T23:55:48.570000-05:00",
                            "slowest": 144.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 5.84,
                                    "memory": 18.62,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.73,
                                    "memory": 11.04,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.11,
                                    "memory": 84.96,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.84,
                                    "memory": 71.78,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.44,
                                    "memory": 56.52,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.1,
                                    "memory": 94.73,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.52,
                                    "memory": 85.38,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.03,
                                    "memory": 95.06,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.13,
                                    "memory": 25.69,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.88,
                                    "memory": 2.09,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.73,
                                    "memory": 79.09,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.31,
                                    "memory": 63.99,
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
            "total_seconds": 3781.68,
        }
