import json
import pathlib
from typing import Optional, Protocol

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.oj.verify.languages import special_comments
from competitive_verifier.oj_resolve.main import main

from .data.integration_data import IntegrationData
from .types import FilePaths


@pytest.fixture
def setenv_resolve(mocker: MockerFixture):
    special_comments.list_special_comments.cache_clear()
    special_comments.list_embedded_urls.cache_clear()

    def python_get_execute_command(
        path: pathlib.Path, *, basedir: pathlib.Path, tempdir: pathlib.Path
    ) -> str:
        return f"env PYTHONPATH={basedir.resolve().as_posix()} python {path.as_posix()}"

    mocker.patch(
        "competitive_verifier.oj.verify.languages.python.PythonLanguageEnvironment.get_execute_command",
        side_effect=python_get_execute_command,
    )


class _ArgsFunc(Protocol):
    def __call__(
        self,
        *,
        bundle: bool = True,
        include: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
        config: Optional[str] = None,
    ) -> list[str]:
        ...


@pytest.fixture
def make_args() -> _ArgsFunc:
    def _make_args(
        *,
        bundle: bool = False,
        include: Optional[list[str]] = None,
        exclude: Optional[list[str]] = None,
        config: Optional[str] = None,
    ) -> list[str]:
        args: list[str] = []
        if not bundle:
            args.append("--no-bundle")
        if include is not None:
            args.append("--include")
            args.extend(include)
        if exclude is not None:
            args.append("--exclude")
            args.extend(exclude)
        if config is not None:
            args.append("--config")
            args.append(config)
        return args

    return _make_args


@pytest.mark.usefixtures("additional_path")
@pytest.mark.order(-1000)
class TestCommandOjResolve:
    @pytest.mark.each_language_integration
    @pytest.mark.integration
    @pytest.mark.usefixtures("setenv_resolve")
    def test_oj_resolve_by_lang_data(
        self,
        make_args: _ArgsFunc,
        integration_data: IntegrationData,
        capfd: pytest.CaptureFixture[str],
    ):
        expected = integration_data.expected_verify_json()
        args = make_args(
            include=integration_data.include_path,
            exclude=integration_data.exclude_path,
            config=integration_data.config_path,
            bundle=True,
        )
        main(args)

        stdout = capfd.readouterr().out
        resolved = json.loads(stdout)
        assert resolved == expected

        verify = integration_data.config_dir_path / "verify.json"
        verify.parent.mkdir(parents=True, exist_ok=True)
        verify.write_text(stdout, encoding="utf-8")

    @pytest.mark.usefixtures("setenv_resolve")
    def test_without_include_exclude(
        self,
        make_args: _ArgsFunc,
        monkeypatch: pytest.MonkeyPatch,
        file_paths: FilePaths,
        capfd: pytest.CaptureFixture[str],
    ):
        monkeypatch.chdir(file_paths.root / "IncludeExclude")
        args = make_args(
            config="config.toml",
            bundle=True,
        )
        main(args)

        stdout = capfd.readouterr().out
        resolved = json.loads(stdout)
        assert resolved == {
            "files": {
                "a1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["a1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "a2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["a2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "b1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["b1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "b2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["b2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "c1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["c1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "c2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["c2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/a1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/a2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/b1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/b1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/b2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/b2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/c1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/c1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/c2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/c2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
            },
        }

    @pytest.mark.usefixtures("setenv_resolve")
    def test_with_include1(
        self,
        make_args: _ArgsFunc,
        monkeypatch: pytest.MonkeyPatch,
        file_paths: FilePaths,
        capfd: pytest.CaptureFixture[str],
    ):
        monkeypatch.chdir(file_paths.root / "IncludeExclude")
        args = make_args(
            include=["subdir/"],
            config="config.toml",
            bundle=True,
        )
        main(args)

        stdout = capfd.readouterr().out
        resolved = json.loads(stdout)
        assert resolved == {
            "files": {
                "subdir/a1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/a2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/b1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/b1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/b2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/b2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/c1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/c1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/c2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/c2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
            },
        }

    @pytest.mark.usefixtures("setenv_resolve")
    def test_with_include2(
        self,
        make_args: _ArgsFunc,
        monkeypatch: pytest.MonkeyPatch,
        file_paths: FilePaths,
        capfd: pytest.CaptureFixture[str],
    ):
        monkeypatch.chdir(file_paths.root / "IncludeExclude")
        args = make_args(
            include=["**a*.txt"],
            config="config.toml",
            bundle=True,
        )
        main(args)

        stdout = capfd.readouterr().out
        resolved = json.loads(stdout)
        assert resolved == {
            "files": {
                "a1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["a1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "a2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["a2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/a1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/a2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
            },
        }

    @pytest.mark.usefixtures("setenv_resolve")
    def test_with_exclude1(
        self,
        make_args: _ArgsFunc,
        monkeypatch: pytest.MonkeyPatch,
        file_paths: FilePaths,
        capfd: pytest.CaptureFixture[str],
    ):
        monkeypatch.chdir(file_paths.root / "IncludeExclude")
        args = make_args(
            exclude=["subdir/"],
            config="config.toml",
            bundle=True,
        )
        main(args)

        stdout = capfd.readouterr().out
        resolved = json.loads(stdout)
        assert resolved == {
            "files": {
                "a1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["a1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "a2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["a2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "b1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["b1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "b2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["b2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "c1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["c1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "c2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["c2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
            },
        }

    @pytest.mark.usefixtures("setenv_resolve")
    def test_with_exclude2(
        self,
        make_args: _ArgsFunc,
        monkeypatch: pytest.MonkeyPatch,
        file_paths: FilePaths,
        capfd: pytest.CaptureFixture[str],
    ):
        monkeypatch.chdir(file_paths.root / "IncludeExclude")
        args = make_args(
            exclude=["a*.txt", "b*.txt"],
            config="config.toml",
            bundle=True,
        )
        main(args)

        stdout = capfd.readouterr().out
        resolved = json.loads(stdout)
        assert resolved == {
            "files": {
                "c1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["c1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "c2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["c2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/a1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/a2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/a2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/b1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/b1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/b2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/b2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/c1.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/c1.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
                "subdir/c2.txt": {
                    "additonal_sources": [],
                    "dependencies": ["subdir/c2.txt"],
                    "document_attributes": {},
                    "verification": [],
                },
            },
        }
