import pathlib
import shutil
import subprocess
from collections.abc import Sequence

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.oj.languages import cplusplus
from competitive_verifier.oj.languages.cplusplus import CPlusPlusLanguageEnvironment

_compilers = [cxx for cxx in ("g++", "clang++") if shutil.which(cxx)]


def _include_directories(
    cxx: str, cxx_flags: Sequence[str], basedir: pathlib.Path
) -> list[pathlib.Path]:
    env = CPlusPlusLanguageEnvironment(CXX=pathlib.Path(cxx), CXXFLAGS=list(cxx_flags))
    return env.include_directories.get(basedir)


@pytest.mark.integration
@pytest.mark.skipif(not _compilers, reason="no C++ compiler is installed")
@pytest.mark.parametrize("cxx", _compilers)
@pytest.mark.parametrize(
    ("cxx_flags", "expected"),
    [
        ((), []),
        (("-O2",), []),
        (("-I", "src"), ["src"]),
        (("-Isrc",), ["src"]),
        (("-iquote", "include"), ["include"]),
        (("-iquoteinclude",), ["include"]),
        (("-isystem", "third_party"), ["third_party"]),
        (("-idirafter", "fallback"), ["fallback"]),
        (
            ("-I", "src", "-Wall", "-Ithird_party", "-iquote", "include"),
            ["include", "src", "third_party"],
        ),
    ],
)
def test_include_directories(
    cxx: str,
    cxx_flags: tuple[str, ...],
    expected: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    for name in ("src", "include", "third_party", "fallback"):
        (tmp_path / name).mkdir()
    monkeypatch.chdir(tmp_path)
    dirs = _include_directories(cxx, cxx_flags, tmp_path)
    # The flag directories plus basedir, which the compile command adds with -I.
    assert sorted(dirs) == sorted(
        [*((tmp_path / p).resolve() for p in expected), tmp_path.resolve()]
    )


@pytest.mark.integration
def test_include_directories_fallback(tmp_path: pathlib.Path):
    assert _include_directories("no-such-compiler", ("-I", "src"), tmp_path) == [
        tmp_path
    ]


@pytest.mark.integration
@pytest.mark.skipif(not _compilers, reason="no C++ compiler is installed")
@pytest.mark.parametrize("cxx", _compilers)
def test_include_directories_keeps_basedir_in_cpath(
    cxx: str,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    tmp_path = tmp_path.resolve()
    (tmp_path / "src").mkdir()
    monkeypatch.chdir(tmp_path)
    # basedir is searched by default through CPATH, but must stay in the list.
    monkeypatch.setenv("CPATH", str(tmp_path))
    assert _include_directories(cxx, ("-I", "src"), tmp_path) == [
        tmp_path / "src",
        tmp_path,
    ]


@pytest.mark.integration
@pytest.mark.skipif(not _compilers, reason="no C++ compiler is installed")
@pytest.mark.parametrize("cxx", _compilers)
def test_include_directories_depends_on_cwd(
    cxx: str,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    tmp_path = tmp_path.resolve()
    results: list[list[pathlib.Path]] = []
    for project in ("a", "b"):
        (tmp_path / project / "include").mkdir(parents=True)
        monkeypatch.chdir(tmp_path / project)
        results.append(_include_directories(cxx, ("-I", "include"), tmp_path / project))
    assert results == [
        [tmp_path / "a" / "include", tmp_path / "a"],
        [tmp_path / "b" / "include", tmp_path / "b"],
    ]


@pytest.mark.integration
@pytest.mark.skipif(not _compilers, reason="no C++ compiler is installed")
@pytest.mark.parametrize("cxx", _compilers)
def test_include_directories_queries_once_per_basedir(
    cxx: str, tmp_path: pathlib.Path, mocker: MockerFixture
):
    spy = mocker.spy(cplusplus, "exec_command")
    env = CPlusPlusLanguageEnvironment(CXX=pathlib.Path(cxx), CXXFLAGS=[])
    for _ in range(2):
        for basedir in ("a", "b"):
            env.include_directories.get(tmp_path / basedir)
    # One run with the flags and one without, per distinct basedir.
    assert spy.call_count == 4


@pytest.mark.integration
def test_include_directories_strip_framework_annotation(
    tmp_path: pathlib.Path, mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch
):
    tmp_path = tmp_path.resolve()
    frameworks = tmp_path / "sdk" / "Frameworks"
    system = tmp_path / "usr" / "include"

    def run(command: list[str], **kwargs: object) -> subprocess.CompletedProcess[str]:
        with_flags = "-I" in command
        lines = ["ignoring nonexistent directory", '#include "..." search starts here:']
        if with_flags:
            lines.append(" include")
        lines.append("#include <...> search starts here:")
        if with_flags:
            lines.append(f" {frameworks} (framework directory)")
        lines += [f" {system}", "End of search list.", " ignored"]
        return subprocess.CompletedProcess(
            command, 0, stdout="", stderr="".join(f"{line}\n" for line in lines)
        )

    mocker.patch.object(cplusplus, "exec_command", side_effect=run)
    monkeypatch.chdir(tmp_path)
    assert _include_directories("clang++", (), tmp_path) == [
        tmp_path / "include",
        frameworks,
    ]
