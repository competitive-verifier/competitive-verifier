import datetime
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from pydantic import BaseModel

from competitive_verifier.models import (
    SourceCodeStat,
    VerificationInput,
    VerificationStatus,
    VerifyCommandResult,
    resolve_dependency,
)


class Parser(BaseModel):
    __root__: dict[Path, SourceCodeStat]


test_resolve_dependency_params: list[tuple[str, Any, Any, Any, Any]] = [
    (
        "AC",
        {
            "files": {
                "c1/a.py": {},
                "c1/b1.py": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "c1/b2.py": {"dependencies": ["c1/b1.py"]},
                "c1/test.py": {"dependencies": ["c1/b1.py"]},
            }
        },
        {
            "total_seconds": 10,
            "files": {
                "c1/test.py": {
                    "verifications": [
                        {
                            "status": "success",
                            "elapsed": 1,
                            "last_execution_time": datetime.datetime(2020, 2, 15),
                        },
                    ]
                },
            },
        },
        ["otherpath.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "is_verification": True,
                "verification_status": VerificationStatus.TEST_ACCEPTED,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_ALL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py", "c1/test.py"},
                "verified_with": set(),
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_ALL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_ALL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": set(),
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
        },
    ),
    (
        "WA",
        {
            "files": {
                "c1/a.py": {},
                "c1/b1.py": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "c1/b2.py": {"dependencies": ["c1/b1.py"]},
                "c1/test.py": {"dependencies": ["c1/b1.py"]},
            }
        },
        {
            "total_seconds": 10,
            "files": {
                "c1/test.py": {
                    "verifications": [
                        {
                            "status": "failure",
                            "elapsed": 1,
                            "last_execution_time": datetime.datetime(2020, 2, 15),
                        },
                    ]
                },
            },
        },
        ["otherpath.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "is_verification": True,
                "verification_status": VerificationStatus.TEST_WRONG_ANSWER,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_ALL_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py", "c1/test.py"},
                "verified_with": set(),
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_ALL_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_ALL_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": set(),
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
        },
    ),
    (
        "AC & skip",
        {
            "files": {
                "c1/a.py": {},
                "c1/b1.py": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "c1/b2.py": {"dependencies": ["c1/b1.py"]},
                "c1/test.py": {"dependencies": ["c1/b1.py"]},
                "c1/test2.py": {"dependencies": ["c1/b1.py"]},
            }
        },
        {
            "total_seconds": 10,
            "files": {
                "c1/test.py": {
                    "verifications": [
                        {
                            "status": "success",
                            "elapsed": 1,
                            "last_execution_time": datetime.datetime(2020, 2, 15),
                        },
                    ]
                },
                "c1/test2.py": {
                    "verifications": [
                        {
                            "status": "skipped",
                            "elapsed": 1,
                            "last_execution_time": datetime.datetime(2020, 2, 15),
                        },
                    ]
                },
            },
        },
        ["otherpath.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "is_verification": True,
                "verification_status": VerificationStatus.TEST_ACCEPTED,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/test2.py": {
                "path": "c1/test2.py",
                "is_verification": True,
                "verification_status": VerificationStatus.TEST_WAITING_JUDGE,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_PARTIAL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py", "c1/test.py", "c1/test2.py"},
                "verified_with": set(),
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_PARTIAL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_PARTIAL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": set(),
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
        },
    ),
    (
        "AC & WA",
        {
            "files": {
                "c1/a.py": {},
                "c1/b1.py": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "c1/b2.py": {"dependencies": ["c1/b1.py"]},
                "c1/test.py": {"dependencies": ["c1/b1.py"]},
                "c1/test2.py": {"dependencies": ["c1/b1.py"]},
            }
        },
        {
            "total_seconds": 10,
            "files": {
                "c1/test.py": {
                    "verifications": [
                        {
                            "status": "success",
                            "elapsed": 1,
                            "last_execution_time": datetime.datetime(2020, 2, 15),
                        },
                    ]
                },
                "c1/test2.py": {
                    "verifications": [
                        {
                            "status": "failure",
                            "elapsed": 1,
                            "last_execution_time": datetime.datetime(2020, 2, 15),
                        },
                    ]
                },
            },
        },
        ["otherpath.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "is_verification": True,
                "verification_status": VerificationStatus.TEST_ACCEPTED,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/test2.py": {
                "path": "c1/test2.py",
                "is_verification": True,
                "verification_status": VerificationStatus.TEST_WRONG_ANSWER,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_SOME_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py", "c1/test.py", "c1/test2.py"},
                "verified_with": set(),
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_SOME_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_SOME_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": set(),
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
        },
    ),
    (
        "no tests",
        {
            "files": {
                "c1/a.py": {},
                "c1/b1.py": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "c1/b2.py": {"dependencies": ["c1/b1.py"]},
            }
        },
        {
            "total_seconds": 10,
            "files": {
                "c1/test.py": {
                    "verifications": [
                        {
                            "status": "failure",
                            "elapsed": 1,
                            "last_execution_time": datetime.datetime(2020, 2, 15),
                        },
                    ]
                },
            },
        },
        ["otherpath.py"],
        {
            "c1/b1.py": {
                "path": "c1/b1.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_NO_TESTS,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py"},
                "verified_with": set(),
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_NO_TESTS,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "is_verification": False,
                "verification_status": VerificationStatus.LIBRARY_NO_TESTS,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": set(),
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
        },
    ),
]


@pytest.mark.parametrize(
    "name, dep_input_obj, dep_result_obj, excluded_files_str, expected_obj",
    test_resolve_dependency_params,
    ids=[tup[0] for tup in test_resolve_dependency_params],
)
def test_resolve_dependency(
    name: str,
    dep_input_obj: Any,
    dep_result_obj: Any,
    excluded_files_str: list[str],
    expected_obj: Any,
):
    with mock.patch(
        "competitive_verifier.models.dependency.git.get_commit_time",
        return_value=datetime.datetime(2010, 2, 15),
    ):
        dep_input = VerificationInput.parse_obj(dep_input_obj)
        dep_result = VerifyCommandResult.parse_obj(dep_result_obj)

        resolved = resolve_dependency(
            input=dep_input,
            result=dep_result,
            excluded_files=set(Path(s) for s in excluded_files_str),
        )
        expected = Parser.parse_obj(expected_obj).__root__
        assert resolved == expected
