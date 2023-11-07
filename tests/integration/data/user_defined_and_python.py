from typing import Any

from ..types import ConfigDirSetter, FilePaths
from .integration_data import IntegrationData


class UserDefinedAndPythonData(IntegrationData):
    def __init__(self, set_config_dir: ConfigDirSetter, file_paths: FilePaths) -> None:
        super().__init__(set_config_dir, file_paths)

    @property
    def bundle_euc_ke_path(self):
        return (
            self.file_paths.dest_root
            / "config"
            / self.name
            / "bundled/targets/encoding/EUC-KR.txt"
        )

    @property
    def bundle_cp932_path(self):
        return (
            self.file_paths.dest_root
            / "config"
            / self.name
            / "bundled/targets/encoding/cp932.txt"
        )

    def assert_extra(self):
        assert self.bundle_euc_ke_path.read_bytes().strip() == b"cp949"
        assert self.bundle_cp932_path.read_bytes().strip() == b"cp932"

    def expected(self) -> dict[str, Any]:
        file_paths = self.file_paths

        return dict(
            {
                "files": {
                    "targets/encoding/EUC-KR.txt": {
                        "dependencies": ["targets/encoding/EUC-KR.txt"],
                        "verification": [],
                        "document_attributes": {},
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": self.bundle_euc_ke_path.as_posix(),
                            }
                        ],
                    },
                    "targets/encoding/cp932.txt": {
                        "dependencies": ["targets/encoding/cp932.txt"],
                        "verification": [],
                        "document_attributes": {},
                        "additonal_sources": [
                            {
                                "name": "bundled",
                                "path": self.bundle_cp932_path.as_posix(),
                            }
                        ],
                    },
                    "targets/python/lib_all_failure.py": {
                        "dependencies": ["targets/python/lib_all_failure.py"],
                        "verification": [],
                        "document_attributes": {"links": []},
                        "additonal_sources": [],
                    },
                    "targets/python/lib_some_failure.py": {
                        "dependencies": ["targets/python/lib_some_failure.py"],
                        "verification": [],
                        "document_attributes": {"TITLE": "Units📏", "links": []},
                        "additonal_sources": [],
                    },
                    "targets/python/lib_skip.py": {
                        "dependencies": ["targets/python/lib_skip.py"],
                        "verification": [],
                        "document_attributes": {"links": []},
                        "additonal_sources": [],
                    },
                    "targets/python/lib_some_skip_some_wa.py": {
                        "dependencies": ["targets/python/lib_some_skip_some_wa.py"],
                        "verification": [],
                        "document_attributes": {"links": []},
                        "additonal_sources": [],
                    },
                    "targets/python/success1.py": {
                        "dependencies": [
                            "targets/python/lib_some_failure.py",
                            "targets/python/lib_some_skip.py",
                            "targets/python/success1.py",
                        ],
                        "verification": [
                            {
                                "name": "Python",
                                "type": "problem",
                                "command": f"env PYTHONPATH={file_paths.root.as_posix()} python targets/python/success1.py",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                            }
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "additonal_sources": [],
                    },
                    "targets/python/failure.wa.py": {
                        "dependencies": [
                            "targets/python/failure.wa.py",
                            "targets/python/lib_all_failure.py",
                            "targets/python/lib_some_skip_some_wa.py",
                        ],
                        "verification": [
                            {
                                "name": "Python",
                                "type": "problem",
                                "command": f"env PYTHONPATH={file_paths.root.as_posix()} python targets/python/failure.wa.py",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                            }
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "additonal_sources": [],
                    },
                    "targets/python/failure.mle.py": {
                        "dependencies": [
                            "targets/python/failure.mle.py",
                            "targets/python/lib_all_failure.py",
                            "targets/python/lib_some_failure.py",
                        ],
                        "verification": [
                            {
                                "name": "Python",
                                "type": "problem",
                                "command": f"env PYTHONPATH={file_paths.root.as_posix()} python targets/python/failure.mle.py",
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
                    "targets/python/skip.py": {
                        "dependencies": [
                            "targets/python/lib_skip.py",
                            "targets/python/lib_some_skip_some_wa.py",
                            "targets/python/skip.py",
                        ],
                        "verification": [{"type": "const", "status": "skipped"}],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "IGNORE": "",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "additonal_sources": [],
                    },
                    "targets/python/success2.py": {
                        "dependencies": [
                            "targets/python/lib_all_success.py",
                            "targets/python/lib_some_skip_some_wa.py",
                            "targets/python/success2.py",
                        ],
                        "verification": [
                            {
                                "name": "Python",
                                "type": "problem",
                                "command": f"env PYTHONPATH={file_paths.root.as_posix()} python targets/python/success2.py",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                            }
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "additonal_sources": [],
                    },
                    "targets/python/lib_all_success.py": {
                        "dependencies": ["targets/python/lib_all_success.py"],
                        "verification": [],
                        "document_attributes": {"links": []},
                        "additonal_sources": [],
                    },
                    "targets/python/failure.re.py": {
                        "dependencies": [
                            "targets/python/failure.re.py",
                            "targets/python/lib_all_failure.py",
                        ],
                        "verification": [
                            {
                                "name": "Python",
                                "type": "problem",
                                "command": f"env PYTHONPATH={file_paths.root.as_posix()} python targets/python/failure.re.py",
                                "problem": "https://judge.yosupo.jp/problem/aplusb",
                            }
                        ],
                        "document_attributes": {
                            "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                            "links": ["https://judge.yosupo.jp/problem/aplusb"],
                        },
                        "additonal_sources": [],
                    },
                    "targets/python/lib_some_skip.py": {
                        "dependencies": ["targets/python/lib_some_skip.py"],
                        "verification": [],
                        "document_attributes": {"links": []},
                        "additonal_sources": [],
                    },
                    "targets/python/failure.tle.py": {
                        "dependencies": [
                            "targets/python/failure.tle.py",
                            "targets/python/lib_all_failure.py",
                        ],
                        "verification": [
                            {
                                "name": "Python",
                                "type": "problem",
                                "command": f"env PYTHONPATH={file_paths.root.as_posix()} python targets/python/failure.tle.py",
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
                }
            }
        )
