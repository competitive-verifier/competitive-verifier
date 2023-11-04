import filecmp
import inspect
import json
import logging
import os
import pathlib
from typing import Any

import pytest
from pytest_mock import MockerFixture
from pytest_subtests import SubTests

from competitive_verifier.oj_resolve.main import main

from .data import RESULT_FILE_PATH, TARGETS_PATH, VERIFY_FILE_PATH


@pytest.fixture
def setenv_resolve(mocker: MockerFixture):
    def python_get_execute_command(
        path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return f"env PYTHONPATH=/dummy/ python {path.as_posix()}"

    mocker.patch(
        "competitive_verifier_oj_clone.languages.python.PythonLanguageEnvironment.get_execute_command",
        side_effect=python_get_execute_command,
    )


@pytest.mark.usefixtures("setenv_resolve")
def test_with_config_include(capfd: pytest.CaptureFixture[str]):
    main(
        [
            "--include",
            TARGETS_PATH,
            "--config",
            "config.toml",
        ]
    )
    stdout = capfd.readouterr().out
    resolved = json.loads(stdout)
    assert (
        pathlib.Path(".competitive-verifier/bundled/targets/encoding/EUC-KR.txt")
        .read_bytes()
        .strip()
        == b"cp949"
    )
    assert (
        pathlib.Path(".competitive-verifier/bundled/targets/encoding/cp932.txt")
        .read_bytes()
        .strip()
        == b"cp932"
    )
    assert resolved == {
        "files": {
            "targets/encoding/EUC-KR.txt": {
                "dependencies": ["targets/encoding/EUC-KR.txt"],
                "verification": [],
                "document_attributes": {},
                "additonal_sources": [
                    {
                        "name": "bundled",
                        "path": ".competitive-verifier/bundled/targets/encoding/EUC-KR.txt",
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
                        "path": ".competitive-verifier/bundled/targets/encoding/cp932.txt",
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
                "document_attributes": {"links": []},
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/success1.py",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.wa.py",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.mle.py",
                        "problem": "https://judge.yosupo.jp/problem/aplusb",
                        "mle": 10.0,
                    }
                ],
                "document_attributes": {
                    "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                    "MLE": "10",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/success2.py",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.re.py",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.tle.py",
                        "problem": "https://judge.yosupo.jp/problem/aplusb",
                        "tle": 0.09,
                    }
                ],
                "document_attributes": {
                    "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                    "TLE": "0.09",
                    "links": ["https://judge.yosupo.jp/problem/aplusb"],
                },
                "additonal_sources": [],
            },
        }
    }

    pathlib.Path(VERIFY_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(VERIFY_FILE_PATH).write_text(stdout)


@pytest.mark.usefixtures("setenv_resolve")
def test_with_config_include_nobundle(capfd: pytest.CaptureFixture[str]):
    main(
        [
            "--no-bundle",
            "--include",
            TARGETS_PATH,
            "--config",
            "config.toml",
        ]
    )
    stdout = capfd.readouterr().out
    resolved = json.loads(stdout)
    assert resolved == {
        "files": {
            "targets/python/lib_all_failure.py": {
                "dependencies": ["targets/python/lib_all_failure.py"],
                "verification": [],
                "document_attributes": {"links": []},
                "additonal_sources": [],
            },
            "targets/python/lib_some_failure.py": {
                "dependencies": ["targets/python/lib_some_failure.py"],
                "verification": [],
                "document_attributes": {"links": []},
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/success1.py",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.wa.py",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.mle.py",
                        "problem": "https://judge.yosupo.jp/problem/aplusb",
                        "mle": 10.0,
                    }
                ],
                "document_attributes": {
                    "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                    "MLE": "10",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/success2.py",
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
            "targets/encoding/EUC-KR.txt": {
                "dependencies": ["targets/encoding/EUC-KR.txt"],
                "verification": [],
                "document_attributes": {},
                "additonal_sources": [],
            },
            "targets/encoding/cp932.txt": {
                "dependencies": ["targets/encoding/cp932.txt"],
                "verification": [],
                "document_attributes": {},
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.re.py",
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
                        "command": "env PYTHONPATH=/dummy/ python targets/python/failure.tle.py",
                        "problem": "https://judge.yosupo.jp/problem/aplusb",
                        "tle": 0.09,
                    }
                ],
                "document_attributes": {
                    "PROBLEM": "https://judge.yosupo.jp/problem/aplusb",
                    "TLE": "0.09",
                    "links": ["https://judge.yosupo.jp/problem/aplusb"],
                },
                "additonal_sources": [],
            },
        }
    }

    pathlib.Path(VERIFY_FILE_PATH).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(VERIFY_FILE_PATH).write_text(stdout)
