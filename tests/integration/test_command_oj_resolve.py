import json
import pathlib
from typing import Optional, Protocol

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.oj.verify.languages import special_comments
from competitive_verifier.oj_resolve.main import main

from .types import FilePaths
from .data.integration_data import IntegrationData


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
    def text_without_include_exclude(
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
        assert resolved == {}

    # def test_with_config_include_nobundle(
    #     self,
    #     make_args: _ArgsFunc,
    #     user_defined_and_python_data: UserDefinedAndPythonData,
    #     capfd: pytest.CaptureFixture[str],
    #     file_paths: FilePaths,
    # ):
    #     expected = user_defined_and_python_data.expected()
    #     expected["files"]["UserDefinedAndPythonData/encoding/EUC-KR.txt"]["additonal_sources"] = []
    #     expected["files"]["UserDefinedAndPythonData/encoding/cp932.txt"]["additonal_sources"] = []
    #     args = make_args(
    #         include=[file_paths.targets],
    #         config="config.toml",
    #         bundle=False,
    #     )
    #     main(args)
    #     stdout = capfd.readouterr().out
    #     resolved = json.loads(stdout)
    #     assert resolved == expected

    # test_with_include_exclude_param: list[tuple[list[str], list[str]]] = [
    #     (
    #         ["UserDefinedAndPythonData/**/*.py", "**/*.awk", "**/*.txt"],
    #         [],
    #     ),
    #     (
    #         ["UserDefinedAndPythonData/"],
    #         ["dummy/dummy.py"],
    #     ),
    #     (
    #         ["UserDefinedAndPythonData/encoding", "UserDefinedAndPythonData/awk", "UserDefinedAndPythonData/python"],
    #         ["dummy/"],
    #     ),
    #     (
    #         ["UserDefinedAndPythonData/encoding", "UserDefinedAndPythonData/awk", "UserDefinedAndPythonData/python"],
    #         [],
    #     ),
    #     (
    #         ["**/*.py", "**/*.awk", "**/*.txt"],
    #         ["dummy/"],
    #     ),
    # ]

    # @pytest.mark.parametrize(
    #     "include, exclude",
    #     test_with_include_exclude_param,
    #     ids=range(len(test_with_include_exclude_param)),
    # )
    # @pytest.mark.usefixtures("setenv_resolve")
    # def test_with_include_exclude(
    #     self,
    #     include: list[str],
    #     exclude: list[str],
    #     make_args: _ArgsFunc,
    #     user_defined_and_python_data: UserDefinedAndPythonData,
    #     capfd: pytest.CaptureFixture[str],
    # ):
    #     expected = user_defined_and_python_data.expected()
    #     del expected["files"]["UserDefinedAndPythonData/encoding/EUC-KR.txt"]
    #     del expected["files"]["UserDefinedAndPythonData/encoding/cp932.txt"]

    #     args = make_args(include=include, exclude=exclude)
    #     main(args)
    #     stdout = capfd.readouterr().out
    #     resolved = json.loads(stdout)
    #     assert resolved == expected

    # @pytest.mark.usefixtures("setenv_resolve")
    # def test_without_args(
    #     self,
    #     monkeypatch: pytest.MonkeyPatch,
    #     make_args: _ArgsFunc,
    #     user_defined_and_python_data: UserDefinedAndPythonData,
    #     capfd: pytest.CaptureFixture[str],
    # ):

    #     expected = user_defined_and_python_data.expected()
    #     del expected["files"]["UserDefinedAndPythonData/encoding/EUC-KR.txt"]
    #     del expected["files"]["UserDefinedAndPythonData/encoding/cp932.txt"]

    #     expected["files"]["dummy/dummy.py"] = {
    #         "additonal_sources": [],
    #         "dependencies": ["dummy/dummy.py"],
    #         "document_attributes": {"links": []},
    #         "verification": [],
    #     }

    #     monkeypatch.chdir("UserDefinedAndPythonData/python")
    #     args = make_args()
    #     main(args)
    #     stdout = capfd.readouterr().out
    #     resolved = json.loads(stdout)
    #     assert resolved == expected
