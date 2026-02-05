import glob
import json
import os
import pathlib
import posixpath
import re
import shutil
import subprocess
import sys
import urllib.parse
from itertools import chain
from logging import getLogger
from typing import ClassVar, Optional

import requests

from competitive_verifier import config
from competitive_verifier.models import Problem, TestCase

from . import testcase_zipper

logger = getLogger(__name__)


class NotLoggedInError(RuntimeError):
    pass


class LibraryCheckerProblem(Problem):
    checker_exe_name: ClassVar[str] = (
        "checker.exe" if sys.platform == "win32" else "checker"
    )

    def __init__(self, *, problem_id: str):
        self.problem_id = problem_id

    def download_system_cases(self) -> bool:
        self.generate_test_cases_in_cloned_repository()
        path = self.get_source_directory()

        for file in chain(path.glob("in/*.in"), path.glob("out/*.out")):
            dst = self.problem_directory / "test" / file.name
            if dst.exists():
                logger.error(
                    "Failed to download since file already exists: %s", str(dst)
                )
                return False
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(file, dst)

        checker_path = self.get_source_checker_path()
        if checker_path and checker_path.exists():
            try:
                shutil.move(checker_path, self.problem_directory)
            except Exception:
                logger.exception("Failed to copy checker")
                shutil.rmtree(self.problem_directory)
                return False
        return True

    def get_source_checker_path(self) -> pathlib.Path | None:
        path = self.get_source_directory()
        return path / self.checker_exe_name

    @property
    def checker(self) -> pathlib.Path | None:
        return self.problem_directory / self.checker_exe_name

    def generate_test_cases_in_cloned_repository(self) -> None:
        self.update_cloned_repository()
        path = self.get_cloned_repository_path()

        spec = str(self.get_source_directory() / "info.toml")
        command = [sys.executable, str(path / "generate.py"), spec]
        logger.info("$ %s", " ".join(command))
        try:
            subprocess.check_call(command, stdout=sys.stderr, stderr=sys.stderr)
        except subprocess.CalledProcessError:
            logger.exception(
                "the generate.py failed: check https://github.com/yosupo06/library-checker-problems/issues"
            )
            raise

    def get_source_directory(self) -> pathlib.Path:
        path = self.get_cloned_repository_path()
        info_tomls = list(path.glob(f"**/{glob.escape(self.problem_id)}/info.toml"))
        if len(info_tomls) != 1:
            logger.error("the problem %s not found or broken", self.problem_id)
            raise RuntimeError
        return info_tomls[0].parent

    @property
    def url(self) -> str:
        return f"https://judge.yosupo.jp/problem/{self.problem_id}"

    @classmethod
    def from_url(cls, url: str) -> Optional["LibraryCheckerProblem"]:
        # example: https://judge.yosupo.jp/problem/unionfind
        result = urllib.parse.urlparse(url)
        if result.scheme in ("", "http", "https") and result.netloc in (
            "judge.yosupo.jp",
            "old.yosupo.jp",
        ):
            m = re.match(r"/problem/(\w+)/?", result.path)
            if m:
                return cls(problem_id=m.group(1))
        return None

    def download_checker_binary(self) -> pathlib.Path:
        self.generate_test_cases_in_cloned_repository()
        return self.get_source_directory() / "checker"

    @classmethod
    def get_cloned_repository_path(cls) -> pathlib.Path:
        return config.get_cache_dir() / "library-checker-problems"

    _is_repository_updated = False

    @classmethod
    def update_cloned_repository(cls) -> None:
        if cls._is_repository_updated:
            return

        try:
            subprocess.check_call(
                ["git", "--version"],  # noqa: S607
                stdout=sys.stderr,
                stderr=sys.stderr,
            )
        except FileNotFoundError:
            logger.exception("git command not found")
            raise

        path = cls.get_cloned_repository_path()
        if not path.exists():
            # init the problem repository
            url = "https://github.com/yosupo06/library-checker-problems"
            logger.info("$ git clone %s %s", url, path)
            subprocess.check_call(
                ["git", "clone", url, str(path)],  # noqa: S607
                stdout=sys.stderr,
                stderr=sys.stderr,
            )
        else:
            # sync the problem repository
            logger.info("$ git -C %s pull", str(path))
            subprocess.check_call(
                ["git", "-C", str(path), "pull"],  # noqa: S607
                stdout=sys.stderr,
                stderr=sys.stderr,
            )

        cls._is_repository_updated = True


