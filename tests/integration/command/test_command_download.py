import os
import pathlib
import shutil
import subprocess

import pytest
from pytest_mock import MockerFixture

from competitive_verifier import oj
from competitive_verifier.models.problem import TestCaseFile as Case
from competitive_verifier.oj.problem import LibraryCheckerProblem, problem_from_url

from .types import FilePaths


@pytest.fixture(scope="session")
def clean_download_dir(file_paths: FilePaths) -> pathlib.Path:
    d = file_paths.dest_root / "download"

    if d.exists():  # pragma: no cover
        shutil.rmtree(d)

    return d


@pytest.fixture
def download_config_dir(
    mocker: MockerFixture,
    request: pytest.FixtureRequest,
    clean_download_dir: pathlib.Path,
) -> pathlib.Path:
    func_name: str = request.function.__name__
    assert func_name.startswith("test_")
    d = clean_download_dir / func_name[len("test_") :]

    mocker.patch.dict(
        os.environ,
        {"COMPETITIVE_VERIFY_CONFIG_PATH": d.as_posix()},
    )
    return d


@pytest.mark.usefixtures("additional_path")
@pytest.mark.order(-1)
class TestCommandDownload:
    @pytest.mark.integration
    @pytest.mark.skipif(
        not bool(shutil.which("g++") or os.getenv("CXX")),
        reason="g++ is not found",
    )
    def test_library_checker(self, download_config_dir: pathlib.Path):
        url = "https://judge.yosupo.jp/problem/aplusb"

        problem = problem_from_url(url)
        assert problem is not None
        assert isinstance(problem, LibraryCheckerProblem)

        problem_path = problem.problem_directory
        assert download_config_dir.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(download_config_dir)
        oj.download(url)
        assert problem_path.exists()

        testcases = list(problem.iter_system_cases())
        assert testcases == [
            Case(
                name=name,
                input_path=problem.source_directory / f"in/{name}.in",
                output_path=problem.source_directory / f"out/{name}.out",
            )
            for name in [
                "example_00",
                "example_01",
                "random_00",
                "random_01",
                "random_02",
                "random_03",
                "random_04",
                "random_05",
                "random_06",
                "random_07",
                "random_08",
                "random_09",
            ]
        ]

        expected_outputs = {
            "example_00": b"6912\n",
            "example_01": b"2000000000\n",
            "random_00": b"348927966\n",
            "random_01": b"385703343\n",
            "random_02": b"1133946337\n",
            "random_03": b"1132392878\n",
            "random_04": b"1144896831\n",
            "random_05": b"393933893\n",
            "random_06": b"899846272\n",
            "random_07": b"507618092\n",
            "random_08": b"340723397\n",
            "random_09": b"1198300249\n",
        }

        assert {
            t.name: t.output_path.read_bytes() for t in testcases
        } == expected_outputs

        for t in testcases:
            checker = problem.checker
            assert (
                subprocess.run(
                    [
                        str(checker),
                        str(t.input_path),
                        str(t.output_path),
                        str(t.output_path),
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
    def test_yukicoder(self, url: str, download_config_dir: pathlib.Path):
        problem = problem_from_url(url)
        assert problem is not None

        problem_path = problem.problem_directory
        assert download_config_dir.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(download_config_dir)

        oj.download(url)

        testcases = list(problem.iter_system_cases())
        assert testcases == [
            Case(
                name=name,
                input_path=problem_path / f"test/{name}.in",
                output_path=problem_path / f"test/{name}.out",
            )
            for name in [
                "01_sample_01",
                "01_sample_02",
                "input1",
                "input10",
                "input2",
                "input3",
                "input4",
                "input5",
                "input6",
                "input7",
                "input8",
                "input9",
            ]
        ]

        expected_outputs = {
            "input1": b"103\n",
            "input2": b"112\n",
            "input3": b"74\n",
            "input4": b"45\n",
            "input5": b"96\n",
            "input6": b"129\n",
            "input7": b"65\n",
            "input8": b"92\n",
            "input9": b"65\n",
            "input10": b"130\n",
            "01_sample_01": b"46\n",
            "01_sample_02": b"72\n",
        }
        assert {
            t.name: t.output_path.read_bytes() for t in testcases
        } == expected_outputs

    @pytest.mark.integration
    @pytest.mark.parametrize(
        "url",
        [
            "https://onlinejudge.u-aizu.ac.jp/courses/lesson/2/ITP1/1/ITP1_1_A",
            "https://onlinejudge.u-aizu.ac.jp/problems/ITP1_1_A",
            "https://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=ITP1_1_A&lang=jp",
        ],
    )
    def test_aizu_onlinejudge(self, url: str, download_config_dir: pathlib.Path):
        problem = problem_from_url(url)
        assert problem is not None

        problem_path = problem.problem_directory
        assert download_config_dir.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(download_config_dir)

        oj.download(url)

        testcases = list(problem.iter_system_cases())
        assert testcases == [
            Case(
                name="judge_data",
                input_path=problem_path / "test/judge_data.in",
                output_path=problem_path / "test/judge_data.out",
            )
        ]

        expected_outputs = {"judge_data": b"Hello World\n"}
        assert {
            t.name: t.output_path.read_bytes() for t in testcases
        } == expected_outputs

    @pytest.mark.integration
    def test_aizu_onlinejudge_arena(self, download_config_dir: pathlib.Path):
        url = "https://onlinejudge.u-aizu.ac.jp/services/room.html#RitsCamp19Day2/problems/A"

        problem = problem_from_url(url)
        assert problem is not None

        problem_path = problem.problem_directory
        assert download_config_dir.absolute().is_relative_to(pathlib.Path.cwd())
        assert problem_path.is_relative_to(download_config_dir)

        oj.download(url)

        testcases = list(problem.iter_system_cases())
        assert testcases == [
            Case(
                name=name,
                input_path=problem_path / f"test/{name}.in",
                output_path=problem_path / f"test/{name}.out",
            )
            for name in [
                "00_sample_01",
                "00_sample_02",
                "01_random_01",
                "01_random_02",
                "01_random_03",
                "01_random_04",
                "01_random_05",
                "01_random_06",
                "01_random_07",
                "01_random_08",
                "01_random_09",
                "01_random_10",
                "01_random_11",
                "01_random_12",
                "01_random_13",
                "01_random_14",
                "01_random_15",
                "01_random_16",
                "01_random_17",
                "01_random_18",
                "01_random_19",
                "01_random_20",
            ]
        ]

        expected_outputs = {
            "00_sample_01": b"A\n",
            "00_sample_02": b"C\n",
            "01_random_01": b"B\n",
            "01_random_02": b"A\n",
            "01_random_03": b"C\n",
            "01_random_04": b"C\n",
            "01_random_05": b"B\n",
            "01_random_06": b"A\n",
            "01_random_07": b"C\n",
            "01_random_08": b"C\n",
            "01_random_09": b"A\n",
            "01_random_10": b"B\n",
            "01_random_11": b"C\n",
            "01_random_12": b"B\n",
            "01_random_13": b"A\n",
            "01_random_14": b"C\n",
            "01_random_15": b"A\n",
            "01_random_16": b"A\n",
            "01_random_17": b"C\n",
            "01_random_18": b"A\n",
            "01_random_19": b"C\n",
            "01_random_20": b"C\n",
        }
        assert {
            t.name: t.output_path.read_bytes() for t in testcases
        } == expected_outputs
