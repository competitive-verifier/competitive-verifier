import datetime
import pathlib
from pathlib import Path
from typing import Any, Generator, Iterable
from unittest import mock
from zoneinfo import ZoneInfo

import pytest
from onlinejudge_command.subcommand.test import JudgeStatus
from pydantic import BaseModel

from competitive_verifier import git
from competitive_verifier.documents.builder import (
    load_static_files,
    render_source_code_stat_for_page,
    render_source_code_stats_for_top_page,
)
from competitive_verifier.documents.type import (
    FrontMatter,
    PageRenderJob,
    SiteRenderConfig,
)
from competitive_verifier.models.dependency import (
    SourceCodeStat,
    SourceCodeStatSlim,
    VerificationStatus,
)
from competitive_verifier.models.file import VerificationFile
from competitive_verifier.models.result import (
    VerificationResult,
    TestcaseResult as _TestcaseResult,
)
from competitive_verifier.models.result_status import ResultStatus

STATIC_FILES_PATH = "src/competitive_verifier_resources/jekyll"
# For windows test
static_files = git.ls_files(STATIC_FILES_PATH)


def test_load_static_files():
    config = SiteRenderConfig(
        config_yml={"foo": 1},
        destination_dir=Path("foo"),
        index_md=Path(__file__),
        static_dir=Path(__file__),
    )
    d = load_static_files(config=config)
    files = {p.relative_to(STATIC_FILES_PATH) for p in static_files}
    files.add(Path("_config.yml"))

    for f in files:
        print(f.as_posix())

    expected = {"foo" / f for f in files}
    assert set(d.keys()) == expected


class Input_render_source_code_stat_for_page(BaseModel):
    job: PageRenderJob
    stat: SourceCodeStat
    links: dict[pathlib.Path, dict[str, Any]]


