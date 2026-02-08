import glob
import json
import os
import pathlib
import posixpath
import re
import subprocess
import sys
import urllib.parse
import zipfile
from abc import abstractmethod
from collections.abc import Iterable, Iterator
from io import BytesIO
from logging import getLogger
from typing import ClassVar, Optional

import requests

from competitive_verifier import config
from competitive_verifier.models import Problem, TestCaseData, TestCaseFile

from .file import enumerate_inouts, iter_testcases, merge_testcase_files, save_testcases

logger = getLogger(__name__)


class NotLoggedInError(RuntimeError):
    pass


class _BaseProblem(Problem):
    def iter_system_cases(self) -> Iterator[TestCaseFile]:
        return iter_testcases(directory=self.test_directory)

    def download_system_cases(self) -> Iterable[TestCaseData] | bool:
        test_directory = self.test_directory

        if test_directory.exists() and any(test_directory.iterdir()):
            logger.info("download:already exists: %s", self.url)
            return True

        self.problem_directory.mkdir(parents=True, exist_ok=True)

        samples = list(self._download_cases())

        # Check samples
        if not samples:
            logger.error("Sample not found")
            return False

        # write samples to files
        save_testcases(samples, directory=test_directory)
        return samples

    @abstractmethod
    def _download_cases(self) -> Iterable[TestCaseData]: ...


class LibraryCheckerProblem(Problem):
    checker_exe_name: ClassVar[str] = (
        "checker.exe" if sys.platform == "win32" else "checker"
    )

    def __init__(self, *, problem_id: str):
        self.problem_id = problem_id
        self._source_directory = None

    def __hash__(self) -> int:
        return hash((self.problem_id, self.repo_path))

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, LibraryCheckerProblem):
            return False
        return self.problem_id == value.problem_id and self.repo_path == value.repo_path

    @property
    def repo_path(self):
        return config.get_cache_dir() / "library-checker-problems"

    def iter_system_cases(self) -> Iterator[TestCaseFile]:
        inputs: dict[str, pathlib.Path] = {}
        outputs: dict[str, pathlib.Path] = {}
        for path in self.source_directory.glob("in/*.in"):
            inputs[path.stem] = path
        for path in self.source_directory.glob("out/*.out"):
            outputs[path.stem] = path
        return merge_testcase_files(inputs, outputs)

    def download_system_cases(self) -> bool:
        self.problem_directory.mkdir(parents=True, exist_ok=True)
        self.generate_test_cases()
        return True

    @property
    def checker(self) -> pathlib.Path | None:
        return self.source_directory / self.checker_exe_name

    def generate_test_cases(self) -> None:
        self.update_cloned_repository()
        path = self.repo_path

        spec = str(self.source_directory / "info.toml")
        command = [sys.executable, str(path / "generate.py"), spec]
        logger.info("$ %s", " ".join(command))
        try:
            subprocess.check_call(command, stdout=sys.stderr, stderr=sys.stderr)
        except subprocess.CalledProcessError:
            logger.exception(
                "the generate.py failed: check https://github.com/yosupo06/library-checker-problems/issues"
            )
            raise

    @property
    def source_directory(self):
        if self._source_directory is None:
            problem_id = self.problem_id
            info_tomls = list(
                self.repo_path.glob(f"**/{glob.escape(problem_id)}/info.toml")
            )
            if len(info_tomls) != 1:
                raise RuntimeError(f"the problem {problem_id!r} not found or broken")
            self._source_directory = info_tomls[0].parent
        return self._source_directory

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

    _is_repository_updated = False

    def update_cloned_repository(self) -> None:
        if self._is_repository_updated:
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

        path = self.repo_path
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

        self._is_repository_updated = True


class _YukicoderProblemNo(int):
    def __new__(cls, value: int):
        return super().__new__(cls, value)

    def __str__(self) -> str:
        return "no/" + super().__str__()


class _YukicoderProblemId(int):
    def __new__(cls, value: int):
        return super().__new__(cls, value)


