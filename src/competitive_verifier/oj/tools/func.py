import hashlib
import pathlib
import sys

from onlinejudge.service.atcoder import AtCoderService
from onlinejudge.service.library_checker import LibraryCheckerProblem
from onlinejudge.service.yukicoder import YukicoderService

from competitive_verifier import config

checker_exe_name = "checker.exe" if sys.platform == "win32" else "checker"


def get_cache_directory() -> pathlib.Path:
    return config.get_cache_dir().resolve() / "online-judge-tools"


def get_problem_cache_dir() -> pathlib.Path:
    return config.get_cache_dir() / "problems"


def get_directory(url: str) -> pathlib.Path:
    return get_problem_cache_dir() / hashlib.md5(url.encode()).hexdigest()


def is_yukicoder(url: str) -> bool:
    return YukicoderService.from_url(url) is not None


def is_atcoder(url: str) -> bool:
    return AtCoderService.from_url(url) is not None


def get_checker_problem(url: str) -> LibraryCheckerProblem | None:
    return LibraryCheckerProblem.from_url(url)


def get_checker_path(
    url_or_problem: str | LibraryCheckerProblem | None,
) -> pathlib.Path | None:
    if isinstance(url_or_problem, str):
        checker_problem = get_checker_problem(url_or_problem)
    else:
        checker_problem = url_or_problem
    if checker_problem:
        problem_dir = checker_problem.get_problem_directory_path()
        return problem_dir / checker_exe_name
