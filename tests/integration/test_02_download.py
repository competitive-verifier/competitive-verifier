import os
import pathlib
import shutil
import subprocess

import pytest

import competitive_verifier.oj as oj

from .types import ConfigDirFunc


@pytest.mark.integration
@pytest.mark.skipif(
    not bool(shutil.which("g++") or os.getenv("CXX")),
    reason="g++ is not found",
)
def test_library_checker(config_dir: ConfigDirFunc):
    url = "https://judge.yosupo.jp/problem/aplusb"
    dst_path = config_dir("download.library_checker")
    promlem_path = oj.get_directory(url)
    assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
    assert promlem_path.is_relative_to(dst_path)
    oj.download(url)
    checker = promlem_path / "checker"
    outputs = list(promlem_path.glob("test/*.out"))
    assert outputs
    for out_path in outputs:
        in_path = out_path.with_suffix(".out")
        assert in_path.exists()
        assert (
            subprocess.run(
                [
                    checker.as_posix(),
                    in_path.as_posix(),
                    out_path.as_posix(),
                    out_path.as_posix(),
                ]
            ).returncode
            == 0
        )


@pytest.mark.integration
@pytest.mark.skipif(
    not bool(os.getenv("YUKICODER_TOKEN")),
    reason="$YUKICODER_TOKEN is not found",
)
def test_yukicoder(config_dir: ConfigDirFunc):
    url = "https://yukicoder.me/problems/no/3040"
    dst_path = config_dir("download.yukicoder")

    promlem_path = oj.get_directory(url)
    assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
    assert promlem_path.is_relative_to(dst_path)

    oj.download(url)

    outputs = list(promlem_path.glob("test/*.out"))
    assert outputs
    for out_path in outputs:
        in_path = out_path.with_suffix(".out")
        assert in_path.exists()
        assert out_path.read_bytes().strip() == b"A + B"


@pytest.mark.integration
def test_aizu_onlinejudge(config_dir: ConfigDirFunc):
    url = "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
    dst_path = config_dir("download.aoj")

    promlem_path = oj.get_directory(url)
    assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
    assert promlem_path.is_relative_to(dst_path)

    oj.download(url)

    outputs = list(promlem_path.glob("test/*.out"))
    assert outputs
    for out_path in outputs:
        in_path = out_path.with_suffix(".out")
        assert in_path.exists()
        assert out_path.read_bytes().strip() == b"Hello World"
