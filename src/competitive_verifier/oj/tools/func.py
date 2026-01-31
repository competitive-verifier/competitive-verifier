import hashlib
import pathlib
import sys
import urllib.parse

from competitive_verifier import config

from .problem import LibraryCheckerProblem

checker_exe_name = "checker.exe" if sys.platform == "win32" else "checker"


def get_problem_cache_dir() -> pathlib.Path:
    return config.get_cache_dir() / "problems"


def problem_directory(url: str) -> pathlib.Path:
    return (
        get_problem_cache_dir()
        / hashlib.md5(url.encode(), usedforsecurity=False).hexdigest()
    )


def is_yukicoder(url: str) -> bool:
    # example: http://yukicoder.me/
    result = urllib.parse.urlparse(url)
    return result.scheme in ("", "http", "https") and result.netloc == "yukicoder.me"


def get_checker_problem(url: str) -> LibraryCheckerProblem | None:
    return LibraryCheckerProblem.from_url(url)


def get_checker_path(
    url_or_problem: str | LibraryCheckerProblem | None,
) -> pathlib.Path | None:
    checker_problem = (
        get_checker_problem(url_or_problem)
        if isinstance(url_or_problem, str)
        else url_or_problem
    )
    if checker_problem:
        problem_dir = checker_problem.get_problem_directory_path()
        return problem_dir / checker_exe_name
    return None