class YukicoderProblem(_BaseProblem):
    problem: _YukicoderProblemNo | _YukicoderProblemId

    def __init__(self, *, problem_no: int | None = None, problem_id: int | None = None):
        if problem_no is not None:
            self.problem = _YukicoderProblemNo(problem_no)
        elif problem_id is not None:
            self.problem = _YukicoderProblemId(problem_id)
        else:
            raise ValueError("Needs problem_no or problem_id")

    def _download_cases(self) -> list[TestCaseData]:
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

        with zipfile.ZipFile(BytesIO(resp.content)) as fh:
            inputs: dict[str, bytes] = {}
            outputs: dict[str, bytes] = {}
            for filename in fh.namelist():
                if filename.endswith("/"):
                    continue
                file = fh.read(filename)
                path = pathlib.Path(filename)
                if filename.startswith("test_in/"):
                    inputs[path.stem] = file
                elif filename.startswith("test_out/"):
                    outputs[path.stem] = file
            return [
                TestCaseData(name=name, input_data=i, output_data=o)
                for name, i, o in enumerate_inouts(inputs, outputs)
            ]

    @property
    def url(self) -> str:
        return f"https://yukicoder.me/problems/{self.problem}"

    @classmethod
    def from_url(cls, url: str) -> Optional["YukicoderProblem"]:
        # example: https://yukicoder.me/problems/no/499
        # example: http://yukicoder.me/problems/1476
        result = urllib.parse.urlparse(url)
        dirname, basename = posixpath.split(_normpath(result.path))
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


class AOJProblem(_BaseProblem):
    def __init__(self, *, problem_id: str):
        self.problem_id = problem_id

    def _download_cases(self) -> Iterable[TestCaseData]:
        return AOJProblem.download_cases(self.problem_id)

    @staticmethod
    def download_cases(problem_id: str) -> Iterable[TestCaseData]:
        # get header
        # reference: http://developers.u-aizu.ac.jp/api?key=judgedat%2Ftestcases%2F%7BproblemId%7D%2Fheader_GET
        url = f"https://judgedat.u-aizu.ac.jp/testcases/{problem_id}/header"
        resp = requests.get(url, allow_redirects=True, timeout=10)
        resp.raise_for_status()
        header_res = json.loads(resp.text)

        # get testcases via the official API
        for header in header_res["headers"]:
            # NOTE: the endpoints are not same to http://developers.u-aizu.ac.jp/api?key=judgedat%2Ftestcases%2F%7BproblemId%7D%2F%7Bserial%7D_GET since the json API often says "..... (terminated because of the limitation)"
            # NOTE: even when using https://judgedat.u-aizu.ac.jp/testcases/PROBLEM_ID/SERIAL, there is the 1G limit (see https://twitter.com/beet_aizu/status/1194947611100188672)
            serial = header["serial"]
            url = f"https://judgedat.u-aizu.ac.jp/testcases/{problem_id}/{serial}"

            resp_in = requests.get(url + "/in", allow_redirects=True, timeout=10)
            resp_in.raise_for_status()
            resp_out = requests.get(url + "/out", allow_redirects=True, timeout=10)
            resp_out.raise_for_status()

            yield TestCaseData(
                header["name"],
                resp_in.content,
                resp_out.content,
            )

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
            and _normpath(result.path) == "/onlinejudge/description.jsp"
            and querystring.get("id")
            and len(querystring["id"]) == 1
        ):
            (n,) = querystring["id"]
            return cls(problem_id=n)

        # example: https://onlinejudge.u-aizu.ac.jp/challenges/sources/JAG/Prelim/2881
        # example: https://onlinejudge.u-aizu.ac.jp/courses/library/4/CGL/3/CGL_3_B
        m = re.match(
            r"^/(challenges|courses)/(sources|library/\d+|lesson/\d+)/(\w+)/(\w+)/(\w+)$",
            _normpath(result.path),
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
        m = re.match(r"^/problems/(\w+)$", _normpath(result.path))
        if (
            result.scheme in ("", "http", "https")
            and result.netloc == "onlinejudge.u-aizu.ac.jp"
            and m
        ):
            n = m.group(1)
            return cls(problem_id=n)

        return None


class AOJArenaProblem(_BaseProblem):
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

    def _download_cases(self) -> Iterable[TestCaseData]:
        return AOJProblem.download_cases(self.get_problem_id())

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
            and _normpath(result.path) == "/services/room.html"
        ):
            fragment = result.fragment.split("/")
            if len(fragment) == 3 and fragment[1] == "problems":  # noqa: PLR2004
                return cls(arena_id=fragment[0], alphabet=fragment[2].upper())
        return None


def _normpath(path: str) -> str:
    """A wrapper of posixpath.normpath.

    posixpath.normpath doesn't collapse a leading duplicated slashes.
    """
    path = posixpath.normpath(path)
    if path.startswith("//"):
        path = "/" + path.lstrip("/")
    return path


def _subclasses_recursive(cls: type[Problem]) -> Iterable[type[Problem]]:
    yield from (children := cls.__subclasses__())
    for ch in children:
        yield from _subclasses_recursive(ch)


def problem_from_url(url: str) -> Problem | None:
    for ch in set(_subclasses_recursive(Problem)):
        if (problem := ch.from_url(url)) is not None:
            return problem
    return None
