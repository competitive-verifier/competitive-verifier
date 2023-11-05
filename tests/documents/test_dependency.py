import datetime
from pathlib import Path
from typing import Any
from unittest import mock

import pytest
from pydantic import RootModel

from competitive_verifier.documents.render import SourceCodeStat, StatusIcon
from competitive_verifier.models import VerificationInput, VerifyCommandResult

Parser = RootModel[dict[Path, SourceCodeStat]]

test_resolve_dependency_params: list[tuple[str, Any, Any, Any, Any]] = [
    (
        "AC",
        {
            "files": {
                "c1/a.py": {},
                "c1/b1.py": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "c1/b2.py": {"dependencies": ["c1/b1.py"]},
                "c1/test.py": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
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
        ["c1/a.py", "c1/b1.py", "c1/b2.py", "c1/test.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "file_input": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
                "is_verification": True,
                "verification_status": StatusIcon.TEST_ACCEPTED,
                "verification_results": [
                    {
                        "status": "success",
                        "elapsed": 1,
                        "last_execution_time": datetime.datetime(2020, 2, 15),
                    },
                ],
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "file_input": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_ALL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py"},
                "verified_with": {"c1/test.py"},
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "file_input": {"dependencies": ["c1/b1.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_ALL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "file_input": {},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_ALL_AC,
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
                "c1/test.py": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "failure",
                        }
                    ],
                },
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
        ["c1/a.py", "c1/b1.py", "c1/b2.py", "c1/test.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "file_input": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "failure",
                        }
                    ],
                },
                "is_verification": True,
                "verification_status": StatusIcon.TEST_WRONG_ANSWER,
                "verification_results": [
                    {
                        "status": "failure",
                        "elapsed": 1,
                        "last_execution_time": datetime.datetime(2020, 2, 15),
                    },
                ],
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "file_input": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_ALL_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py"},
                "verified_with": {"c1/test.py"},
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "file_input": {"dependencies": ["c1/b1.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_ALL_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "file_input": {},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_ALL_WA,
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
                "c1/test.py": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
                "c1/test2.py": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "skipped",
                        }
                    ],
                },
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
        ["c1/a.py", "c1/b1.py", "c1/b2.py", "c1/test.py", "c1/test2.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "file_input": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
                "is_verification": True,
                "verification_status": StatusIcon.TEST_ACCEPTED,
                "verification_results": [
                    {
                        "status": "success",
                        "elapsed": 1,
                        "last_execution_time": datetime.datetime(2020, 2, 15),
                    },
                ],
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/test2.py": {
                "path": "c1/test2.py",
                "file_input": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "skipped",
                        }
                    ],
                },
                "is_verification": True,
                "verification_status": StatusIcon.TEST_WAITING_JUDGE,
                "verification_results": [
                    {
                        "status": "skipped",
                        "elapsed": 1,
                        "last_execution_time": datetime.datetime(2020, 2, 15),
                    },
                ],
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "file_input": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_PARTIAL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py"},
                "verified_with": {"c1/test.py", "c1/test2.py"},
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "file_input": {"dependencies": ["c1/b1.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_PARTIAL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "file_input": {},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_PARTIAL_AC,
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
                "c1/test.py": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
                "c1/test2.py": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "failure",
                        }
                    ],
                },
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
        ["c1/a.py", "c1/b1.py", "c1/b2.py", "c1/test.py", "c1/test2.py"],
        {
            "c1/test.py": {
                "path": "c1/test.py",
                "file_input": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
                "is_verification": True,
                "verification_status": StatusIcon.TEST_ACCEPTED,
                "verification_results": [
                    {
                        "status": "success",
                        "elapsed": 1,
                        "last_execution_time": datetime.datetime(2020, 2, 15),
                    },
                ],
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/test2.py": {
                "path": "c1/test2.py",
                "file_input": {
                    "dependencies": ["c1/b1.py"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "failure",
                        }
                    ],
                },
                "is_verification": True,
                "verification_status": StatusIcon.TEST_WRONG_ANSWER,
                "verification_results": [
                    {
                        "status": "failure",
                        "elapsed": 1,
                        "last_execution_time": datetime.datetime(2020, 2, 15),
                    },
                ],
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": set(),
                "verified_with": set(),
            },
            "c1/b1.py": {
                "path": "c1/b1.py",
                "file_input": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_SOME_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py"},
                "verified_with": {"c1/test.py", "c1/test2.py"},
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "file_input": {"dependencies": ["c1/b1.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_SOME_WA,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "file_input": {},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_SOME_WA,
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
        ["c1/a.py", "c1/b1.py", "c1/b2.py", "c1/test.py"],
        {
            "c1/b1.py": {
                "path": "c1/b1.py",
                "file_input": {"dependencies": ["c1/a.py", "c1/b2.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_NO_TESTS,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b2.py", "c1/a.py"},
                "required_by": {"c1/b2.py"},
                "verified_with": set(),
            },
            "c1/b2.py": {
                "path": "c1/b2.py",
                "file_input": {"dependencies": ["c1/b1.py"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_NO_TESTS,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/b1.py"},
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
            "c1/a.py": {
                "path": "c1/a.py",
                "file_input": {},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_NO_TESTS,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": set(),
                "required_by": {"c1/b1.py"},
                "verified_with": set(),
            },
        },
    ),
    (
        "Test depends on lib",
        {
            "files": {
                "c1/hello.java": {
                    "dependencies": ["c1/hello.java", "c1/hello_test.java"]
                },
                "c1/hello_test.java": {
                    "dependencies": ["c1/hello.java", "c1/hello_test.java"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
            }
        },
        {
            "total_seconds": 10,
            "files": {
                "c1/hello_test.java": {
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
        ["c1/hello.java", "c1/hello_test.java"],
        {
            "c1/hello.java": {
                "path": "c1/hello.java",
                "file_input": {"dependencies": ["c1/hello.java", "c1/hello_test.java"]},
                "is_verification": False,
                "verification_status": StatusIcon.LIBRARY_ALL_AC,
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/hello_test.java"},
                "required_by": set(),
                "verified_with": {"c1/hello_test.java"},
            },
            "c1/hello_test.java": {
                "path": "c1/hello_test.java",
                "file_input": {
                    "dependencies": ["c1/hello.java", "c1/hello_test.java"],
                    "verification": [
                        {
                            "type": "const",
                            "status": "success",
                        }
                    ],
                },
                "is_verification": True,
                "verification_status": StatusIcon.TEST_ACCEPTED,
                "verification_results": [
                    {
                        "status": "success",
                        "elapsed": 1,
                        "last_execution_time": datetime.datetime(2020, 2, 15),
                    }
                ],
                "timestamp": datetime.datetime(2010, 2, 15, 0, 0),
                "depends_on": {"c1/hello.java"},
                "required_by": {"c1/hello.java"},
                "verified_with": set(),
            },
        },
    ),
]


@pytest.mark.parametrize(
    "name, dep_input_obj, dep_result_obj, included_files_str, expected_obj",
    test_resolve_dependency_params,
    ids=[tup[0] for tup in test_resolve_dependency_params],
)
def test_resolve_dependency(
    name: str,
    dep_input_obj: Any,
    dep_result_obj: Any,
    included_files_str: list[str],
    expected_obj: Any,
):
    with mock.patch(
        "competitive_verifier.git.get_commit_time",
        return_value=datetime.datetime(2010, 2, 15),
    ):
        dep_input = VerificationInput.model_validate(dep_input_obj)
        dep_result = VerifyCommandResult.model_validate(dep_result_obj)

        resolved = SourceCodeStat.resolve_dependency(
            input=dep_input,
            result=dep_result,
            included_files=set(Path(s) for s in included_files_str),
        )
        expected = Parser.model_validate(expected_obj).root
        assert resolved == expected


test_StatusIcon_is_success_params: list[tuple[StatusIcon, bool]] = [
    (StatusIcon.LIBRARY_ALL_AC, True),
    (StatusIcon.LIBRARY_PARTIAL_AC, True),
    (StatusIcon.LIBRARY_SOME_WA, False),
    (StatusIcon.LIBRARY_ALL_WA, False),
    (StatusIcon.LIBRARY_NO_TESTS, True),
    (StatusIcon.TEST_ACCEPTED, True),
    (StatusIcon.TEST_WRONG_ANSWER, False),
    (StatusIcon.TEST_WAITING_JUDGE, True),
]


@pytest.mark.parametrize(
    "status, is_success",
    test_StatusIcon_is_success_params,
)
def test_StatusIcon_is_success(
    status: StatusIcon,
    is_success: bool,
):
    assert status.is_success == is_success
    assert status.is_failed != is_success
