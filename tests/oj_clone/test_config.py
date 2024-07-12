# pyright: reportGeneralTypeIssues=false
import io
import textwrap
from typing import Any

import pytest
from pydantic import ValidationError
from pydantic_core import ErrorDetails

from competitive_verifier.oj.verify.list import OjVerifyConfig

default_languages: dict[str, Any] = {
    "cpp": {},
    "go": {
        "execute": {
            "command": ["go", "run", "{basedir}/{path}"],
            "env": {"GO111MODULE": "off"},
        },
    },
    "haskell": {
        "execute": {
            "command": ["runghc", "{basedir}/{path}"],
        },
    },
    "java": {},
    "nim": {"environments": []},
    "ruby": {
        "execute": {
            "command": ["ruby", "{basedir}/{path}"],
        },
    },
    "rust": {},
}


test_oj_resolve_config_load_params: dict[str, tuple[str, dict[str, Any]]] = {
    "not_deifne": (
        textwrap.dedent(""),
        {"languages": default_languages},
    ),
    "empty_deifne": (
        textwrap.dedent(
            """
            [languages.cpp]
            [languages.go]
            [languages.haskell]
            [languages.java]
            [languages.nim]
            [languages.ruby]
            [languages.rust]
            """
        ),
        {"languages": default_languages},
    ),
    "full_define": (
        textwrap.dedent(
            r"""
            [languages.cpp]
            [[languages.cpp.environments]]
            CXX = "g++"
            CXXFLAGS = ["flags"]
            extra = 1
            [[languages.cpp.environments]]
            CXX = "clang++"
            extra = 2
            [languages.go]
            execute = "env GO111MODULE=off go run {basedir}/{path}"
            [languages.haskell]
            execute = "runghc {basedir}/{path}"
            [languages.java]
            [languages.nim]
            [[languages.nim.environments]]
            compile_to = "cpp"
            NIMFLAGS = ["-d:release", "--opt:speed"]
            [languages.ruby]
            execute = "ruby {basedir}/{path}"
            [languages.rust]
            [languages.rust.list_dependencies_backend]
            kind = "cargo-udeps"
            toolchain = "nightly"
            [languages.awk]
            compile = "bash -c 'echo hello > {tempdir}/hello'"
            execute = "env AWKPATH={basedir} awk -f {path}"
            bundle = "false"
            list_dependencies = "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' {path}"
            """
        ),
        {
            "languages": {
                "cpp": {
                    "environments": [
                        {"CXX": "g++", "CXXFLAGS": ["flags"]},
                        {"CXX": "clang++"},
                    ]
                },
                "go": {
                    "execute": "env GO111MODULE=off go run {basedir}/{path}",
                },
                "haskell": {
                    "execute": "runghc {basedir}/{path}",
                },
                "java": {},
                "nim": {
                    "environments": [
                        {"compile_to": "cpp", "NIMFLAGS": ["-d:release", "--opt:speed"]}
                    ],
                },
                "ruby": {
                    "execute": "ruby {basedir}/{path}",
                },
                "rust": {
                    "list_dependencies_backend": {
                        "kind": "cargo-udeps",
                        "toolchain": "nightly",
                    }
                },
                "awk": {
                    "compile": "bash -c 'echo hello > {tempdir}/hello'",
                    "execute": "env AWKPATH={basedir} awk -f {path}",
                    "bundle": "false",
                    "list_dependencies": "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' {path}",
                },
            },
        },
    ),
    "rust_kind_none": (
        textwrap.dedent(
            """
            [languages.rust.list_dependencies_backend]
            kind = "none"
            """
        ),
        {
            "languages": default_languages
            | {
                "rust": {
                    "list_dependencies_backend": {
                        "kind": "none",
                    }
                },
            }
        },
    ),
}


@pytest.mark.parametrize(
    "toml, expected",
    test_oj_resolve_config_load_params.values(),
    ids=test_oj_resolve_config_load_params.keys(),
)
def test_oj_resolve_config_load(toml: str, expected: Any):
    with io.BytesIO(toml.encode("utf-8")) as fp:
        assert OjVerifyConfig.load(fp).model_dump(exclude_none=True) == expected


