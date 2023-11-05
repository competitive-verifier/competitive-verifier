# Python Version: 3.x
import functools
import pathlib
import re
from logging import getLogger
from typing import Iterable, Mapping

from competitive_verifier.oj.verify.utils import read_text_normalized

logger = getLogger(__name__)


# special comments like Vim and Python: see https://www.python.org/dev/peps/pep-0263/
@functools.lru_cache(maxsize=None)
def list_special_comments(path: pathlib.Path) -> Mapping[str, str]:
    pattern = re.compile(
        r"\b(?:verify-helper|verification-helper|competitive-verifier):\s*([0-9A-Za-z_]+)(?:\s(.*))?$"
    )
    attributes: dict[str, str] = {}
    for line in read_text_normalized(path).splitlines():
        matched = pattern.search(line)
        if matched:
            key = matched.group(1)
            value = (matched.group(2) or "").strip()
            attributes[key] = value
    return attributes


@functools.lru_cache(maxsize=None)
def list_embedded_urls(path: pathlib.Path) -> Iterable[str]:
    pattern = re.compile(
        r"""['"`]?https?://\S*"""
    )  # use a broad pattern. There are no needs to make match strict.
    content = read_text_normalized(path)
    urls: list[str] = []
    for url in pattern.findall(content):
        # The URL may be written like `"https://atcoder.jp/"`. In this case, we need to remove `"`s around the URL.
        # We also need to remove trailing superfluous chars in a case like `{"url":"https://atcoder.jp/"}`.
        for quote in ("'", '"', "`"):
            if url.startswith(quote):
                end_quote_pos = url.rfind(quote)
                if end_quote_pos == 0:
                    # Remove opening quote from the URL like `"https://atcoder.jp/`
                    url = url[1:]
                else:
                    # Remove quotes and trailing superfluous chars around the URL
                    url = url[1:end_quote_pos]
                break
        urls.append(url)
    return sorted(set(urls))
