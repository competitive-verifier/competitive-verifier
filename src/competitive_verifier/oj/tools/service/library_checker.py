# Python Version: 3.x
import glob
import pathlib
import re
import subprocess
import sys
import urllib.parse
from logging import getLogger
from typing import Optional

from competitive_verifier import config

from . import testcase_zipper
from .type import Problem, TestCase

logger = getLogger(__name__)


class LibraryCheckerProblem(Problem):
    def __init__(self, *, problem_id: str):
        self.problem_id = problem_id

    def download_system_cases(self) -> list[TestCase]:
        self.generate_test_cases_in_cloned_repository()
        path = self.get_problem_directory_path()
        files: list[tuple[str, bytes]] = []
        files += [(file.name, file.read_bytes()) for file in path.glob("in/*.in")]
        files += [(file.name, file.read_bytes()) for file in path.glob("out/*.out")]
        return testcase_zipper.extract_from_files(iter(files))

    def generate_test_cases_in_cloned_repository(self) -> None:
        self.update_cloned_repository()
        path = self.get_cloned_repository_path()

        problem_spec = str(self.get_problem_directory_path() / "info.toml")
        command = [sys.executable, str(path / "generate.py"), problem_spec]
        logger.info("$ %s", " ".join(command))
        try:
            subprocess.check_call(command, stdout=sys.stderr, stderr=sys.stderr)
        except subprocess.CalledProcessError:
            logger.exception(
                "the generate.py failed: check https://github.com/yosupo06/library-checker-problems/issues"
            )
            raise

    def get_problem_directory_path(self) -> pathlib.Path:
        path = self.get_cloned_repository_path()
        info_tomls = list(path.glob(f"**/{glob.escape(self.problem_id)}/info.toml"))
        if len(info_tomls) != 1:
            logger.error("the problem %s not found or broken", self.problem_id)
            raise RuntimeError
        return info_tomls[0].parent

    def get_url(self) -> str:
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
        return self.get_problem_directory_path() / "checker"

    @classmethod
    def get_cloned_repository_path(cls) -> pathlib.Path:
        return config.get_cache_dir() / "library-checker-problems"

    is_repository_updated = False

    @classmethod
    def update_cloned_repository(cls) -> None:
        if cls.is_repository_updated:
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

        cls.is_repository_updated = True
