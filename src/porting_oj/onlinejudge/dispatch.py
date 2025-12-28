# Python Version: 3.x
from typing import List, Optional, Type

from onlinejudge.type import Problem


problems = []  # type: List[Type['Problem']]


def problem_from_url(url: str) -> Optional[Problem]:
    """
    >>> onlinejudge.dispatch.problem_from_url("https://atcoder.jp/contests/abc077/tasks/arc084_b")
    <onlinejudge.service.atcoder.AtCoderProblem object at 0x7fa0538ead68>

    >>> onlinejudge.dispatch.problem_from_url("https://codeforces.com/contest/1012/problem/D")
    <onlinejudge.service.codeforces.CodeforcesProblem object at 0x7fa05a916710>
    """

    for cls in problems:
        problem = cls.from_url(url)
        if problem is not None:
            return problem
    return None
