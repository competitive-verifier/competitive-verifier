# Python Version: 3.x
# -*- coding: utf-8 -*-
"""
the module for yukicoder (https://yukicoder.me/)

:note: There is the official API https://petstore.swagger.io/?url=https://yukicoder.me/api/swagger.yaml
"""

import json
import posixpath
import string
import urllib.parse
import urllib3
from logging import getLogger
from typing import *
import onlinejudge.implementation.testcase_zipper
import onlinejudge.implementation.utils as utils
import onlinejudge.dispatch
from onlinejudge.type import *

logger = getLogger(__name__)


class YukicoderProblem(onlinejudge.type.Problem):
    def __init__(self, *, problem_no=None, problem_id=None):
        assert problem_no or problem_id
        assert not problem_no or isinstance(problem_no, int)
        assert not problem_id or isinstance(problem_id, int)
        self.problem_no = problem_no
        self.problem_id = problem_id

    def download_system_cases(self, *, session: Optional[requests.Session] = None) -> List[TestCase]:
        """
        :raises NotLoggedInError:
        """

        session = session or utils.get_default_session()
        if not self._is_logged_in(session=session):
            raise NotLoggedInError
        url = '{}/testcase.zip'.format(self.get_url())
        resp = utils.request('GET', url, session=session)
        fmt = 'test_%e/%s'
        return onlinejudge.implementation.testcase_zipper.extract_from_zip(resp.content, fmt, ignore_unmatched_samples=True)  # NOTE: yukicoder's test sets sometimes contain garbages. The owner insists that this is an intended behavior, so we need to ignore them.

    def get_url(self) -> str:
        if self.problem_no:
            return 'https://yukicoder.me/problems/no/{}'.format(self.problem_no)
        elif self.problem_id:
            return 'https://yukicoder.me/problems/{}'.format(self.problem_id)
        else:
            raise ValueError

    @classmethod
    def from_url(cls, url: str) -> Optional['YukicoderProblem']:
        # example: https://yukicoder.me/problems/no/499
        # example: http://yukicoder.me/problems/1476
        result = urllib.parse.urlparse(url)
        dirname, basename = posixpath.split(utils.normpath(result.path))
        if result.scheme in ('', 'http', 'https') \
                and result.netloc == 'yukicoder.me':
            n = None  # type: Optional[int]
            try:
                n = int(basename)
            except ValueError:
                pass
            if n is not None:
                if dirname == '/problems/no':
                    return cls(problem_no=n)
                if dirname == '/problems':
                    return cls(problem_id=n)
        return None

    def _is_logged_in(self, *, session: Optional[requests.Session] = None) -> bool:
        session = session or utils.get_default_session()
        url = 'https://yukicoder.me'
        resp = utils.request('GET', url, session=session)
        assert resp.status_code == 200
        return 'login-btn' not in str(resp.content)



onlinejudge.dispatch.problems += [YukicoderProblem]
