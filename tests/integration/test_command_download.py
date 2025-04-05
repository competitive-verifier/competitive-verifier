import os
import pathlib
import shutil
import subprocess

import pytest

import competitive_verifier.config as config
import competitive_verifier.oj as oj

from .types import ConfigDirSetter


@pytest.mark.usefixtures("additional_path")
@pytest.mark.order(-1)
class TestCommandDownload:
    @pytest.mark.integration
    @pytest.mark.skipif(
        not bool(shutil.which("g++") or os.getenv("CXX")),
        reason="g++ is not found",
    )
    def test_library_checker(self, set_config_dir: ConfigDirSetter):
        url = "https://judge.yosupo.jp/problem/aplusb"
        dst_path = set_config_dir("download/library_checker")
        problem_path = oj.get_directory(url)
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(dst_path)
        oj.download(url)
        checker = problem_path / "checker"
        outputs = list(problem_path.glob("test/*.out"))
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
    def test_yukicoder(self, set_config_dir: ConfigDirSetter):
        url = "https://yukicoder.me/problems/no/1088"
        dst_path = set_config_dir("download/yukicoder")

        problem_path = oj.get_directory(url)
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(dst_path)

        oj.download(url)

        outputs = list(problem_path.glob("test/*.out"))
        assert outputs
        for out_path in outputs:
            in_path = out_path.with_suffix(".out")
            assert in_path.exists()
            assert out_path.read_bytes().strip() == b"A + B"

    @pytest.mark.integration
    def test_aizu_onlinejudge(self, set_config_dir: ConfigDirSetter):
        url = "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A"
        dst_path = set_config_dir("download/aoj")

        problem_path = oj.get_directory(url)
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(dst_path)

        oj.download(url)

        outputs = list(problem_path.glob("test/*.out"))
        assert outputs
        for out_path in outputs:
            in_path = out_path.with_suffix(".out")
            assert in_path.exists()
            assert out_path.read_bytes().strip() == b"Hello World"

    @pytest.mark.integration
    def test_atcoder(self, set_config_dir: ConfigDirSetter):
        url = "https://atcoder.jp/contests/abc322/tasks/abc322_a"
        dst_path = set_config_dir("download/atcoder")
        problem_path = (
            config.get_cache_dir() / "atcoder-testcases" / "abc322" / "abc322" / "A"
        )
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(dst_path)

        oj.download(url)

        inputs = list(problem_path.glob("in/*"))
        outputs = list(problem_path.glob("out/*"))
        assert inputs
        assert outputs
