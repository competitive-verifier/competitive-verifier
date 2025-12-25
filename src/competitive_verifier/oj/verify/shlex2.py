"""Port of "https://github.com/smoofra/mslex/blob/master/mslex.py"."""

import re
import shlex
import sys
from collections.abc import Generator, Iterator

cmd_meta: str = r"([\"\^\&\|\<\>\(\)\%\!])"
cmd_meta_or_space: str = r"[\s\"\^\&\|\<\>\(\)\%\!]"

cmd_meta_inside_quotes: str = r"([\"\%\!])"


def _parts(s: str, itr: Iterator[re.Match[str]]) -> Generator[str, None, None]:
    yield '"'
    for m in itr:
        _, end = m.span()
        slashes, quotes, onlyslashes, text = m.groups()
        if quotes:
            yield slashes
            yield slashes
            yield r"\"" * len(quotes)
        elif onlyslashes:
            if end == len(s):
                yield onlyslashes
                yield onlyslashes
            else:
                yield onlyslashes
        else:
            yield text
    yield '"'


def _quote_with_meta(s: str) -> str:
    if not re.search(cmd_meta_inside_quotes, s):
        m = re.search(r"\\+$", s)
        if m:
            return '"' + s + m.group() + '"'
        return f'"{s}"'
    if not re.search(r"[\s\"]", s):
        return re.sub(cmd_meta, r"^\1", s)
    return re.sub(cmd_meta, r"^\1", _msquote(s, for_cmd=False))


def _msquote(s: str, *, for_cmd: bool = True) -> str:
    """Quote a string for use as a command line argument in DOS or Windows.

    On windows, before a command line argument becomes a char* in a
    program's argv, it must be parsed by both cmd.exe, and by
    CommandLineToArgvW.

    If for_cmd is true, then this will quote the string so it will
    be parsed correctly by cmd.exe and then by CommandLineToArgvW.

    If for_cmd is false, then this will quote the string so it will
    be parsed correctly when passed directly to CommandLineToArgvW.

    For some strings there is no way to quote them so they will
    parse correctly in both situations.
    """
    if not s:
        return '""'
    if not re.search(cmd_meta_or_space, s):
        return s
    if for_cmd and re.search(cmd_meta, s):
        _quote_with_meta(s)
    i = re.finditer(r"(\\*)(\"+)|(\\+)|([^\\\"]+)", s)

    return "".join(_parts(s, i))


quote = _msquote if sys.platform == "win32" else shlex.quote
split = shlex.split


def join(args: list[str]) -> str:
    """Run `shlex or smoofra/mslex`."""
    if sys.platform == "win32":
        return " ".join(_msquote(arg) for arg in args)
    return shlex.join(args)
