# Python Version: 3.x
import datetime
import http.client
import http.cookiejar
import posixpath
import urllib.parse
from logging import getLogger
from typing import *

from onlinejudge.type import *
from onlinejudge.utils import *  # re-export

logger = getLogger(__name__)


# We should use this instead of posixpath.normpath
# posixpath.normpath doesn't collapse a leading duplicated slashes. see: https://stackoverflow.com/questions/7816818/why-doesnt-os-normpath-collapse-a-leading-double-slash
def normpath(path: str) -> str:
    path = posixpath.normpath(path)
    if path.startswith('//'):
        path = '/' + path.lstrip('/')
    return path


def request(method: str, url: str, session: requests.Session, raise_for_status: bool = True, **kwargs) -> requests.Response:
    """`request()` is a wrapper of the `requests` package with logging.

    There is a way to bring logs from `requests` via `urllib3`, but we don't use it, because it's not very intended feature ant not very customizable. See https://2.python-requests.org/en/master/api/#api-changes
    """

    assert method in ['GET', 'POST']
    kwargs.setdefault('allow_redirects', True)
    logger.info('network: %s: %s', method, url)
    if 'data' in kwargs:
        logger.debug('network: data: %s', repr(kwargs['data']))  # TODO: prepare a nice filter. This may contain credentials.
    resp = session.request(method, url, **kwargs)
    if resp.url != url:
        logger.info('network: redirected to: %s', resp.url)
    logger.info('network: %s %s', resp.status_code, http.client.responses[resp.status_code])  # e.g. "200 OK" or "503 Service Unavailable"
    if raise_for_status:
        resp.raise_for_status()
    return resp