def generate_render_source_code_stat_for_page_params() -> (
    Generator[
        tuple[Input_render_source_code_stat_for_page, str, dict[str, Any]], None, None
    ]
):
    links = {
        pathlib.Path("lib/any.txt"): {
            "path": "lib/any.txt",
            "title": "ANY",
            "icon": VerificationStatus.LIBRARY_SOME_WA.name,
        },
        pathlib.Path("lib/req.txt"): {
            "path": "lib/req.txt",
            "title": "LIBFAILURE",
            "icon": VerificationStatus.LIBRARY_ALL_WA.name,
        },
        pathlib.Path("lib/success.txt"): {
            "path": "lib/success.txt",
            "title": "LIB",
            "icon": VerificationStatus.LIBRARY_ALL_AC.name,
        },
        pathlib.Path("lib/failure.txt"): {
            "path": "lib/failure.txt",
            "title": "LIBFAILURE",
            "icon": VerificationStatus.LIBRARY_ALL_WA.name,
        },
        pathlib.Path("test/success.txt"): {
            "path": "test/success.txt",
            "title": "SUCCESS",
            "icon": VerificationStatus.TEST_ACCEPTED.name,
        },
        pathlib.Path("test/failure.txt"): {
            "path": "test/failure.txt",
            "title": "test/failure.txt",
            "icon": VerificationStatus.TEST_WAITING_JUDGE.name,
        },
    }
    tzinfo = ZoneInfo("Asia/Tokyo")

    yield (
        Input_render_source_code_stat_for_page(
            job=PageRenderJob(
                path=pathlib.Path("lib/success.txt"),
                content=b"Any Content",
                front_matter=FrontMatter(
                    title="FmTitle",
                    documentation_of="lib/success.txt",
                    layout="document",
                    data={"foo": "bar"},
                ),
            ),
            stat=SourceCodeStat(
                path=pathlib.Path("lib/success.txt"),
                is_verification=False,
                verification_status=VerificationStatus.LIBRARY_ALL_AC,
                timestamp=datetime.datetime(2023, 1, 2, 3, 4, 5, 678, tzinfo=tzinfo),
                required_by={pathlib.Path("lib/req.txt")},
                depends_on={pathlib.Path("lib/any.txt")},
                verified_with={pathlib.Path("test/success.txt")},
                file_input=VerificationFile(
                    dependencies={
                        pathlib.Path("lib/any.txt"),
                        pathlib.Path("test/success.txt"),
                    },
                    document_attributes={
                        "**FOO**": "😄",
                    },
                ),
            ),
            links=links,
        ),
        "echo OK",
        {
            "path": "lib/success.txt",
            "embedded": [{"name": "default", "code": "echo OK"}],
            "isVerificationFile": False,
            "verificationStatus": 1,
            "timestamp": "2023-01-02 03:04:05.000678+09:00",
            "dependsOn": ["lib/any.txt"],
            "requiredBy": ["lib/req.txt"],
            "verifiedWith": ["test/success.txt"],
            "attributes": {"**FOO**": "😄"},
            "testcases": None,
            "_pathExtension": "txt",
            "_verificationStatusIcon": "LIBRARY_ALL_AC",
            "_isVerificationFailed": False,
            "_extendedDependsOn": [
                {"path": "lib/any.txt", "title": "ANY", "icon": "LIBRARY_SOME_WA"}
            ],
            "_extendedRequiredBy": [
                {"path": "lib/req.txt", "title": "LIBFAILURE", "icon": "LIBRARY_ALL_WA"}
            ],
            "_extendedVerifiedWith": [
                {
                    "path": "test/success.txt",
                    "title": "SUCCESS",
                    "icon": "TEST_ACCEPTED",
                }
            ],
        },
    )

    yield (
        Input_render_source_code_stat_for_page(
            job=PageRenderJob(
                path=pathlib.Path("lib/any.txt"),
                content=b"Any Content",
                front_matter=FrontMatter(
                    title="FmTitle",
                    documentation_of="lib/any.txt",
                    layout="document",
                    data={"foo": "bar"},
                ),
            ),
            stat=SourceCodeStat(
                path=pathlib.Path("lib/any.txt"),
                is_verification=False,
                verification_status=VerificationStatus.LIBRARY_ALL_AC,
                timestamp=datetime.datetime(2023, 1, 2, 3, 4, 5, 678, tzinfo=tzinfo),
                required_by={
                    pathlib.Path("lib/success.txt"),
                },
                depends_on={pathlib.Path("lib/any.txt")},
                verified_with={pathlib.Path("test/success.txt")},
                file_input=VerificationFile(
                    dependencies={
                        pathlib.Path("lib/any.txt"),
                        pathlib.Path("test/success.txt"),
                    },
                    document_attributes={
                        "**FOO**": "😄",
                    },
                ),
            ),
            links=links,
        ),
        "# ANY !",
        {
            "path": "lib/any.txt",
            "embedded": [{"name": "default", "code": "# ANY !"}],
            "isVerificationFile": False,
            "verificationStatus": 1,
            "timestamp": "2023-01-02 03:04:05.000678+09:00",
            "dependsOn": ["lib/any.txt"],
            "requiredBy": ["lib/success.txt"],
            "verifiedWith": ["test/success.txt"],
            "attributes": {"**FOO**": "😄"},
            "testcases": None,
            "_pathExtension": "txt",
            "_verificationStatusIcon": "LIBRARY_ALL_AC",
            "_isVerificationFailed": False,
            "_extendedDependsOn": [
                {"path": "lib/any.txt", "title": "ANY", "icon": "LIBRARY_SOME_WA"}
            ],
            "_extendedRequiredBy": [
                {"path": "lib/success.txt", "title": "LIB", "icon": "LIBRARY_ALL_AC"}
            ],
            "_extendedVerifiedWith": [
                {
                    "path": "test/success.txt",
                    "title": "SUCCESS",
                    "icon": "TEST_ACCEPTED",
                }
            ],
        },
    )

    yield (
        Input_render_source_code_stat_for_page(
            job=PageRenderJob(
                path=pathlib.Path("lib/failure.txt"),
                content=b"Any Content",
                front_matter=FrontMatter(
                    title="FmTitle",
                    documentation_of="lib/failure.txt",
                    layout="document",
                    data={"foo": "bar"},
                ),
            ),
            stat=SourceCodeStat(
                path=pathlib.Path("lib/failure.txt"),
                is_verification=False,
                verification_status=VerificationStatus.TEST_WRONG_ANSWER,
                timestamp=datetime.datetime(2023, 1, 2, 3, 4, 5, 678, tzinfo=tzinfo),
                required_by=set(),
                depends_on={pathlib.Path("lib/failure.txt")},
                verified_with=set(),
                file_input=VerificationFile(
                    dependencies={
                        pathlib.Path("lib/failure.txt"),
                    },
                    document_attributes={
                        "**FOO**": "😄",
                    },
                ),
                verification_results=[
                    VerificationResult(
                        verification_name="handmade",
                        elapsed=13.35,
                        heaviest=313,
                        slowest=1.5,
                        status=ResultStatus.FAILURE,
                        testcases=[
                            _TestcaseResult(
                                name="case01",
                                status=JudgeStatus.AC,
                                elapsed=0.41,
                                memory=21,
                            ),
                            _TestcaseResult(
                                name="case02",
                                status=JudgeStatus.RE,
                                elapsed=0.32,
                                memory=42,
                            ),
                            _TestcaseResult(
                                name="case03",
                                status=JudgeStatus.WA,
                                elapsed=0.452,
                                memory=60,
                            ),
                            _TestcaseResult(
                                name="case04",
                                status=JudgeStatus.TLE,
                                elapsed=5.452,
                                memory=15,
                            ),
                        ],
                        last_execution_time=datetime.datetime(
                            2023, 6, 2, 3, 4, 5, 678, tzinfo=tzinfo
                        ),
                    ),
                ],
            ),
            links=links,
        ),
        "assert",
        {
            "path": "lib/failure.txt",
            "embedded": [{"name": "default", "code": "assert"}],
            "isVerificationFile": False,
            "verificationStatus": 7,
            "timestamp": "2023-01-02 03:04:05.000678+09:00",
            "dependsOn": ["lib/failure.txt"],
            "requiredBy": [],
            "verifiedWith": [],
            "attributes": {"**FOO**": "😄"},
            "testcases": [
                {
                    "elapsed": 0.41,
                    "environment": "handmade",
                    "memory": 21.0,
                    "name": "case01",
                    "status": "AC",
                },
                {
                    "elapsed": 0.32,
                    "environment": "handmade",
                    "memory": 42.0,
                    "name": "case02",
                    "status": "RE",
                },
                {
                    "elapsed": 0.452,
                    "environment": "handmade",
                    "memory": 60.0,
                    "name": "case03",
                    "status": "WA",
                },
                {
                    "elapsed": 5.452,
                    "environment": "handmade",
                    "memory": 15.0,
                    "name": "case04",
                    "status": "TLE",
                },
            ],
            "_pathExtension": "txt",
            "_verificationStatusIcon": "TEST_WRONG_ANSWER",
            "_isVerificationFailed": True,
            "_extendedDependsOn": [
                {
                    "path": "lib/failure.txt",
                    "title": "LIBFAILURE",
                    "icon": "LIBRARY_ALL_WA",
                }
            ],
            "_extendedRequiredBy": [],
            "_extendedVerifiedWith": [],
        },
    )


