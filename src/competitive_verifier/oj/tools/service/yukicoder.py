import posixpath
import urllib.parse
from logging import getLogger
from typing import Optional

import requests

from . import testcase_zipper
from .text import normpath
from .type import NotLoggedInError, Problem, TestCase

logger = getLogger(__name__)


class YukicoderProblemNo(int):
    def __new__(cls, value: int):
        return super().__new__(cls, value)

    def __str__(self) -> str:
        return "no/" + super().__str__()


class YukicoderProblemId(int):
    def __new__(cls, value: int):
        return super().__new__(cls, value)


class YukicoderProblem(Problem):
    problem: YukicoderProblemNo | YukicoderProblemId

    def __init__(self, *, problem_no: int | None = None, problem_id: int | None = None):
        if problem_no is not None:
            self.problem = YukicoderProblemNo(problem_no)
        elif problem_id is not None:
            self.problem = YukicoderProblemId(problem_id)
        else:
            raise ValueError("Needs problem_no or problem_id")

    def download_system_cases(
        self, *, headers: dict[str, str] | None = None
    ) -> list[TestCase]:
        """Download yukicoder problem.

        Raises:
            NotLoggedInError: If the `cargo metadata` command fails
        """
        if not self._is_logged_in(headers=headers):
            raise NotLoggedInError("Required: $YUKICODER_TOKEN environment variable")
        url = f"{self.get_url()}/testcase.zip"
        resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
        fmt = "test_%e/%s"
        return testcase_zipper.extract_from_zip(
            resp.content, fmt, ignore_unmatched_samples=True
        )  # NOTE: yukicoder's test sets sometimes contain garbages. The owner insists that this is an intended behavior, so we need to ignore them.

    def get_url(self) -> str:
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