class ErrorDetailsWithUrl(ErrorDetails):
    url: str


test_oj_resolve_config_load_error_params: dict[
    str, tuple[str, list[ErrorDetailsWithUrl]]
] = {
    "cpp_no_CXX": (
        textwrap.dedent(
            r"""
            [languages.cpp]
            [[languages.cpp.environments]]
            CX = "g++"
            """
        ),
        [
            {
                "input": {"CX": "g++"},
                "loc": ("languages", "cpp", "environments", 0, "CXX"),
                "msg": "Field required",
                "type": "missing",
                "url": "https://errors.pydantic.dev/2.8/v/missing",
            },
        ],
    ),
    "java_with_execute_and_compile": (
        textwrap.dedent(
            r"""
            [languages.java]
            compile = "javac {path}"
            execute = "java {path}"
            """
        ),
        [
            {
                "ctx": {
                    "error": ValueError(
                        'You cannot overwrite "execute" for Java language'
                    )
                },
                "input": "java {path}",
                "loc": ("languages", "java", "execute"),
                "msg": 'Value error, You cannot overwrite "execute" for Java language',
                "type": "value_error",
                "url": "https://errors.pydantic.dev/2.8/v/value_error",
            },
            {
                "ctx": {
                    "error": ValueError(
                        'You cannot overwrite "compile" for Java language'
                    )
                },
                "input": "javac {path}",
                "loc": ("languages", "java", "compile"),
                "msg": 'Value error, You cannot overwrite "compile" for Java language',
                "type": "value_error",
                "url": "https://errors.pydantic.dev/2.8/v/value_error",
            },
        ],
    ),
    "user_defined_no_execute": (
        textwrap.dedent(
            r"""
            [languages.awk]
            compile = "bash -c 'echo hello > {tempdir}/hello'"
            bundle = "false"
            list_dependencies = "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' {path}"
            """
        ),
        [
            {
                "input": {
                    "bundle": "false",
                    "compile": "bash -c 'echo hello > {tempdir}/hello'",
                    "list_dependencies": "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' "
                    "{path}",
                },
                "loc": ("languages", "awk", "execute"),
                "msg": "Field required",
                "type": "missing",
                "url": "https://errors.pydantic.dev/2.8/v/missing",
            },
        ],
    ),
    "user_defined_no_execute_2": (
        textwrap.dedent(
            r"""
            [languages.awk]
            compile = "bash -c 'echo hello > {tempdir}/hello'"
            bundle = "false"
            list_dependencies = "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' {path}"
            [languages.txt]
            """
        ),
        [
            {
                "input": {
                    "bundle": "false",
                    "compile": "bash -c 'echo hello > {tempdir}/hello'",
                    "list_dependencies": "sed 's/^@include \"\\(.*\\)\"$/\\1/ ; t ; d' "
                    "{path}",
                },
                "loc": ("languages", "awk", "execute"),
                "msg": "Field required",
                "type": "missing",
                "url": "https://errors.pydantic.dev/2.8/v/missing",
            },
            {
                "input": {},
                "loc": ("languages", "txt", "execute"),
                "msg": "Field required",
                "type": "missing",
                "url": "https://errors.pydantic.dev/2.8/v/missing",
            },
        ],
    ),
}


@pytest.mark.parametrize(
    "toml, expected_error",
    test_oj_resolve_config_load_error_params.values(),
    ids=test_oj_resolve_config_load_error_params.keys(),
)
def test_oj_resolve_config_load_error(toml: str, expected_error: list[ErrorDetails]):
    with io.BytesIO(toml.encode("utf-8")) as fp:
        with pytest.raises(ValidationError) as excinfo:
            OjVerifyConfig.load(fp)
        e: ValidationError = excinfo.value
        errors = e.errors()
        assert len(errors) == len(expected_error)
        for i, ex in enumerate(errors):
            expected_ctx = expected_error[i].get("ctx")
            if expected_ctx and expected_ctx.get("error"):
                assert "ctx" in ex
                assert ex["ctx"]["error"].args == expected_ctx["error"].args
                del ex["ctx"]["error"]
                del expected_ctx["error"]
        assert errors == expected_error
