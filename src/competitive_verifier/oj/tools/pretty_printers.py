import enum
import shutil
from collections.abc import Iterable
from logging import getLogger
from typing import NamedTuple

import colorama

# ruff: noqa: S101

logger = getLogger(__name__)


class _PrettyTokenType(enum.Enum):
    BODY = "BODY"
    BODY_HIGHLIGHT_LEFT = "BODY_HIGHLIGHT_LEFT"
    BODY_HIGHLIGHT_RIGHT = "BODY_HIGHLIGHT_RIGHT"
    WHITESPACE = "WHITESPACE"
    NEWLINE = "NEWLINE"
    HINT = "HINT"


class _PrettyToken(NamedTuple):
    type: _PrettyTokenType
    value: str


def _tokenize_str(s: str) -> list[_PrettyToken]:
    tokens: list[_PrettyToken] = []
    l = 0
    while l < len(s):
        r = l + 1
        while r < len(s) and (s[l] in " \t") == (s[r] in " \t"):
            r += 1
        typ = _PrettyTokenType.WHITESPACE if s[l] in " \t" else _PrettyTokenType.BODY
        tokens.append(_PrettyToken(typ, s[l:r]))
        l = r
    return tokens


def _tokenize_line(line: str) -> list[_PrettyToken]:
    body = line.rstrip()
    newline = line[len(body) :]
    tokens: list[_PrettyToken] = []

    # add the body of line
    if body:
        tokens += _tokenize_str(body)

    # add newlines
    if newline:
        if newline in ("\n", "\r\n"):
            tokens.append(_PrettyToken(_PrettyTokenType.NEWLINE, newline))
        else:
            whitespace = newline.rstrip("\n")
            newline = newline[len(whitespace) :]
            if whitespace:
                tokens.append(_PrettyToken(_PrettyTokenType.WHITESPACE, whitespace))
            tokens.append(_PrettyToken(_PrettyTokenType.HINT, "(trailing whitespace)"))
            if newline:
                tokens.append(_PrettyToken(_PrettyTokenType.NEWLINE, newline))

    return tokens


def _decode_with_recovery(content: bytes) -> tuple[list[_PrettyToken], str]:
    tokens: list[_PrettyToken] = []
    try:
        text = content.decode()
    except UnicodeDecodeError as e:
        tokens.append(_PrettyToken(_PrettyTokenType.HINT, str(e)))
        text = content.decode(errors="replace")
    return tokens, text


def _warn_if_empty(tokens: list[_PrettyToken]) -> list[_PrettyToken]:
    if not tokens:
        return [_PrettyToken(_PrettyTokenType.HINT, "(empty)")]
    if tokens[-1][0] == _PrettyTokenType.BODY:
        tokens.append(_PrettyToken(_PrettyTokenType.HINT, "(no trailing newline)"))
    if all(token.type == _PrettyTokenType.NEWLINE for token in tokens):
        tokens.append(_PrettyToken(_PrettyTokenType.HINT, "(only newline)"))
    return tokens


def _tokenize_large_file_content(
    *, content: bytes, limit: int, head: int, tail: int, char_in_line: int
) -> list[_PrettyToken]:
    """`_tokenize_large_file_content` constructs the intermediate representations. They have no color infomation."""
    assert head + tail < limit

    def candidate_do_nothing(text: str) -> list[_PrettyToken]:
        tokens: list[_PrettyToken] = []
        for line in text.splitlines(keepends=True):
            tokens += _tokenize_line(line)
        return tokens

    def candidate_line_based(text: str) -> list[_PrettyToken]:
        lines = text.splitlines(keepends=True)
        if len(lines) < limit:
            return candidate_do_nothing(text)

        tokens: list[_PrettyToken] = []
        for line in lines[:head]:
            tokens += _tokenize_line(line)
        tokens.append(
            _PrettyToken(
                _PrettyTokenType.HINT,
                f"... ({len(lines[head:-tail])} lines) ...\n",
            )
        )
        for line in lines[-tail:]:
            tokens += _tokenize_line(line)
        return tokens

    def candidate_char_based(text: str) -> list[_PrettyToken]:
        if len(text) < char_in_line * limit:
            return candidate_do_nothing(text)

        l = len(text[: char_in_line * head].rstrip())
        r = len(text) - char_in_line * tail
        tokens: list[_PrettyToken] = []
        for line in text[:l].splitlines(keepends=True):
            tokens += _tokenize_line(line)
        tokens.append(_PrettyToken(_PrettyTokenType.HINT, f"... ({r - l} chars) ..."))
        for line in text[r:].splitlines(keepends=True):
            tokens += _tokenize_line(line)
        return tokens

    def count_size(tokens: Iterable[_PrettyToken]) -> int:
        size = 0
        for _, s in tokens:
            size += len(s)
        return size

    # Choose the shortest one from the three candidates.
    tokens, text = _decode_with_recovery(content)
    if text:
        candidates: list[list[_PrettyToken]] = [
            candidate_do_nothing(text),
            candidate_line_based(text),
            candidate_char_based(text),
        ]
        tokens.extend(min(candidates, key=count_size))
    return _warn_if_empty(tokens)


def _replace_whitespace(s: str) -> str:
    return s.replace(" ", "_").replace("\t", "\\t").replace("\r", "\\r")


def _render_tokens(*, tokens: list[_PrettyToken]) -> str:
    """`_tokenize_large_file_content` generate the result string. It is colored."""

    def font_bold(s: str) -> str:
        return colorama.Style.BRIGHT + s + colorama.Style.RESET_ALL

    def font_dim(s: str) -> str:
        return colorama.Style.DIM + s + colorama.Style.RESET_ALL

    def font_red(s: str) -> str:
        return colorama.Fore.RED + s + colorama.Style.RESET_ALL

    result: list[str] = []
    for key, value in tokens:
        match key:
            case _PrettyTokenType.BODY:
                v = font_bold(value)
            case _PrettyTokenType.BODY_HIGHLIGHT_LEFT:
                v = font_red(value)
            case _PrettyTokenType.BODY_HIGHLIGHT_RIGHT:
                v = font_red(value)
            case _PrettyTokenType.WHITESPACE:
                v = font_dim(_replace_whitespace(value))
            case _PrettyTokenType.NEWLINE:
                v = font_dim(_replace_whitespace(value))
            case _PrettyTokenType.HINT:
                v = font_dim(value)
            case _:
                msg = f"Invalid token type: {key!r}"
                raise NotImplementedError(msg)
        result.append(v)
    return "".join(result)


def _get_terminal_size() -> int:
    char_in_line, _ = shutil.get_terminal_size()
    return max(
        char_in_line, 40
    )  # shutil.get_terminal_size() may return too small values (e.g. (0, 0) on Circle CI) successfully (i.e. fallback is not used). see https://github.com/kmyk/online-judge-tools/pull/611


def make_pretty_large_file_content(
    content: bytes, limit: int, head: int, tail: int
) -> str:
    char_in_line = _get_terminal_size()
    tokens = _tokenize_large_file_content(
        content=content, limit=limit, head=head, tail=tail, char_in_line=char_in_line
    )
    return _render_tokens(tokens=tokens)
