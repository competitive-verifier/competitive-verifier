import shutil
from typing import Any, Optional

import pytest

from ..types import ConfigDirSetter, FilePaths
from .integration_data import IntegrationData


class GoWithoutConfigData(IntegrationData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    def check_envinronment(self) -> bool:
        return bool(shutil.which("go"))

    @classmethod
    def input_name(cls) -> str:
        return "GoData"

    def expected_verify_json(self) -> dict[str, Any]:
        return dict(
            {
                "files": {
                    "helloworld.aoj.go": {
                        "additonal_sources": [],
                        "dependencies": [
                            "helloworld.aoj.go",
                            "helloworld/helloworld.go",
                            "helloworld_test.go",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
                        },
                        "verification": [
                            {
                                "command": {
                                    "command": [
                                        "go",
                                        "run",
                                        f"{self.targets_path}/helloworld.aoj.go",
                                    ],
                                    "env": {"GO111MODULE": "off"},
                                },
                                "name": "go",
                                "problem": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
                                "type": "problem",
                            }
                        ],
                    },
                    "helloworld/helloworld.go": {
                        "additonal_sources": [],
                        "dependencies": [
                            "helloworld.aoj.go",
                            "helloworld/helloworld.go",
                            "helloworld_test.go",
                        ],
                        "document_attributes": {},
                        "verification": [],
                    },
                    "helloworld_test.go": {
                        "additonal_sources": [],
                        "dependencies": [
                            "helloworld.aoj.go",
                            "helloworld/helloworld.go",
                            "helloworld_test.go",
                        ],
                        "document_attributes": {"UNITTEST": "GOTESTRESULT"},
                        "verification": [{"status": "failure", "type": "const"}],
                    },
                },
            }
        )

    def expected_verify_result(self) -> dict[str, Any]:
        return {
            "files": {
                "helloworld.aoj.go": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 1415.0,
                            "heaviest": 172.0,
                            "last_execution_time": "2019-03-17T20:56:36.500000-12:00",
                            "slowest": 141.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 4.0,
                                    "memory": 43.12,
                                    "name": "judge_data",
                                    "status": "AC",
                                }
                            ],
                            "verification_name": "go",
                        }
                    ],
                },
                "helloworld_test.go": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 1938.0,
                            "last_execution_time": "1971-07-29T05:58:46.490000+12:00",
                            "status": "failure",
                        }
                    ],
                },
            },
            "total_seconds": 2547.12,
        }


class GoWithConfigData(GoWithoutConfigData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    @classmethod
    def input_name(cls) -> str:
        return "GoData"

    @property
    def config_path(self) -> Optional[str]:
        return (self.targets_path / "config.toml").as_posix()

    def expected_verify_json(self) -> dict[str, Any]:
        return dict(
            {
                "files": {
                    "helloworld.aoj.go": {
                        "additonal_sources": [],
                        "dependencies": [
                            "helloworld.aoj.go",
                            "helloworld/helloworld.go",
                            "helloworld_test.go",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
                        },
                        "verification": [
                            {
                                "command": f"{self.config_dir_path / 'cache/problems/fbdb181defb159dce09f4dc9338a6728'}/helloworld.aoj.go",
                                "compile": f"env GO111MODULE=off go build -o {self.config_dir_path / 'cache/problems/fbdb181defb159dce09f4dc9338a6728'}/helloworld.aoj.go {self.targets_path}/helloworld.aoj.go",
                                "name": "go",
                                "problem": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
                                "type": "problem",
                            }
                        ],
                    },
                    "helloworld/helloworld.go": {
                        "additonal_sources": [],
                        "dependencies": [
                            "helloworld.aoj.go",
                            "helloworld/helloworld.go",
                            "helloworld_test.go",
                        ],
                        "document_attributes": {},
                        "verification": [],
                    },
                    "helloworld_test.go": {
                        "additonal_sources": [],
                        "dependencies": [
                            "helloworld.aoj.go",
                            "helloworld/helloworld.go",
                            "helloworld_test.go",
                        ],
                        "document_attributes": {"UNITTEST": "GOTESTRESULT"},
                        "verification": [{"status": "failure", "type": "const"}],
                    },
                },
            }
        )
