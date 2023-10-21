from pathlib import Path
import pathlib
from typing import Any, Iterable
from pydantic import BaseModel

import pytest

from competitive_verifier import git
from competitive_verifier.documents.builder import (
    load_static_files,
    render_source_code_stat_for_page,
    render_source_code_stats_for_top_page,
)
from competitive_verifier.documents.type import PageRenderJob, SiteRenderConfig
from competitive_verifier.models.dependency import (
    SourceCodeStat,
    SourceCodeStatSlim,
    VerificationStatus,
)

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
    path: pathlib.Path
    stats: dict[pathlib.Path, SourceCodeStat]
    page_title_dict: dict[pathlib.Path, str]


test_render_source_code_stat_for_page_params: list[
    tuple[Input_render_source_code_stat_for_page, dict[str, Any]]
] = []


@pytest.mark.parametrize(
    "input, expected",
    test_render_source_code_stat_for_page_params,
)
def test_render_source_code_stat_for_page(
    input: Input_render_source_code_stat_for_page,
    expected: dict[str, Any],
):
    result = render_source_code_stat_for_page(
        job=input.job,
        path=input.path,
        stats=input.stats,
        page_title_dict=input.page_title_dict,
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
