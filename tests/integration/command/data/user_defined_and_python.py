import pathlib
from typing import Any

from competitive_verifier.oj.gnu import time_command

from .integration_data import IntegrationData


class UserDefinedAndPythonData(IntegrationData):
    @property
    def bundle_euc_ke_path(self):
        return self.config_dir_path / "bundled/encoding/EUC-KR.txt"

    @property
    def bundle_cp932_path(self):
        return self.config_dir_path / "bundled/encoding/cp932.txt"

    @property
    def config_path(self) -> str | None:
        return (self.targets_path / "config.toml").as_posix()

    @property
    def exclude_path(self) -> list[str] | None:
        return ["dummy/"]

    def assert_oj_resolve(self):
        assert self.bundle_euc_ke_path.read_bytes().strip() == b"cp949"
        assert self.bundle_cp932_path.read_bytes().strip() == b"cp932"

    def expected_verify_json(self) -> dict[str, Any]:
        return {
            "files": {
                "awk/aplusb.awk": {
                    "additonal_sources": [],
                    "dependencies": ["awk/aplusb.awk"],
                    "document_attributes": {"TITLE": 'Calculate "A + B"'},
                    "verification": [],
                },
                "awk/aplusb.test.awk": {
                    "additonal_sources": [],
                    "dependencies": ["awk/aplusb.awk", "awk/aplusb.test.awk"],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb"
                    },
                    "verification": [
                        {
                            "command": {
                                "command": f"awk -f {pathlib.Path('awk/aplusb.test.awk')}",
                                "env": {"AWKPATH": str(self.targets_path)},
                            },
                            "compile": f"ls {self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6'}",
                            "name": "awk",
                            "problem": "https://judge.yosupo.jp/problem/aplusb",
                            "type": "problem",
                        }
                    ],
                },
                "awk/aplusb_direct.awk": {
                    "additonal_sources": [],
                    "dependencies": ["awk/aplusb_direct.awk"],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb"
                    },
                    "verification": [
                        {
                            "command": {
                                "command": f"awk -f {pathlib.Path('awk/aplusb_direct.awk')}",
                                "env": {"AWKPATH": str(self.targets_path)},
                            },
                            "compile": f"ls {self.config_dir_path / 'cache/problems/8e3916c7805235eb07ec2a58660d89c6'}",
                            "name": "awk",
                            "problem": "https://judge.yosupo.jp/problem/aplusb",
                            "type": "problem",
                        }
                    ],
                },
                "awk/myaplusb1.test.awk": {
                    "additonal_sources": [],
                    "dependencies": [
                        "awk/aplusb.awk",
                        "awk/myaplusb1.test.awk",
                    ],
                    "document_attributes": {
                        "LOCALCASE": "./myaplusb",
                    },
                    "verification": [
                        {
                            "command": {
                                "command": "awk -f awk/myaplusb1.test.awk",
                                "env": {
                                    "AWKPATH": str(self.targets_path),
                                },
                            },
                            "compile": f"ls {self.config_dir_path / 'cache/localcase/fe34e9ca8a1b0c7dc6064caa76df4ceb'}",
                            "tempdir": f"{self.config_dir_path / 'cache/localcase/fe34e9ca8a1b0c7dc6064caa76df4ceb'}",
                            "input": "awk/myaplusb",
                            "name": "awk",
                            "type": "local",
                        },
                    ],
                },
                "awk/myaplusb2.test.awk": {
                    "additonal_sources": [],
                    "dependencies": [
                        "awk/aplusb.awk",
                        "awk/myaplusb2.test.awk",
                    ],
                    "document_attributes": {
                        "LOCALCASE": "awk/myaplusb",
                    },
                    "verification": [
                        {
                            "command": {
                                "command": "awk -f awk/myaplusb2.test.awk",
                                "env": {
                                    "AWKPATH": str(self.targets_path),
                                },
                            },
                            "compile": f"ls {self.config_dir_path / 'cache/localcase/1ddebc75fd9eacc1b706e14eca475e9b'}",
                            "tempdir": f"{self.config_dir_path / 'cache/localcase/1ddebc75fd9eacc1b706e14eca475e9b'}",
                            "input": "awk/myaplusb",
                            "name": "awk",
                            "type": "local",
                        },
                    ],
                },
                "awk/myaplusb3.test.awk": {
                    "additonal_sources": [],
                    "dependencies": [
                        "awk/aplusb.awk",
                        "awk/myaplusb3.test.awk",
                    ],
                    "document_attributes": {
                        "LOCALCASE": "//awk/",
                    },
                    "verification": [
                        {
                            "command": {
                                "command": "awk -f awk/myaplusb3.test.awk",
                                "env": {
                                    "AWKPATH": str(self.targets_path),
                                },
                            },
                            "compile": f"ls {self.config_dir_path / 'cache/localcase/1ae5fd5805b72f60d16a9c648d4fe262'}",
                            "tempdir": f"{self.config_dir_path / 'cache/localcase/1ae5fd5805b72f60d16a9c648d4fe262'}",
                            "input": "awk",
                            "name": "awk",
                            "type": "local",
                        },
                    ],
                },
                "encoding/EUC-KR.txt": {
                    "dependencies": ["encoding/cp932.txt", "encoding/EUC-KR.txt"],
                    "verification": [],
                    "document_attributes": {},
                    "additonal_sources": [
                        {
                            "name": "bundled",
                            "path": self.bundle_euc_ke_path.as_posix(),
                        }
                    ],
                },
                "encoding/cp932.txt": {
                    "dependencies": ["encoding/cp932.txt", "encoding/EUC-KR.txt"],
                    "verification": [],
                    "document_attributes": {},
                    "additonal_sources": [
                        {
                            "name": "bundled",
                            "path": self.bundle_cp932_path.as_posix(),
                        }
                    ],
                },
                "python/lib_all_failure.py": {
                    "dependencies": ["python/lib_all_failure.py"],
                    "verification": [],
                    "document_attributes": {"links": []},
                    "additonal_sources": [],
                },
                "python/lib_some_failure.py": {
                    "dependencies": ["python/lib_some_failure.py"],
                    "verification": [],
                    "document_attributes": {"TITLE": "Units📏", "links": []},
                    "additonal_sources": [],
                },
                "python/lib_hidden.py": {
                    "additonal_sources": [],
                    "dependencies": ["python/lib_hidden.py"],
                    "document_attributes": {"DISPLAY": "hidden", "links": []},
                    "verification": [],
                },
                "python/lib_skip.py": {
                    "dependencies": ["python/lib_skip.py"],
                    "verification": [],
                    "document_attributes": {"links": []},
                    "additonal_sources": [],
                },
                "python/lib_some_skip_some_wa.py": {
                    "dependencies": ["python/lib_some_skip_some_wa.py"],
                    "verification": [],
                    "document_attributes": {"links": []},
                    "additonal_sources": [],
                },
                "python/success1.py": {
                    "dependencies": [
                        "python/lib_some_failure.py",
                        "python/lib_some_skip.py",
                        "python/success1.py",
                    ],
                    "verification": [
                        {
                            "name": "Python",
                            "type": "problem",
                            "command": f"env PYTHONPATH={self.targets_path.as_posix()} python python/success1.py",
                            "problem": "https://judge.yosupo.jp/problem/aplusb",
                        }
                    ],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                        "links": ["https://judge.yosupo.jp/problem/aplusb"],
                    },
                    "additonal_sources": [],
                },
                "python/failure.wa.py": {
                    "dependencies": [
                        "python/failure.wa.py",
                        "python/lib_all_failure.py",
                        "python/lib_some_skip_some_wa.py",
                    ],
                    "verification": [
                        {
                            "name": "Python",
                            "type": "problem",
                            "command": f"env PYTHONPATH={self.targets_path.as_posix()} python python/failure.wa.py",
                            "problem": "https://judge.yosupo.jp/problem/aplusb",
                        }
                    ],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                        "links": ["https://judge.yosupo.jp/problem/aplusb"],
                    },
                    "additonal_sources": [],
                },
                "python/failure.mle.py": {
                    "dependencies": [
                        "python/failure.mle.py",
                        "python/lib_all_failure.py",
                        "python/lib_some_failure.py",
                    ],
                    "verification": [
                        {
                            "name": "Python",
                            "type": "problem",
                            "command": f"env PYTHONPATH={self.targets_path.as_posix()} python python/failure.mle.py",
                            "problem": "https://judge.yosupo.jp/problem/aplusb",
                            "mle": 100.0,
                        }
                    ],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                        "MLE": "100",
                        "links": ["https://judge.yosupo.jp/problem/aplusb"],
                    },
                    "additonal_sources": [],
                },
                "python/skip.py": {
                    "dependencies": [
                        "python/lib_skip.py",
                        "python/lib_some_skip_some_wa.py",
                        "python/skip.py",
                    ],
                    "verification": [{"type": "const", "status": "skipped"}],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                        "IGNORE": "",
                        "links": ["https://judge.yosupo.jp/problem/aplusb"],
                    },
                    "additonal_sources": [],
                },
                "python/success2.py": {
                    "dependencies": [
                        "python/lib_all_success.py",
                        "python/lib_some_skip_some_wa.py",
                        "python/success2.py",
                    ],
                    "verification": [
                        {
                            "name": "Python",
                            "type": "problem",
                            "command": f"env PYTHONPATH={self.targets_path.as_posix()} python python/success2.py",
                            "problem": "https://judge.yosupo.jp/problem/aplusb",
                        }
                    ],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                        "links": ["https://judge.yosupo.jp/problem/aplusb"],
                    },
                    "additonal_sources": [],
                },
                "python/lib_all_success.py": {
                    "dependencies": ["python/lib_all_success.py"],
                    "verification": [],
                    "document_attributes": {"links": []},
                    "additonal_sources": [],
                },
                "python/failure.re.py": {
                    "dependencies": [
                        "python/failure.re.py",
                        "python/lib_all_failure.py",
                    ],
                    "verification": [
                        {
                            "name": "Python",
                            "type": "problem",
                            "command": f"env PYTHONPATH={self.targets_path.as_posix()} python python/failure.re.py",
                            "problem": "https://judge.yosupo.jp/problem/aplusb",
                        }
                    ],
                    "document_attributes": {
                        "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                        "links": ["https://judge.yosupo.jp/problem/aplusb"],
                    },
                    "additonal_sources": [],
                },
                "python/lib_some_skip.py": {
                    "dependencies": ["python/lib_some_skip.py"],
                    "verification": [],
                    "document_attributes": {"links": []},
                    "additonal_sources": [],
                },
                "python/failure.tle.py": {
                    "dependencies": [
                        "python/failure.tle.py",
                        "python/lib_all_failure.py",
                    ],
                    "verification": [
                        {
                            "name": "Python",
                            "type": "problem",
                            "command": f"env PYTHONPATH={self.targets_path.as_posix()} python python/failure.tle.py",
                            "problem": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
                            "tle": 0.1,
                        }
                    ],
                    "document_attributes": {
                        "PROBLEM": "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
                        "TLE": "0.1",
                        "links": [
                            "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
                        ],
                    },
                    "additonal_sources": [],
                },
                "python/sub/no_dependants.py": {
                    "additonal_sources": [],
                    "dependencies": ["python/sub/no_dependants.py"],
                    "document_attributes": {"links": []},
                    "verification": [],
                },
            }
        }

    def expected_verify_result(self) -> dict[str, Any]:
        return {
            "total_seconds": 14892.72,
            "files": {
                "awk/aplusb.test.awk": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 5030.0,
                            "heaviest": 48.0,
                            "last_execution_time": "2016-04-01T06:51:05.550000-07:00",
                            "slowest": 503.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 5.28,
                                    "memory": 84.4,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.32,
                                    "memory": 8.22,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.07,
                                    "memory": 9.44,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.2,
                                    "memory": 92.03,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.74,
                                    "memory": 7.33,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.63,
                                    "memory": 68.03,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.1,
                                    "memory": 22.03,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.08,
                                    "memory": 62.59,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.28,
                                    "memory": 50.1,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.77,
                                    "memory": 78.42,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.28,
                                    "memory": 72.85,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.38,
                                    "memory": 82.09,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "awk",
                        }
                    ],
                },
                "awk/aplusb_direct.awk": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 2481.0,
                            "heaviest": 198.0,
                            "last_execution_time": "2019-09-03T13:45:49.350000-02:00",
                            "slowest": 248.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 3.82,
                                    "memory": 48.12,
                                    "name": "example_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.27,
                                    "memory": 69.16,
                                    "name": "example_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.99,
                                    "memory": 97.03,
                                    "name": "random_00",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.9,
                                    "memory": 25.28,
                                    "name": "random_01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.37,
                                    "memory": 77.2,
                                    "name": "random_02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.71,
                                    "memory": 95.31,
                                    "name": "random_03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.02,
                                    "memory": 3.83,
                                    "name": "random_04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.69,
                                    "memory": 55.61,
                                    "name": "random_05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.75,
                                    "memory": 46.8,
                                    "name": "random_06",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.08,
                                    "memory": 75.38,
                                    "name": "random_07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.96,
                                    "memory": 58.54,
                                    "name": "random_08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.36,
                                    "memory": 98.49,
                                    "name": "random_09",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "awk",
                        }
                    ],
                },
                "awk/myaplusb1.test.awk": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 1353.0,
                            "heaviest": 498.0,
                            "last_execution_time": "2062-01-30T15:09:06.330000-04:00",
                            "slowest": 135.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 3.25,
                                    "memory": 84.05,
                                    "name": "case13",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.63,
                                    "memory": 29.83,
                                    "name": "case11",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.19,
                                    "memory": 1.38,
                                    "name": "case05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.15,
                                    "memory": 10.09,
                                    "name": "case09",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.4,
                                    "memory": 51.95,
                                    "name": "case10",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.61,
                                    "memory": 14.13,
                                    "name": "case07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.17,
                                    "memory": 24.01,
                                    "name": "case02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.16,
                                    "memory": 92.12,
                                    "name": "case04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.74,
                                    "memory": 29.45,
                                    "name": "case16",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 3.15,
                                    "memory": 98.59,
                                    "name": "case08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.35,
                                    "memory": 57.39,
                                    "name": "case12",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 7.09,
                                    "memory": 14.39,
                                    "name": "case01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.29,
                                    "memory": 84.86,
                                    "name": "case03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.78,
                                    "memory": 81.13,
                                    "name": "case14",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.82,
                                    "memory": 57.1,
                                    "name": "case15",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.13,
                                    "memory": 86.9,
                                    "name": "case06",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "awk",
                        },
                    ],
                },
                "awk/myaplusb2.test.awk": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 2888.0,
                            "heaviest": 232.0,
                            "last_execution_time": "2064-08-22T07:27:17.220000+10:00",
                            "slowest": 288.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 4.58,
                                    "memory": 16.24,
                                    "name": "case13",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.87,
                                    "memory": 92.37,
                                    "name": "case11",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.94,
                                    "memory": 53.84,
                                    "name": "case05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.84,
                                    "memory": 9.04,
                                    "name": "case09",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.09,
                                    "memory": 80.76,
                                    "name": "case10",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.39,
                                    "memory": 7.66,
                                    "name": "case07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.68,
                                    "memory": 89.31,
                                    "name": "case02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.89,
                                    "memory": 69.07,
                                    "name": "case04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.67,
                                    "memory": 79.41,
                                    "name": "case16",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.78,
                                    "memory": 33.26,
                                    "name": "case08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.23,
                                    "memory": 56.6,
                                    "name": "case12",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 4.48,
                                    "memory": 50.73,
                                    "name": "case01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.85,
                                    "memory": 17.84,
                                    "name": "case03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.98,
                                    "memory": 15.52,
                                    "name": "case14",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.81,
                                    "memory": 46.17,
                                    "name": "case15",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.31,
                                    "memory": 12.57,
                                    "name": "case06",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "awk",
                        },
                    ],
                },
                "awk/myaplusb3.test.awk": {
                    "newest": True,
                    "verifications": [
                        {
                            "elapsed": 8358.0,
                            "heaviest": 728.0,
                            "last_execution_time": "2042-11-05T02:21:05.270000-10:00",
                            "slowest": 835.0,
                            "status": "success",
                            "testcases": [
                                {
                                    "elapsed": 2.18,
                                    "memory": 44.71,
                                    "name": "myaplusb2/one_minus_one",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.41,
                                    "memory": 53.47,
                                    "name": "myaplusb2/zero",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.08,
                                    "memory": 70.73,
                                    "name": "myaplusb/case13",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.6,
                                    "memory": 29.74,
                                    "name": "myaplusb/case11",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.93,
                                    "memory": 88.37,
                                    "name": "myaplusb/case05",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.23,
                                    "memory": 14.55,
                                    "name": "myaplusb/case09",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 5.8,
                                    "memory": 41.07,
                                    "name": "myaplusb/case10",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.18,
                                    "memory": 20.07,
                                    "name": "myaplusb/case07",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.41,
                                    "memory": 72.27,
                                    "name": "myaplusb/case02",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.21,
                                    "memory": 1.09,
                                    "name": "myaplusb/case04",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.04,
                                    "memory": 2.71,
                                    "name": "myaplusb/case16",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 6.67,
                                    "memory": 42.73,
                                    "name": "myaplusb/case08",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.83,
                                    "memory": 32.3,
                                    "name": "myaplusb/case12",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 8.72,
                                    "memory": 11.97,
                                    "name": "myaplusb/case01",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 9.56,
                                    "memory": 7.92,
                                    "name": "myaplusb/case03",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 0.98,
                                    "memory": 60.18,
                                    "name": "myaplusb/case14",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 1.18,
                                    "memory": 1.79,
                                    "name": "myaplusb/case15",
                                    "status": "AC",
                                },
                                {
                                    "elapsed": 2.03,
                                    "memory": 78.99,
                                    "name": "myaplusb/case06",
                                    "status": "AC",
                                },
                            ],
                            "verification_name": "awk",
                        },
                    ],
                },
                "python/failure.mle.py": {
                    "verifications": [
                        {
                            "verification_name": "Python",
                            "status": "failure",
                            "elapsed": 4426.0,
                            "last_execution_time": "1973-10-02T03:07:14.120000Z",
                            **(
                                {
                                    "slowest": 442.0,
                                    "heaviest": 349.0,
                                    "testcases": [
                                        {
                                            "name": "example_00",
                                            "status": "MLE",
                                            "elapsed": 5.34,
                                            "memory": 89.12,
                                        },
                                        {
                                            "name": "example_01",
                                            "status": "MLE",
                                            "elapsed": 9.79,
                                            "memory": 78.31,
                                        },
                                        {
                                            "name": "random_00",
                                            "status": "MLE",
                                            "elapsed": 4.8,
                                            "memory": 6.08,
                                        },
                                        {
                                            "name": "random_01",
                                            "status": "AC",
                                            "elapsed": 4.09,
                                            "memory": 15.08,
                                        },
                                        {
                                            "name": "random_02",
                                            "status": "AC",
                                            "elapsed": 3.33,
                                            "memory": 6.99,
                                        },
                                        {
                                            "name": "random_03",
                                            "status": "MLE",
                                            "elapsed": 4.04,
                                            "memory": 9.04,
                                        },
                                        {
                                            "name": "random_04",
                                            "status": "AC",
                                            "elapsed": 8.19,
                                            "memory": 81.73,
                                        },
                                        {
                                            "name": "random_05",
                                            "status": "AC",
                                            "elapsed": 0.18,
                                            "memory": 47.13,
                                        },
                                        {
                                            "name": "random_06",
                                            "status": "AC",
                                            "elapsed": 1.01,
                                            "memory": 68.03,
                                        },
                                        {
                                            "name": "random_07",
                                            "status": "MLE",
                                            "elapsed": 3.76,
                                            "memory": 40.93,
                                        },
                                        {
                                            "name": "random_08",
                                            "status": "AC",
                                            "elapsed": 1.32,
                                            "memory": 69.99,
                                        },
                                        {
                                            "name": "random_09",
                                            "status": "MLE",
                                            "elapsed": 0.12,
                                            "memory": 19.27,
                                        },
                                    ],
                                }
                                if time_command()
                                else {}
                            ),
                        }
                    ],
                    "newest": True,
                },
                "python/failure.wa.py": {
                    "verifications": [
                        {
                            "verification_name": "Python",
                            "status": "failure",
                            "elapsed": 3240.0,
                            "slowest": 324.0,
                            "heaviest": 994.0,
                            "testcases": [
                                {
                                    "name": "example_00",
                                    "status": "AC",
                                    "elapsed": 1.89,
                                    "memory": 34.41,
                                },
                                {
                                    "name": "example_01",
                                    "status": "AC",
                                    "elapsed": 2.17,
                                    "memory": 10.24,
                                },
                                {
                                    "name": "random_00",
                                    "status": "AC",
                                    "elapsed": 3.25,
                                    "memory": 7.82,
                                },
                                {
                                    "name": "random_01",
                                    "status": "WA",
                                    "elapsed": 7.41,
                                    "memory": 81.13,
                                },
                                {
                                    "name": "random_02",
                                    "status": "WA",
                                    "elapsed": 1.53,
                                    "memory": 91.42,
                                },
                                {
                                    "name": "random_03",
                                    "status": "AC",
                                    "elapsed": 4.6,
                                    "memory": 13.13,
                                },
                                {
                                    "name": "random_04",
                                    "status": "WA",
                                    "elapsed": 5.09,
                                    "memory": 38.65,
                                },
                                {
                                    "name": "random_05",
                                    "status": "WA",
                                    "elapsed": 6.34,
                                    "memory": 73.13,
                                },
                                {
                                    "name": "random_06",
                                    "status": "AC",
                                    "elapsed": 3.13,
                                    "memory": 32.18,
                                },
                                {
                                    "name": "random_07",
                                    "status": "AC",
                                    "elapsed": 8.88,
                                    "memory": 10.07,
                                },
                                {
                                    "name": "random_08",
                                    "status": "WA",
                                    "elapsed": 1.66,
                                    "memory": 88.91,
                                },
                                {
                                    "name": "random_09",
                                    "status": "WA",
                                    "elapsed": 9.41,
                                    "memory": 34.78,
                                },
                            ],
                            "last_execution_time": "1986-10-21T03:14:48.980000+11:00",
                        }
                    ],
                    "newest": True,
                },
                "python/failure.tle.py": {
                    "verifications": [
                        {
                            "verification_name": "Python",
                            "status": "failure",
                            "elapsed": 1020.0,
                            "slowest": 102.0,
                            "heaviest": 966.0,
                            "testcases": [
                                {
                                    "name": "judge_data",
                                    "status": "TLE",
                                    "elapsed": 6.75,
                                    "memory": 8.22,
                                }
                            ],
                            "last_execution_time": "2054-12-13T14:49:21.790000-08:00",
                        }
                    ],
                    "newest": True,
                },
                "python/success1.py": {
                    "verifications": [
                        {
                            "verification_name": "Python",
                            "status": "success",
                            "elapsed": 8685.0,
                            "slowest": 868.0,
                            "heaviest": 955.0,
                            "testcases": [
                                {
                                    "name": "example_00",
                                    "status": "AC",
                                    "elapsed": 8.66,
                                    "memory": 14.97,
                                },
                                {
                                    "name": "example_01",
                                    "status": "AC",
                                    "elapsed": 3.4,
                                    "memory": 82.48,
                                },
                                {
                                    "name": "random_00",
                                    "status": "AC",
                                    "elapsed": 6.01,
                                    "memory": 69.23,
                                },
                                {
                                    "name": "random_01",
                                    "status": "AC",
                                    "elapsed": 8.47,
                                    "memory": 16.15,
                                },
                                {
                                    "name": "random_02",
                                    "status": "AC",
                                    "elapsed": 1.28,
                                    "memory": 88.6,
                                },
                                {
                                    "name": "random_03",
                                    "status": "AC",
                                    "elapsed": 5.69,
                                    "memory": 85.15,
                                },
                                {
                                    "name": "random_04",
                                    "status": "AC",
                                    "elapsed": 2.52,
                                    "memory": 74.99,
                                },
                                {
                                    "name": "random_05",
                                    "status": "AC",
                                    "elapsed": 2.0,
                                    "memory": 4.66,
                                },
                                {
                                    "name": "random_06",
                                    "status": "AC",
                                    "elapsed": 4.46,
                                    "memory": 13.48,
                                },
                                {
                                    "name": "random_07",
                                    "status": "AC",
                                    "elapsed": 7.96,
                                    "memory": 6.91,
                                },
                                {
                                    "name": "random_08",
                                    "status": "AC",
                                    "elapsed": 7.67,
                                    "memory": 39.47,
                                },
                                {
                                    "name": "random_09",
                                    "status": "AC",
                                    "elapsed": 0.16,
                                    "memory": 36.45,
                                },
                            ],
                            "last_execution_time": "2034-09-03T09:15:32.640000+02:00",
                        }
                    ],
                    "newest": True,
                },
                "python/success2.py": {
                    "verifications": [
                        {
                            "verification_name": "Python",
                            "status": "success",
                            "elapsed": 735.0,
                            "slowest": 73.0,
                            "heaviest": 19.0,
                            "testcases": [
                                {
                                    "name": "example_00",
                                    "status": "AC",
                                    "elapsed": 1.1,
                                    "memory": 53.93,
                                },
                                {
                                    "name": "example_01",
                                    "status": "AC",
                                    "elapsed": 5.48,
                                    "memory": 50.39,
                                },
                                {
                                    "name": "random_00",
                                    "status": "AC",
                                    "elapsed": 9.31,
                                    "memory": 58.92,
                                },
                                {
                                    "name": "random_01",
                                    "status": "AC",
                                    "elapsed": 4.3,
                                    "memory": 35.83,
                                },
                                {
                                    "name": "random_02",
                                    "status": "AC",
                                    "elapsed": 2.64,
                                    "memory": 87.34,
                                },
                                {
                                    "name": "random_03",
                                    "status": "AC",
                                    "elapsed": 2.73,
                                    "memory": 54.56,
                                },
                                {
                                    "name": "random_04",
                                    "status": "AC",
                                    "elapsed": 5.98,
                                    "memory": 34.29,
                                },
                                {
                                    "name": "random_05",
                                    "status": "AC",
                                    "elapsed": 3.52,
                                    "memory": 91.97,
                                },
                                {
                                    "name": "random_06",
                                    "status": "AC",
                                    "elapsed": 7.15,
                                    "memory": 79.87,
                                },
                                {
                                    "name": "random_07",
                                    "status": "AC",
                                    "elapsed": 6.63,
                                    "memory": 11.11,
                                },
                                {
                                    "name": "random_08",
                                    "status": "AC",
                                    "elapsed": 6.53,
                                    "memory": 74.19,
                                },
                                {
                                    "name": "random_09",
                                    "status": "AC",
                                    "elapsed": 7.4,
                                    "memory": 27.16,
                                },
                            ],
                            "last_execution_time": "1991-06-27T16:59:27.680000+06:00",
                        }
                    ],
                    "newest": True,
                },
                "python/failure.re.py": {
                    "verifications": [
                        {
                            "verification_name": "Python",
                            "status": "failure",
                            "elapsed": 554.0,
                            "slowest": 55.0,
                            "heaviest": 10.0,
                            "testcases": [
                                {
                                    "name": "example_00",
                                    "status": "RE",
                                    "elapsed": 3.47,
                                    "memory": 55.14,
                                },
                                {
                                    "name": "example_01",
                                    "status": "RE",
                                    "elapsed": 4.8,
                                    "memory": 82.74,
                                },
                                {
                                    "name": "random_00",
                                    "status": "RE",
                                    "elapsed": 4.62,
                                    "memory": 53.04,
                                },
                                {
                                    "name": "random_01",
                                    "status": "RE",
                                    "elapsed": 5.6,
                                    "memory": 84.32,
                                },
                                {
                                    "name": "random_02",
                                    "status": "RE",
                                    "elapsed": 9.28,
                                    "memory": 18.09,
                                },
                                {
                                    "name": "random_03",
                                    "status": "RE",
                                    "elapsed": 6.41,
                                    "memory": 13.18,
                                },
                                {
                                    "name": "random_04",
                                    "status": "RE",
                                    "elapsed": 7.17,
                                    "memory": 63.97,
                                },
                                {
                                    "name": "random_05",
                                    "status": "RE",
                                    "elapsed": 7.59,
                                    "memory": 75.35,
                                },
                                {
                                    "name": "random_06",
                                    "status": "RE",
                                    "elapsed": 4.79,
                                    "memory": 50.9,
                                },
                                {
                                    "name": "random_07",
                                    "status": "RE",
                                    "elapsed": 2.83,
                                    "memory": 25.32,
                                },
                                {
                                    "name": "random_08",
                                    "status": "RE",
                                    "elapsed": 1.71,
                                    "memory": 53.67,
                                },
                                {
                                    "name": "random_09",
                                    "status": "RE",
                                    "elapsed": 4.52,
                                    "memory": 85.17,
                                },
                            ],
                            "last_execution_time": "2047-08-08T05:27:05.540000-08:00",
                        }
                    ],
                    "newest": True,
                },
                "python/skip.py": {
                    "verifications": [
                        {
                            "status": "skipped",
                            "elapsed": 5703.0,
                            "last_execution_time": "1999-08-27T06:18:53.270000-10:00",
                        }
                    ],
                    "newest": True,
                },
            },
        }