class _YukicoderProblemNo(int):
    def __new__(cls, value: int):
        return super().__new__(cls, value)

    def __str__(self) -> str:
        return "no/" + super().__str__()


class _YukicoderProblemId(int):
    def __new__(cls, value: int):
        return super().__new__(cls, value)


class YukicoderProblem(Problem):
    problem: _YukicoderProblemNo | _YukicoderProblemId

    def __init__(self, *, problem_no: int | None = None, problem_id: int | None = None):
        if problem_no is not None:
            self.problem = _YukicoderProblemNo(problem_no)
        elif problem_id is not None:
            self.problem = _YukicoderProblemId(problem_id)
        else:
            raise ValueError("Needs problem_no or problem_id")

    def download_system_cases(self) -> list[TestCase]:
        """Download yukicoder problem.

        Raises:
            NotLoggedInError: If the `cargo metadata` command fails
        """
        headers: dict[str, str] | None = None
        if yukicoder_token := os.environ.get("YUKICODER_TOKEN"):
            headers = {"Authorization": f"Bearer {yukicoder_token}"}

        if not self._is_logged_in(headers=headers):
            raise NotLoggedInError("Required: $YUKICODER_TOKEN environment variable")
        url = f"{self.url}/testcase.zip"
        resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        fmt = "test_%e/%s"
        return testcase_zipper.extract_from_zip(
            resp.content, fmt, ignore_unmatched_samples=True
        )  # NOTE: yukicoder's test sets sometimes contain garbages. The owner insists that this is an intended behavior, so we need to ignore them.

    @property
    def url(self) -> str:
        return f"https://yukicoder.me/problems/{self.problem}"

    @classmethod
    def from_url(cls, url: str) -> Optional["YukicoderProblem"]:
        # example: https://yukicoder.me/problems/no/499
        # example: http://yukicoder.me/problems/1476
        result = urllib.parse.urlparse(url)
        dirname, basename = posixpath.split(normpath(result.path))
        if result.scheme in ("", "http", "https") and result.netloc == "yukicoder.me":
            try:
                n = int(basename)
            except ValueError:
                pass
            else:
                if dirname == "/problems/no":
                    return cls(problem_no=n)
                if dirname == "/problems":
                    return cls(problem_id=n)
        return None

    def _is_logged_in(self, *, headers: dict[str, str] | None = None) -> bool:
        url = "https://yukicoder.me"
        resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        resp.raise_for_status()
        return "login-btn" not in str(resp.content)


