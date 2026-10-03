import functools
import pathlib
import shutil
import subprocess

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.oj.languages.cplusplus import (
    _cplusplus_list_include_directories,  # pyright: ignore[reportPrivateUsage]
    _search_dirs,  # pyright: ignore[reportPrivateUsage]
)

_compilers = [cxx for cxx in ("g++", "clang++") if shutil.which(cxx)]


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
def test_list_include_directories(
    cxx: str,
    cxx_flags: tuple[str, ...],
    expected: list[str],
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    for name in ("src", "include", "third_party", "fallback"):
        (tmp_path / name).mkdir()
    monkeypatch.chdir(tmp_path)
    dirs = _cplusplus_list_include_directories(
        CXX=pathlib.Path(cxx),
        CXXFLAGS=cxx_flags,
        cwd=pathlib.Path.cwd(),
    )
    assert sorted(dirs) == sorted((tmp_path / p).resolve() for p in expected)


@pytest.mark.integration
def test_list_include_directories_fallback(tmp_path: pathlib.Path):
    dirs = _cplusplus_list_include_directories(
        CXX=pathlib.Path("no-such-compiler"),
        CXXFLAGS=("-I", "src"),
        cwd=tmp_path,
    )
    assert dirs == []


@pytest.mark.integration
@pytest.mark.skipif(not _compilers, reason="no C++ compiler is installed")
@pytest.mark.parametrize("cxx", _compilers)
def test_list_include_directories_keeps_basedir_in_cpath(
    cxx: str,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    (tmp_path / "src").mkdir()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("CPATH", str(tmp_path))
    list_dirs = functools.partial(
        _cplusplus_list_include_directories,
        CXX=pathlib.Path(cxx),
        CXXFLAGS=("-I", "src", "-I", str(tmp_path)),
        cwd=tmp_path,
    )
    # basedir is searched by default through CPATH, so the diff drops it ...
    assert list_dirs() == [tmp_path / "src"]
    # ... unless it is kept explicitly.
    assert list_dirs(keep=(tmp_path,)) == [
        tmp_path / "src",
        tmp_path,
    ]


@pytest.mark.integration
@pytest.mark.skipif(not _compilers, reason="no C++ compiler is installed")
@pytest.mark.parametrize("cxx", _compilers)
def test_list_include_directories_depends_on_cwd(
    cxx: str,
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
):
    for project in ("a", "b"):
        (tmp_path / project / "include").mkdir(parents=True)
    results: list[list[pathlib.Path]] = []
    for project in ("a", "b"):
        monkeypatch.chdir(tmp_path / project)
        results.append(
            _cplusplus_list_include_directories(
                CXX=pathlib.Path(cxx),
                CXXFLAGS=("-I", "include"),
                cwd=pathlib.Path.cwd(),
            )
        )
    assert results == [[tmp_path / "a" / "include"], [tmp_path / "b" / "include"]]


@pytest.mark.integration
def test_search_dirs_strips_framework_annotation(
    tmp_path: pathlib.Path, mocker: MockerFixture
):
    tmp_path = tmp_path.resolve()
    frameworks = tmp_path / "sdk" / "Frameworks"
    system = tmp_path / "usr" / "include"
    stderr = f"""\
ignoring nonexistent directory
#include "..." search starts here:
 include
#include <...> search starts here:
 {frameworks} (framework directory)
 {system}
End of search list.
 ignored
"""
    mocker.patch(
        "competitive_verifier.oj.languages.cplusplus.exec_command",
        return_value=subprocess.CompletedProcess([], 0, stdout="", stderr=stderr),
    )
    assert _search_dirs(CXX=pathlib.Path("clang++"), CXXFLAGS=[], cwd=tmp_path) == [
        tmp_path / "include",
        frameworks,
        system,
    ]
