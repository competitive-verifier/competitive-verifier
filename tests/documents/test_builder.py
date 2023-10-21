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
from competitive_verifier.models.dependency import SourceCodeStat

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
    stats_iter: Iterable[SourceCodeStat]
    page_title_dict: dict[pathlib.Path, str]


test_render_source_code_stats_for_top_page_params: list[
    tuple[Input_render_source_code_stats_for_top_page, dict[str, Any]]
] = [
    (
        Input_render_source_code_stats_for_top_page(
            page_title_dict={pathlib.Path("foo/bar.py"): "FOOBAR"},
            stats_iter=[
                SourceCodeStat(
                    path=pathlib.Path("foo/bar.py"),
                    depends_on={},
                    required_by={pathlib.Path("foo/baz.py")},
                    verified_with={},
                ),
                SourceCodeStat(
                    path=pathlib.Path("foo/baz.py"),
                    depends_on={pathlib.Path("foo/bar.py")},
                    required_by={},
                    verified_with={pathlib.Path("foo/test.py")},
                ),
                SourceCodeStat(
                    path=pathlib.Path("foo/test.py"),
                    depends_on={},
                    required_by={pathlib.Path("foo/baz.py")},
                    verified_with={},
                ),
            ],
        ),
        {},
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
