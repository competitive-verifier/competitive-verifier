# Python Version: 3.x
"""
the module containing base types

:note: Some methods are not implemented in subclasses.
    Please check the definitions of subclasses under :py:mod:`onlinejudge.service`.
"""

import datetime
from abc import ABC, abstractmethod
from typing import Callable, Iterator, List, NamedTuple, NewType, Optional, Sequence, Tuple

import requests


class LoginError(RuntimeError):
    def __init__(self, message: str = 'failed to login'):
        super().__init__(message)


class TestCase(NamedTuple):
    name: str
    input_name: str
    input_data: bytes
    output_name: str
    output_data: bytes

LanguageId = NewType('LanguageId', str)
class Language(NamedTuple):
    id: LanguageId
    name: str


class NotLoggedInError(RuntimeError):
    def __init__(self, message: str = 'login required'):
        super().__init__(message)


class SampleParseError(RuntimeError):
    def __init__(self, message: str = 'failed to parse samples'):
        super().__init__(message)


class Problem(ABC):
    """
    :note: :py:class:`Problem` represents just a URL of a problem, without the data of the problem.
           :py:class:`Problem` はちょうど問題の URL のみを表現します。キャッシュや内部状態は持ちません。
    """
    def download_system_cases(self, *, session: Optional[requests.Session] = None) -> List[TestCase]:
        """
        :raises NotLoggedInError:
        """
        raise NotImplementedError

    @abstractmethod
    def get_url(self) -> str:
        raise NotImplementedError

    def __repr__(self) -> str:
        return '{}.from_url({})'.format(self.__class__.__name__, repr(self.get_url()))

    def __eq__(self, other) -> bool:
        return self.__class__ == other.__class__ and self.get_url() == other.get_url()

    @classmethod
    @abstractmethod
    def from_url(cls, url: str) -> Optional['Problem']:
        pass
