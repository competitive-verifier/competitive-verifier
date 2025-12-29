import os
import pathlib
import shutil
import subprocess

import pytest

from competitive_verifier import oj

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
        promlem_path = oj.get_directory(url)
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert promlem_path.is_relative_to(dst_path)
        oj.download(url)
        checker = promlem_path / "checker"
        outputs = list(promlem_path.glob("test/*.out"))
        assert outputs
        for out_path in outputs:
            in_path = out_path.with_suffix(".in")
            assert in_path.exists()
            assert (
                subprocess.run(
                    [
                        checker.as_posix(),
                        in_path.as_posix(),
                        out_path.as_posix(),
                        out_path.as_posix(),
                    ],
                    check=False,
                ).returncode
                == 0
            )

    @pytest.mark.integration
    @pytest.mark.skipif(
        not bool(os.getenv("YUKICODER_TOKEN")),
        reason="$YUKICODER_TOKEN is not found",
    )
    @pytest.mark.parametrize(
        "url",
        ["https://yukicoder.me/problems/4573", "https://yukicoder.me/problems/no/1088"],
    )
    def test_yukicoder(self, url: str, set_config_dir: ConfigDirSetter):
        dst_path = set_config_dir("download/yukicoder")

        promlem_path = oj.get_directory(url)
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert promlem_path.is_relative_to(dst_path)

        oj.download(url)

        outputs = list(promlem_path.glob("test/*.out"))
        assert {p.stem: p.read_bytes().strip() for p in outputs} == {
            "input1": b"103",
            "input2": b"112",
            "input3": b"74",
            "input4": b"45",
            "input5": b"96",
            "input6": b"129",
            "input7": b"65",
            "input8": b"92",
            "input9": b"65",
            "input10": b"130",
            "01_sample_01": b"46",
            "01_sample_02": b"72",
        }
        for out_path in outputs:
            in_path = out_path.with_suffix(".in")
            assert in_path.exists()

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "url",
        [
            "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
            "https://onlinejudge.u-aizu.ac.jp/problems/ITP1_1_A",
            "https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A&lang=jp",
        ],
    )
    def test_aizu_onlinejudge(self, url: str, set_config_dir: ConfigDirSetter):
        dst_path = set_config_dir("download/aoj")

        promlem_path = oj.get_directory(url)
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert promlem_path.is_relative_to(dst_path)

        oj.download(url)

        outputs = list(promlem_path.glob("test/*.out"))
        assert {p.stem: p.read_bytes().strip() for p in outputs} == {
            "judge_data": b"Hello World",
        }
        for out_path in outputs:
            in_path = out_path.with_suffix(".in")
            assert in_path.exists()

    @pytest.mark.integration
    def test_aizu_onlinejudge_arena(self, set_config_dir: ConfigDirSetter):
        url = "https://onlinejudge.u-aizu.ac.jp/services/room.html#RitsCamp19Day2/problems/A"
        dst_path = set_config_dir("download/aoj")

        promlem_path = oj.get_directory(url)
        assert dst_path.absolute().is_relative_to(pathlib.Path.cwd())
        assert promlem_path.is_relative_to(dst_path)

        oj.download(url)

        outputs = list(promlem_path.glob("test/*.out"))
        assert {p.stem: p.read_bytes().strip() for p in outputs} == {
            "00_sample_01": b"A",
            "00_sample_02": b"C",
            "01_random_01": b"B",
            "01_random_02": b"A",
            "01_random_03": b"C",
            "01_random_04": b"C",
            "01_random_05": b"B",
            "01_random_06": b"A",
            "01_random_07": b"C",
            "01_random_08": b"C",
            "01_random_09": b"A",
            "01_random_10": b"B",
            "01_random_11": b"C",
            "01_random_12": b"B",
            "01_random_13": b"A",
            "01_random_14": b"C",
            "01_random_15": b"A",
            "01_random_16": b"A",
            "01_random_17": b"C",
            "01_random_18": b"A",
            "01_random_19": b"C",
            "01_random_20": b"C",
        }
        for out_path in outputs:
            in_path = out_path.with_suffix(".in")
            assert in_path.exists()
