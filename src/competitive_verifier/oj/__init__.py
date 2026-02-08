from .oj_download import main as download
from .oj_test import main as test
from .problem import problem_from_url
from .resolver import OjResolve

__all__ = [
    "OjResolve",
    "download",
    "problem_from_url",
    "test",
]