class AOJProblem(Problem):
    def __init__(self, *, problem_id: str):
        self.problem_id = problem_id

    def download_system_cases(self) -> list[TestCase]:
        # get header
        # reference: http://developers.u-aizu.ac.jp/api?key=judgedat%2Ftestcases%2F%7BproblemId%7D%2Fheader_GET
        url = f"https://judgedat.u-aizu.ac.jp/testcases/{self.problem_id}/header"
        resp = requests.get(url, allow_redirects=True, timeout=10)
        resp.raise_for_status()
        header_res = json.loads(resp.text)

        # get testcases via the official API
        testcases: list[TestCase] = []
        for header in header_res["headers"]:
            # NOTE: the endpoints are not same to http://developers.u-aizu.ac.jp/api?key=judgedat%2Ftestcases%2F%7BproblemId%7D%2F%7Bserial%7D_GET since the json API often says "..... (terminated because of the limitation)"
            # NOTE: even when using https://judgedat.u-aizu.ac.jp/testcases/PROBLEM_ID/SERIAL, there is the 1G limit (see https://twitter.com/beet_aizu/status/1194947611100188672)
            serial = header["serial"]
            url = f"https://judgedat.u-aizu.ac.jp/testcases/{self.problem_id}/{serial}"

            resp_in = requests.get(url + "/in", allow_redirects=True, timeout=10)
            resp_in.raise_for_status()
            resp_out = requests.get(url + "/out", allow_redirects=True, timeout=10)
            resp_out.raise_for_status()

            testcases += [
                TestCase(
                    header["name"],
                    header["name"],
                    resp_in.content,
                    header["name"],
                    resp_out.content,
                )
            ]
        return testcases

    @property
    def url(self) -> str:
        return f"http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id={self.problem_id}"

    @classmethod
    def from_url(cls, url: str) -> Optional["AOJProblem"]:
        result = urllib.parse.urlparse(url)

        # example: http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=1169
        # example: http://judge.u-aizu.ac.jp/onlinejudge/description.jsp?id=DSL_1_A&lang=jp
        querystring = urllib.parse.parse_qs(result.query)
        if (
            result.scheme in ("", "http", "https")
            and result.netloc == "judge.u-aizu.ac.jp"
            and normpath(result.path) == "/onlinejudge/description.jsp"
            and querystring.get("id")
            and len(querystring["id"]) == 1
        ):
            (n,) = querystring["id"]
            return cls(problem_id=n)

        # example: https://onlinejudge.u-aizu.ac.jp/challenges/sources/JAG/Prelim/2881
        # example: https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/3/CGL_3_B
        m = re.match(
            r"^/(challenges|courses)/(sources|library/\d+|lesson/\d+)/(\w+)/(\w+)/(\w+)$",
            normpath(result.path),
        )
        if (
            result.scheme in ("", "http", "https")
            and result.netloc == "onlinejudge.u-aizu.ac.jp"
            and m
        ):
            n = m.group(5)
            return cls(problem_id=n)

        # example: https://onlinejudge.u-aizu.ac.jp/problems/0423
        # example: https://onlinejudge.u-aizu.ac.jp/problems/CGL_3_B
        m = re.match(r"^/problems/(\w+)$", normpath(result.path))
        if (
            result.scheme in ("", "http", "https")
            and result.netloc == "onlinejudge.u-aizu.ac.jp"
            and m
        ):
            n = m.group(1)
            return cls(problem_id=n)

        return None


class AOJArenaProblem(Problem):
    def __init__(self, *, arena_id: str, alphabet: str):
        if len(alphabet) != 1 or not alphabet.isupper():
            raise ValueError(arena_id, alphabet)
        self.arena_id = arena_id
        self.alphabet = alphabet

        self._problem_id: str | None = None

    def get_problem_id(self) -> str:
        if self._problem_id is None:
            url = f"https://judgeapi.u-aizu.ac.jp/arenas/{self.arena_id}/problems"
            resp = requests.get(url, allow_redirects=True, timeout=10)
            resp.raise_for_status()
            problems = json.loads(resp.text)
            for problem in problems:
                if problem["id"] == self.alphabet:
                    p = problem["problemId"]
                    logger.debug("problem: %s", p)
                    self._problem_id = p
                    return p
            raise ValueError("Problem is not found.")
        return self._problem_id

    def download_system_cases(self) -> list[TestCase]:
        return AOJProblem(problem_id=self.get_problem_id()).download_system_cases()

    @property
    def url(self) -> str:
        return f"https://onlinejudge.u-aizu.ac.jp/services/room.html#{self.arena_id}/problems/{self.alphabet}"

    @classmethod
    def from_url(cls, url: str) -> Optional["AOJArenaProblem"]:
        # example: https://onlinejudge.u-aizu.ac.jp/services/room.html#RitsCamp19Day2/problems/A
        result = urllib.parse.urlparse(url)
        if (
            result.scheme in ("", "http", "https")
            and result.netloc == "onlinejudge.u-aizu.ac.jp"
            and normpath(result.path) == "/services/room.html"
        ):
            fragment = result.fragment.split("/")
            if len(fragment) == 3 and fragment[1] == "problems":  # noqa: PLR2004
                return cls(arena_id=fragment[0], alphabet=fragment[2].upper())
        return None


def normpath(path: str) -> str:
    """A wrapper of posixpath.normpath.

    posixpath.normpath doesn't collapse a leading duplicated slashes.
    """
    path = posixpath.normpath(path)
    if path.startswith("//"):
        path = "/" + path.lstrip("/")
    return path
