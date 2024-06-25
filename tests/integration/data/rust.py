import shutil
from typing import Any

import pytest

from ..types import ConfigDirSetter, FilePaths
from .integration_data import IntegrationData


class RustWithoutConfigData(IntegrationData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    def check_envinronment(self) -> bool:
        return bool(shutil.which("rustc"))

    @classmethod
    def input_name(cls) -> str:
        return "RustData"

    def expected_verify_json(self) -> dict[str, Any]:
        return dict(
            {
                "files": {
                    "crates/helloworld/hello/src/lib.rs": {
                        "additonal_sources": [],
                        "dependencies": ["crates/helloworld/hello/src/lib.rs"],
                        "document_attributes": {"links": []},
                        "verification": [],
                    },
                    "crates/helloworld/world/src/lib.rs": {
                        "additonal_sources": [],
                        "dependencies": ["crates/helloworld/world/src/lib.rs"],
                        "document_attributes": {"links": []},
                        "verification": [],
                    },
                    "crates/io/input/src/lib.rs": {
                        "additonal_sources": [],
                        "dependencies": [
                            "crates/io/input/src/lib.rs",
                            "crates/io/scanner/src/lib.rs",
                        ],
                        "document_attributes": {"links": []},
                        "verification": [],
                    },
                    "crates/io/scanner/src/lib.rs": {
                        "additonal_sources": [],
                        "dependencies": ["crates/io/scanner/src/lib.rs"],
                        "document_attributes": {"links": []},
                        "verification": [],
                    },
                    "src/lib.rs": {
                        "additonal_sources": [],
                        "dependencies": [
                            "crates/helloworld/hello/src/lib.rs",
                            "crates/helloworld/world/src/lib.rs",
                            "crates/io/input/src/lib.rs",
                            "crates/io/scanner/src/lib.rs",
                            "src/lib.rs",
                        ],
                        "document_attributes": {"links": []},
                        "verification": [],
                    },
                    "verification/src/bin/aizu-online-judge-itp1-1-a.rs": {
                        "additonal_sources": [],
                        "dependencies": [
                            "crates/helloworld/hello/src/lib.rs",
                            "crates/helloworld/world/src/lib.rs",
                            "crates/io/input/src/lib.rs",
                            "verification/src/bin/aizu-online-judge-itp1-1-a.rs",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A",
                            "links": [
                                "https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A"
                            ],
                        },
                        "verification": [
                            {
                                "command": str(
                                    self.targets_path
                                    / "target/release/aizu-online-judge-itp1-1-a"
                                ),
                                "compile": "cd "
                                f"{self.targets_path / 'verification/src/bin'} "
                                "&& "
                                "cargo "
                                "build "
                                "--release "
                                "--bin "
                                "aizu-online-judge-itp1-1-a",
                                "name": "Rust",
                                "problem": "https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A",
                                "type": "problem",
                            }
                        ],
                    },
                    "verification/src/bin/library-checker-aplusb.rs": {
                        "additonal_sources": [],
                        "dependencies": [
                            "crates/helloworld/hello/src/lib.rs",
                            "crates/helloworld/world/src/lib.rs",
                            "crates/io/input/src/lib.rs",
                            "verification/src/bin/library-checker-aplusb.rs",
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "verification": [
                            {
                                "command": str(
                                    self.targets_path
                                    / "target/release/library-checker-aplusb"
                                ),
                                "compile": "cd "
                                f"{self.targets_path / 'verification/src/bin'} "
                                "&& "
                                "cargo "
                                "build "
                                "--release "
                                "--bin "
                                "library-checker-aplusb",
                                "name": "Rust",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            }
                        ],
                    },
                },
            }
        )

    def expected_verify_result(self) -> dict[str, Any]:
        return {
            "files": {
                "verification/src/bin/aizu-online-judge-itp1-1-a.rs": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 3414.0,
                            "heaviest": 369.0,
                            "last_execution_time": "2046-08-15T20:50:50.570000-05:00",
                            "slowest": 341.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 7.94,
                                    "memory": 5.09,
                                    "name": "judge_data",
                                    "status": "AC",
                                }
                            ],
                            "verification_name": "Rust",
                        }
                    ],
                },
                "verification/src/bin/library-checker-aplusb.rs": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 9167.0,
                            "heaviest": 758.0,
                            "last_execution_time": "2003-08-01T18:18:37.670000+05:00",
                            "slowest": 916.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 4.35,
                                    "memory": 2.83,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.5,
                                    "memory": 35.22,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.53,
                                    "memory": 71.7,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.82,
                                    "memory": 81.21,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.12,
                                    "memory": 66.34,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.58,
                                    "memory": 38.37,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.95,
                                    "memory": 29.66,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.71,
                                    "memory": 59.01,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.2,
                                    "memory": 97.93,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.44,
                                    "memory": 72.71,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.02,
                                    "memory": 78.97,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.52,
                                    "memory": 18.84,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "Rust",
                        }
                    ],
                },
            },
            "total_seconds": 2547.12,
        }