test_render_source_code_stat_for_page_params = list(
    generate_render_source_code_stat_for_page_params()
)


@pytest.mark.parametrize(
    "input,content,expected",
    test_render_source_code_stat_for_page_params,
)
def test_render_source_code_stat_for_page(
    input: Input_render_source_code_stat_for_page,
    content: str,
    expected: dict[str, Any],
):
    with mock.patch(
        "competitive_verifier.documents.builder.read_text_normalized",
        return_value=content,
    ):
        result = render_source_code_stat_for_page(
            job=input.job,
            path=input.stat.path,
            stat=input.stat,
            links=input.links,
        )
    assert result == expected


class Input_render_source_code_stats_for_top_page(BaseModel):
    stats_iter: Iterable[SourceCodeStatSlim]
    page_title_dict: dict[pathlib.Path, str]


test_render_source_code_stats_for_top_page_params: list[
    tuple[Input_render_source_code_stats_for_top_page, dict[str, Any]]
] = [
    (
        Input_render_source_code_stats_for_top_page(
            page_title_dict={
                pathlib.Path("src/LIBRARY_ALL_AC.py"): "accept",
                pathlib.Path("test/TEST_WAITING_JUDGE.py"): "Skipped",
                pathlib.Path("src/LIBRARY_PARTIAL_AC.py"): "src/LIBRARY_PARTIAL_AC.py",
                pathlib.Path("src/LIBRARY_SOME_WA.py"): "src/LIBRARY_SOME_WA.py",
                pathlib.Path("src/LIBRARY_NO_TESTS.py"): "src/LIBRARY_NO_TESTS.py",
                pathlib.Path("test/TEST_ACCEPTED.py"): "test/TEST_ACCEPTED.py",
                pathlib.Path("test/TEST_WRONG_ANSWER.py"): "test/TEST_WRONG_ANSWER.py",
            },
            stats_iter=[
                SourceCodeStatSlim(
                    path=pathlib.Path("src/LIBRARY_ALL_AC.py"),
                    is_verification=False,
                    verification_status=VerificationStatus.LIBRARY_ALL_AC,
                ),
                SourceCodeStatSlim(
                    path=pathlib.Path("src/LIBRARY_PARTIAL_AC.py"),
                    is_verification=False,
                    verification_status=VerificationStatus.LIBRARY_PARTIAL_AC,
                ),
                SourceCodeStatSlim(
                    path=pathlib.Path("src/LIBRARY_SOME_WA.py"),
                    is_verification=False,
                    verification_status=VerificationStatus.LIBRARY_SOME_WA,
                ),
                SourceCodeStatSlim(
                    path=pathlib.Path("src/LIBRARY_NO_TESTS.py"),
                    is_verification=False,
                    verification_status=VerificationStatus.LIBRARY_NO_TESTS,
                ),
                SourceCodeStatSlim(
                    path=pathlib.Path("test/TEST_ACCEPTED.py"),
                    is_verification=True,
                    verification_status=VerificationStatus.TEST_ACCEPTED,
                ),
                SourceCodeStatSlim(
                    path=pathlib.Path("test/TEST_WAITING_JUDGE.py"),
                    is_verification=True,
                    verification_status=VerificationStatus.TEST_WAITING_JUDGE,
                ),
                SourceCodeStatSlim(
                    path=pathlib.Path("test/TEST_WRONG_ANSWER.py"),
                    is_verification=True,
                    verification_status=VerificationStatus.TEST_WRONG_ANSWER,
                ),
            ],
        ),
        {
            "libraryCategories": [
                {
                    "name": "src",
                    "pages": [
                        {
                            "path": "src/LIBRARY_ALL_AC.py",
                            "title": "accept",
                            "icon": "LIBRARY_ALL_AC",
                        },
                        {
                            "path": "src/LIBRARY_NO_TESTS.py",
                            "title": "src/LIBRARY_NO_TESTS.py",
                            "icon": "LIBRARY_NO_TESTS",
                        },
                        {
                            "path": "src/LIBRARY_PARTIAL_AC.py",
                            "title": "src/LIBRARY_PARTIAL_AC.py",
                            "icon": "LIBRARY_PARTIAL_AC",
                        },
                        {
                            "path": "src/LIBRARY_SOME_WA.py",
                            "title": "src/LIBRARY_SOME_WA.py",
                            "icon": "LIBRARY_SOME_WA",
                        },
                    ],
                }
            ],
            "verificationCategories": [
                {
                    "name": "test",
                    "pages": [
                        {
                            "path": "test/TEST_ACCEPTED.py",
                            "title": "test/TEST_ACCEPTED.py",
                            "icon": "TEST_ACCEPTED",
                        },
                        {
                            "path": "test/TEST_WAITING_JUDGE.py",
                            "title": "Skipped",
                            "icon": "TEST_WAITING_JUDGE",
                        },
                        {
                            "path": "test/TEST_WRONG_ANSWER.py",
                            "title": "test/TEST_WRONG_ANSWER.py",
                            "icon": "TEST_WRONG_ANSWER",
                        },
                    ],
                }
            ],
        },
    ),
]


@pytest.mark.parametrize(
    "input, expected",
    test_render_source_code_stats_for_top_page_params,
)
def test_render_source_code_stats_for_top_page(
    input: Input_render_source_code_stats_for_top_page,
    expected: dict[str, Any],
):
    result = render_source_code_stats_for_top_page(
        stats_iter=input.stats_iter,
        page_title_dict=input.page_title_dict,
    )
    assert result == expected
