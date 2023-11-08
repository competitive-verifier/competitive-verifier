from typing import Any, Optional

import pytest

from ..types import ConfigDirSetter, FilePaths
from .integration_data import IntegrationData


class UserDefinedAndPythonData(IntegrationData):
    def __init__(
        self,
        monkeypatch: pytest.MonkeyPatch,
        set_config_dir: ConfigDirSetter,
        file_paths: FilePaths,
    ) -> None:
        super().__init__(monkeypatch, set_config_dir, file_paths)

    @property
    def bundle_euc_ke_path(self):
        return (
            self.file_paths.dest_root
            / "config"
            / self.name
            / "bundled/encoding/EUC-KR.txt"
        )

    @property
    def bundle_cp932_path(self):
        return (
            self.file_paths.dest_root
            / "config"
            / self.name
            / "bundled/encoding/cp932.txt"
        )

    @property
    def config_path(self) -> Optional[str]:
        return (self.targets_path / "config.toml").as_posix()

    @property
    def exclude_path(self) -> Optional[list[str]]:
        return ["dummy/"]

    def assert_extra(self):
        assert self.bundle_euc_ke_path.read_bytes().strip() == b"cp949"
        assert self.bundle_cp932_path.read_bytes().strip() == b"cp932"

    def expected(self) -> dict[str, Any]:
        return dict(
            {
                "files": {
                    "awk/aplusb.awk": {
                        "additonal_sources": [],
                        "dependencies": ["awk/aplusb.awk"],
                        "document_attributes": {"TITLE": 'Calculate "A + ' 'B"'},
                        "verification": [],
                    },
                    "awk/aplusb.test.awk": {
                        "additonal_sources": [],
                        "dependencies": ["awk/aplusb.test.awk"],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb"
                        },
                        "verification": [
                            {
                                "command": f"env AWKPATH={self.targets_path.as_posix()} awk -f awk/aplusb.test.awk",
                                "compile": f"ls {self.config_dir_path.as_posix()}/cache/problems/8e3916c7805235eb07ec2a58660d89c6",
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
                                "command": f"env AWKPATH={self.targets_path.as_posix()} awk -f awk/aplusb_direct.awk",
                                "compile": f"ls {self.config_dir_path.as_posix()}/cache/problems/8e3916c7805235eb07ec2a58660d89c6",
                                "name": "awk",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                                "type": "problem",
                            }
                        ],
                    },
                    "encoding/EUC-KR.txt": {
                        "dependencies": ["encoding/EUC-KR.txt"],
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
                        "dependencies": ["encoding/cp932.txt"],
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
        )
