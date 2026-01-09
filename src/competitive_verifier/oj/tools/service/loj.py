import json
import pathlib
import platform
import posixpath
import shutil
import urllib.parse
from logging import getLogger
from typing import Optional

import requests

from competitive_verifier import config
from competitive_verifier.exec import exec_command

from .text import normpath
from .type import Problem, TestCase

logger = getLogger(__name__)


class LOJProblem(Problem):
    def __init__(self, *, problem_id: int):
        self.problem_id = problem_id

    def download_system_cases(
        self, *, headers: dict[str, str] | None = None
    ) -> list[TestCase]:
        filenames = self.get_problem()
        links = self.get_links(filenames)
        testcases: list[TestCase] = []
        for filename in filenames:
            if not filename.endswith((".out", ".ans")):
                continue
            base_name = filename[:-4]
            out_url = links.get(filename)
            out_filename = base_name + ".out"
            in_url = links.get(out_filename)
            if in_url and out_url:
                resp_in = requests.get(in_url, headers=headers, timeout=10)
                resp_in.raise_for_status()
                resp_out = requests.get(out_url, headers=headers, timeout=10)
                resp_out.raise_for_status()
                testcases.append(
                    TestCase(
                        base_name,
                        filename,
                        resp_in.content,
                        out_filename,
                        resp_out.content,
                    )
                )
        spj_filenames = [fname for fname in filenames if fname.startswith("spj_")]
        if spj_filenames:
            fname = spj_filenames[0]
            # Currently only to support C/C++ checker.
            if not fname.endswith((".cpp", ".cc", ".c")):
                logger.warning("Unsupported special judge file: %s", fname)
                return testcases
            self.compile_checker(fname)
            # Fetch and save special judge file if needed.
            spj_url = links.get(fname)
            if spj_url is None:
                return testcases
            resp_spj = requests.get(spj_url, headers=headers, timeout=10)
            resp_spj.raise_for_status()
            with (self.get_checker_cache_path() / fname).open("wb") as f:
                f.write(resp_spj.content)
            if "testlib.h" in resp_spj.text:
                self.compile_checker(fname)
        return testcases

    def get_url(self) -> str:
        return f"https://loj.ac/p/{self.problem_id}"

    @classmethod
    def get_checker_cache_path(cls) -> pathlib.Path:
        return config.get_cache_dir() / "loj-checkers"

    def get_problem(self) -> list[str]:
        # List files attached to the problem.
        problem_resp = requests.post(
            "https://api.loj.ac/api/problem/getProblem",
            {
                "displayId": self.problem_id,
                "testData": True,
                "additionalFiles": False,
                "permissionOfCurrentUser": True,
            },
            timeout=10,
        )
        problem_resp.raise_for_status()
        problem_files = json.loads(problem_resp.text)
        filenames: list[str] = []
        for file in problem_files["testData"]:
            filename = file["filename"]
            if filename.endswith((".in", ".out", ".ans")):
                filenames.append(filename)

        # Check if problem needs special judge.
        # Reference: https://github.com/LibreOJ/backend/blob/master/src/migration/migrations/problem.ts#L299
        spj_filenames = [fname for fname in filenames if fname.startswith("spj_")]
        if spj_filenames:
            filenames.append(spj_filenames[0])
        return filenames

    def get_links(self, filenames: list[str]) -> dict[str, str]:
        # Get links of files via the API.
        files_resp = requests.post(
            "https://api.loj.ac/api/problem/downloadProblemFiles",
            {
                "problemId": self.problem_id,
                "type": "TestData",
                "filenameList": filenames,
            },
            timeout=10,
        )
        files_resp.raise_for_status()
        files_data = json.loads(files_resp.text)["downloadInfo"]

        links: dict[str, str] = {}
        for file_info in files_data:
            filename = file_info["filename"]
            download_url = file_info["downloadUrl"]
            links[filename] = download_url
        return links

    def compile_checker(self, fname: str) -> None:
        # Get latest testlib from GitHub.
        # Reference: https://raw.githubusercontent.com/MikeMirzayanov/testlib/refs/heads/master/testlib.h
        # Reference: https://github.com/LibreOJ/backend/blob/master/src/migration/migrations/problem.ts#L382
        testlib_resp = requests.get(
            "https://raw.githubusercontent.com/MikeMirzayanov/testlib/refs/heads/master/testlib.h",
            timeout=10,
        )
        testlib_resp.raise_for_status()
        with (self.get_checker_cache_path() / "testlib.h").open("wb") as f:
            f.write(testlib_resp.content)

        # Compile the checker.
        compiler = shutil.which("g++") or shutil.which("clang++")
        if compiler:
            checker_exe = "checker.exe" if platform.system() == "Windows" else "checker"
            checker_path = self.get_checker_cache_path() / checker_exe
            source_path = self.get_checker_cache_path() / fname
            cmd = [
                compiler,
                "-O2",
                "-I",
                str(self.get_checker_cache_path()),
                "-o",
                str(checker_path),
                str(source_path),
            ]
            logger.info("Compiling checker: %s", cmd)
            exec_command(cmd, check=True)
        else:
            logger.warning(
                "No C++ compiler found (g++ or clang++). Checker compilation skipped."
            )

    @classmethod
    def from_url(cls, url: str) -> Optional["LOJProblem"]:
        # example: https://loj.ac/p/2
        result = urllib.parse.urlparse(url)
        dirname, basename = posixpath.split(normpath(result.path))
        if result.scheme in ("", "http", "https") and result.netloc == "loj.ac":
            try:
                n = int(basename)
            except ValueError:
                pass
            else:
                if dirname == "/p":
                    return cls(problem_id=n)
        return None
