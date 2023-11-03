import datetime
import filecmp
import inspect
import os
import pathlib
from typing import Any
from unittest import mock
from pydantic import BaseModel

import pytest
import yaml

import competitive_verifier.documents.builder
from competitive_verifier.documents.main import main

TARGETS_PATH = "testdata/targets"
VERIFY_FILE_PATH = "testdata/test-verify.json"
RESULT_FILE_PATH = "testdata/test-result.json"
DESTINATION_ROOT = pathlib.Path("testdata/dst_dir")

DEFAULT_ARGS = [
    "--verify-json",
    VERIFY_FILE_PATH,
    RESULT_FILE_PATH,
]

tzinfo = datetime.timezone(datetime.timedelta(hours=9), name="Asia/Tokyo")
MOCK_TIME = datetime.datetime(2023, 12, 4, 5, 6, 7, 8910, tzinfo=tzinfo)


class MarkdownData(BaseModel):
    path: str
    front_matter: dict[str, Any]
    content: bytes = b""


TARGETS: list[MarkdownData] = [
    MarkdownData(path=f"{TARGETS_PATH}/encoding/EUC-KR.txt.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/encoding/cp932.txt.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/failure.mle.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/failure.re.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/failure.tle.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/failure.wa.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/lib_all_failure.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/lib_all_success.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/lib_skip.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/lib_some_failure.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/lib_some_skip.py.md", front_matter={}),
    MarkdownData(
        path=f"{TARGETS_PATH}/python/lib_some_skip_some_wa.py.md", front_matter={}
    ),
    MarkdownData(path=f"{TARGETS_PATH}/python/skip.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/success1.py.md", front_matter={}),
    MarkdownData(path=f"{TARGETS_PATH}/python/success2.py.md", front_matter={}),
]


@pytest.fixture(scope="session")
def clean():
    import shutil

    if DESTINATION_ROOT.is_dir():
        shutil.rmtree(DESTINATION_ROOT)


@pytest.fixture(scope="session")
def setup_docs(clean: Any):
    os.environ["GITHUB_REF_NAME"] = "TESTING_GIT_REF"
    os.environ["GITHUB_WORKFLOW"] = "TESTING_WORKFLOW"


def check_common(destination: pathlib.Path):
    assert destination.is_dir()

    targets = {t.path: t for t in TARGETS}

    for target_file in filter(
        lambda p: p.is_file(),
        (destination / TARGETS_PATH).glob("**/*"),
    ):
        path_str = target_file.relative_to(destination).as_posix()
        target_value = target_file.read_bytes().strip()
        assert target_value.startswith(b"---\n")
        del targets[path_str]

    assert not targets


class MockEnvTestcaseResult(competitive_verifier.documents.builder.EnvTestcaseResult):
    pass


@pytest.mark.usefixtures("setup_docs")
def test_with_config():
    destination = DESTINATION_ROOT / inspect.stack()[0].function
    docs_settings_dir = pathlib.Path("testdata/docs_settings")

    with mock.patch(
        "competitive_verifier.git.get_commit_time",
        return_value=MOCK_TIME,
    ):
        main(
            [
                "--docs",
                docs_settings_dir.as_posix(),
                "--destination",
                destination.as_posix(),
            ]
            + DEFAULT_ARGS
        )

    check_common(destination)

    config_yml = yaml.safe_load((destination / "_config.yml").read_bytes())
    assert config_yml == {
        "action_name": "TESTING_WORKFLOW",
        "basedir": "",
        "branch_name": "TESTING_GIT_REF",
        "description": "My description",
        "filename-index": True,
        "highlightjs-style": "vs2015",
        "plugins": [
            "jemoji",
            "jekyll-redirect-from",
            "jekyll-remote-theme",
        ],
        "mathjax": 2,
        "sass": {"style": "compressed"},
        "theme": "jekyll-theme-modernist",
        "icons": {
            "LIBRARY_ALL_AC": ":heavy_check_mark:",
            "LIBRARY_ALL_WA": ":x:",
            "LIBRARY_NO_TESTS": ":warning:",
            "LIBRARY_PARTIAL_AC": ":heavy_check_mark:",
            "LIBRARY_SOME_WA": ":question:",
            "TEST_ACCEPTED": ":100:",
            "TEST_WAITING_JUDGE": ":warning:",
            "TEST_WRONG_ANSWER": ":x:",
        },
    }

    assert (destination / "static.md").exists()
    assert (destination / "static.md").read_text(
        encoding="utf-8"
    ) == "# Static page\n\nI'm Static!"

    static_dir = docs_settings_dir / "static"
    for static_file in filter(lambda p: p.is_file(), static_dir.glob("**/*")):
        assert filecmp.cmp(
            static_file, destination / static_file.relative_to(static_dir)
        )


@pytest.mark.usefixtures("setup_docs")
def test_without_config():
    destination = DESTINATION_ROOT / inspect.stack()[0].function

    with mock.patch(
        "competitive_verifier.git.get_commit_time",
        return_value=MOCK_TIME,
    ):
        main(
            [
                "--docs",
                "testdata/nothing",
                "--destination",
                destination.as_posix(),
            ]
            + DEFAULT_ARGS
        )

    check_common(destination)

    config_yml = yaml.safe_load((destination / "_config.yml").read_bytes())
    assert config_yml == {
        "action_name": "TESTING_WORKFLOW",
        "basedir": "",
        "branch_name": "TESTING_GIT_REF",
        "description": '<small>This documentation is automatically generated by <a href="https://github.com/competitive-verifier/competitive-verifier">competitive-verifier/competitive-verifier</a></small>',
        "filename-index": False,
        "highlightjs-style": "default",
        "plugins": [
            "jemoji",
            "jekyll-redirect-from",
            "jekyll-remote-theme",
        ],
        "mathjax": 3,
        "sass": {"style": "compressed"},
        "theme": "jekyll-theme-minimal",
        "icons": {
            "LIBRARY_ALL_AC": ":heavy_check_mark:",
            "LIBRARY_ALL_WA": ":x:",
            "LIBRARY_NO_TESTS": ":warning:",
            "LIBRARY_PARTIAL_AC": ":heavy_check_mark:",
            "LIBRARY_SOME_WA": ":question:",
            "TEST_ACCEPTED": ":heavy_check_mark:",
            "TEST_WAITING_JUDGE": ":warning:",
            "TEST_WRONG_ANSWER": ":x:",
        },
    }

    assert not (destination / "static.md").exists()

    resource_dir = pathlib.Path("src/competitive_verifier_resources/jekyll")
    for resource_file in filter(lambda p: p.is_file(), resource_dir.glob("**/*")):
        assert filecmp.cmp(
            resource_file, destination / resource_file.relative_to(resource_dir)
        )
