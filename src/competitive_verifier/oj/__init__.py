from .oj_download import run_wrapper as download
from .oj_test import run_wrapper as test
from .problem import problem_from_url
from .resolver import OjResolve

__all__ = [
    "OjResolve",
    "download",
    "problem_from_url",
    "test",
]
