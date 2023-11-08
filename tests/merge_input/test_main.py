import pytest

import competitive_verifier.merge_input.main
from competitive_verifier.models import VerificationInput

test_merge_params: list[tuple[list[VerificationInput], VerificationInput]] = [
    (
        [
            VerificationInput.model_validate(
                {
                    "files": {
                        "foo/bar.py": {},
                        "foo/baz.py": {
                            "path": "foo/baz.py",
                            "document_attributes": {
                                "title": "foo-baz",
                            },
                            "dependencies": ["foo/bar.py"],
                            "verification": [
                                {
                                    "type": "const",
                                    "status": "success",
                                }
                            ],
                        },
                    },
                }
            ),
        ],
        VerificationInput.model_validate(
            {
                "files": {
                    "foo/bar.py": {},
                    "foo/baz.py": {
                        "path": "foo/baz.py",
                        "document_attributes": {
                            "title": "foo-baz",
                        },
                        "dependencies": ["foo/bar.py"],
                        "verification": [
                            {
                                "type": "const",
                                "status": "success",
                            }
                        ],
                    },
                },
            }
        ),
    ),
    (
        [
            VerificationInput.model_validate(
                {
                    "files": {
                        "foo/bar.py": {},
                        "foo/baz.py": {
                            "path": "foo/baz.py",
                            "document_attributes": {
                                "title": "foo-baz",
                            },
                            "dependencies": ["foo/bar.py"],
                            "verification": [
                                {
                                    "type": "const",
                                    "status": "success",
                                }
                            ],
                        },
                    },
                }
            ),
            VerificationInput.model_validate(
                {
                    "files": {
                        "hoge/bar.py": {},
                        "hoge/baz.py": {
                            "path": "hoge/baz.py",
                            "document_attributes": {
                                "title": "foo-baz",
                            },
                            "dependencies": ["hoge/bar.py"],
                            "verification": [
                                {
                                    "type": "const",
                                    "status": "success",
                                }
                            ],
                        },
                    },
                }
            ),
        ],
        VerificationInput.model_validate(
            {
                "files": {
                    "foo/bar.py": {},
                    "foo/baz.py": {
                        "path": "foo/baz.py",
                        "document_attributes": {
                            "title": "foo-baz",
                        },
                        "dependencies": ["foo/bar.py"],
                        "verification": [
                            {
                                "type": "const",
                                "status": "success",
                            }
                        ],
                    },
                    "hoge/bar.py": {},
                    "hoge/baz.py": {
                        "path": "hoge/baz.py",
                        "document_attributes": {
                            "title": "foo-baz",
                        },
                        "dependencies": ["hoge/bar.py"],
                        "verification": [
                            {
                                "type": "const",
                                "status": "success",
                            }
                        ],
                    },
                },
            }
        ),
    ),
]


@pytest.mark.parametrize(
    "inputs, expected",
    test_merge_params,
    ids=range(len(test_merge_params)),
)
def test_merge(inputs: list[VerificationInput], expected: VerificationInput):
    assert competitive_verifier.merge_input.main.merge(inputs) == expected
