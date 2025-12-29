import json
import re
import urllib.parse
from logging import getLogger
from typing import Optional

import requests

from .text import normpath
from .type import Problem, TestCase

logger = getLogger(__name__)


class AOJProblem(Problem):
    def __init__(self, *, problem_id: str):
        self.problem_id = problem_id

    def download_system_cases(
        self, *, headers: dict[str, str] | None = None
    ) -> list[TestCase]:
        # get header
        # reference: http://developers.u-aizu.ac.jp/api?key=judgedat%2Ftestcases%2F%7BproblemId%7D%2Fheader_GET
        url = f"https://judgedat.u-aizu.ac.jp/testcases/{self.problem_id}/header"
        resp = requests.get(url, headers=headers, allow_redirects=True, timeout=10)
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

    def get_url(self) -> str:
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

    def download_system_cases(
        self, *, headers: dict[str, str] | None = None
    ) -> list[TestCase]:
        return AOJProblem(problem_id=self.get_problem_id()).download_system_cases(
            headers=headers
        )

    def get_url(self) -> str:
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
