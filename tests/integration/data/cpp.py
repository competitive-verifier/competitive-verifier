import shutil
from typing import Any, Optional

import pytest

from ..types import ConfigDirSetter, FilePaths
from .integration_data import IntegrationData


class CppWithoutConfigData(IntegrationData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    def check_envinronment(self) -> bool:
        return bool(shutil.which("g++") and shutil.which("clang++"))

    @classmethod
    def input_name(cls) -> str:
        return "CppData"

    def expected_verify_json(self) -> dict[str, Any]:
        return dict(
            {
                "files": {
                    "aplusb.hpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": str(
                                    self.config_dir_path / "bundled/aplusb.hpp"
                                ),
                            }
                        ],
                        "dependencies": ["aplusb.hpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "links": [],
                        },
                        "verification": [],
                    },
                    "aplusb.main.cpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": f"{self.config_dir_path / 'bundled/aplusb.main.cpp'}",
                            }
                        ],
                        "dependencies": ["aplusb.hpp", "aplusb.main.cpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "STANDALONE": "",
                            "links": [],
                        },
                        "verification": [
                            {
                                "command": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'}",
                                "compile": "/usr/bin/g++ "
                                "--std=c++17 -O2 "
                                "-Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'} "
                                "aplusb.main.cpp",
                                "name": "g++",
                                "tempdir": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc'}",
                                "type": "command",
                            },
                            {
                                "command": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'}",
                                "compile": "/usr/bin/clang++ "
                                "--std=c++17 -O2 "
                                "-Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'} "
                                "aplusb.main.cpp",
                                "name": "clang++",
                                "tempdir": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc'}",
                                "type": "command",
                            },
                        ],
                    },
                    "aplusb.test.cpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": str(
                                    self.config_dir_path / "bundled/aplusb.test.cpp"
                                ),
                            }
                        ],
                        "dependencies": ["aplusb.hpp", "aplusb.test.cpp", "macros.hpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "verification": [
                            {
                                "command": f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'}",
                                "compile": "/usr/bin/g++ "
                                "--std=c++17 -O2 -Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'} "
                                "aplusb.test.cpp",
                                "name": "g++",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            },
                            {
                                "command": f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'}",
                                "compile": "/usr/bin/clang++ "
                                "--std=c++17 -O2 -Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'} "
                                "aplusb.test.cpp",
                                "name": "clang++",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            },
                        ],
                    },
                    "macros.hpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": str(
                                    self.config_dir_path / "bundled/macros.hpp"
                                ),
                            }
                        ],
                        "dependencies": ["macros.hpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "links": [],
                        },
                        "verification": [],
                    },
                },
            },
        )

    def expected_verify_result(self) -> dict[str, Any]:
        return {
            "files": {
                "aplusb.main.cpp": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 9633.0,
                            "last_execution_time": "2047-05-09T09:21:33.150000+03:00",
                            "status": "success",
                            "verification_name": "g++",
                        },
                        {
                            "elapsed": 2064.0,
                            "last_execution_time": "2004-04-16T13:27:48.340000-03:00",
                            "status": "success",
                            "verification_name": "clang++",
                        },
                    ],
                },
                "aplusb.test.cpp": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 7135.0,
                            "heaviest": 8.0,
                            "last_execution_time": "2039-07-14T04:50:17.220000+10:00",
                            "slowest": 713.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 8.65,
                                    "memory": 44.22,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.7,
                                    "memory": 33.42,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.22,
                                    "memory": 72.01,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.92,
                                    "memory": 37.04,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.54,
                                    "memory": 35.13,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.19,
                                    "memory": 75.36,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.27,
                                    "memory": 99.94,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.22,
                                    "memory": 11.11,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.69,
                                    "memory": 31.8,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.96,
                                    "memory": 2.22,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.35,
                                    "memory": 7.1,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.37,
                                    "memory": 80.29,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "g++",
                        },
                        {
                            "elapsed": 8550.0,
                            "heaviest": 236.0,
                            "last_execution_time": "1974-07-10T15:38:07.610000-01:00",
                            "slowest": 855.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 8.88,
                                    "memory": 32.57,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.86,
                                    "memory": 36.07,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.11,
                                    "memory": 66.14,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.19,
                                    "memory": 47.34,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.42,
                                    "memory": 56.25,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.08,
                                    "memory": 21.26,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.75,
                                    "memory": 66.28,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.05,
                                    "memory": 29.79,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.51,
                                    "memory": 97.67,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.15,
                                    "memory": 20.61,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.07,
                                    "memory": 96.03,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.86,
                                    "memory": 41.06,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "clang++",
                        },
                    ],
                },
            },
            "total_seconds": 2547.12,
        }


class CppWithConfigData(CppWithoutConfigData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    @property
    def config_path(self) -> Optional[str]:
        return (self.targets_path / "config.toml").as_posix()

    def expected_verify_json(self) -> dict[str, Any]:
        return dict(
            {
                "files": {
                    "aplusb.hpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": str(
                                    self.config_dir_path / "bundled/aplusb.hpp"
                                ),
                            }
                        ],
                        "dependencies": ["aplusb.hpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "links": [],
                        },
                        "verification": [],
                    },
                    "aplusb.main.cpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": f"{self.config_dir_path / 'bundled/aplusb.main.cpp'}",
                            }
                        ],
                        "dependencies": ["aplusb.hpp", "aplusb.main.cpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "STANDALONE": "",
                            "links": [],
                        },
                        "verification": [
                            {
                                "command": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'}",
                                "compile": "g++ "
                                "--std=c++17 -Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'} "
                                "aplusb.main.cpp",
                                "name": "g++",
                                "tempdir": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc'}",
                                "type": "command",
                            },
                            {
                                "command": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'}",
                                "compile": "clang++ "
                                "--std=c++17 -Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc/a.out'} "
                                "aplusb.main.cpp",
                                "name": "clang++",
                                "tempdir": f"{self.config_dir_path / 'cache/standalone/4e17a93c916bd2ca29bdf880cce422dc'}",
                                "type": "command",
                            },
                        ],
                    },
                    "aplusb.test.cpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": str(
                                    self.config_dir_path / "bundled/aplusb.test.cpp"
                                ),
                            }
                        ],
                        "dependencies": ["aplusb.hpp", "aplusb.test.cpp", "macros.hpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "verification": [
                            {
                                "command": f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'}",
                                "compile": "g++ "
                                "--std=c++17 -Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'} "
                                "aplusb.test.cpp",
                                "name": "g++",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            },
                            {
                                "command": f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'}",
                                "compile": "clang++ "
                                "--std=c++17 -Wall -g -I "
                                f"{self.targets_path} "
                                "-o "
                                f"{self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6/a.out'} "
                                "aplusb.test.cpp",
                                "name": "clang++",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            },
                        ],
                    },
                    "macros.hpp": {
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": str(
                                    self.config_dir_path / "bundled/macros.hpp"
                                ),
                            }
                        ],
                        "dependencies": ["macros.hpp"],
                        "document_attributes": {
                            "*NOT_SPECIAL_COMMENTS*": "",
                            "links": [],
                        },
                        "verification": [],
                    },
                },
            },
        )
