from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Generator, Iterable
from dataclasses import dataclass
from typing import IO, TypeAlias

from colorama import Fore, Style

from competitive_verifier.models import JudgeStatus

_whitespace_table = str.maketrans(
    {
        " ": "_",
        "\t": "\\t",
        "\r": "\\r",
        "\n": "\\n",
    }
)


def _replace_whitespace(s: str) -> str:
    return s.translate(_whitespace_table)


class _PrettyToken(ABC):
    """A token for verification output."""

    value: str

    def __init__(self, value: str) -> None:
        self.value = value

    @classmethod
    @abstractmethod
    def style(cls) -> str: ...

    def render(self) -> str:
        return self.style() + self.value + Style.RESET_ALL


class _BodyToken(_PrettyToken):
    @classmethod
    def style(cls) -> str:
        return Style.BRIGHT


class _HintToken(_PrettyToken):
    @classmethod
    def style(cls) -> str:
        return Style.DIM


class _WhitespaceToken(_PrettyToken):
    def __init__(self, value: str) -> None:
        self.value = _replace_whitespace(value)

    @classmethod
    def style(cls) -> str:
        return Style.DIM


_NewlineToken: TypeAlias = _WhitespaceToken


def _tokenize_str(s: str) -> list[_PrettyToken]:
    tokens: list[_PrettyToken] = []
    l = 0
    while l < len(s):
        r = l + 1
        while r < len(s) and (s[l] in " \t") == (s[r] in " \t"):
            r += 1
        typ = _WhitespaceToken if s[l] in " \t" else _BodyToken
        tokens.append(typ(s[l:r]))
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
            tokens.append(_NewlineToken(newline))
        else:
            whitespace = newline.rstrip("\n")
            newline = newline[len(whitespace) :]
            if whitespace:
                tokens.append(_WhitespaceToken(whitespace))
            tokens.append(_HintToken("(trailing whitespace)"))
            if newline:
                tokens.append(_NewlineToken(newline))

    return tokens


def _load_content(content: str | bytes) -> tuple[list[_PrettyToken], str]:
    if isinstance(content, str):
        return [], content
    try:
        return [], content.decode()
    except UnicodeDecodeError as e:
        return [_HintToken(str(e))], content.decode(errors="replace")


def _merge_token(tokens: list[_PrettyToken]) -> Iterable[_PrettyToken]:
    if len(tokens) == 0:
        yield _HintToken("(empty)")
        return

    prev = tokens[0]
    for token in tokens[1:]:
        if type(prev) is type(token):
            prev = type(prev)(prev.value + token.value)
        else:
            yield prev
            prev = token
    yield prev

    if isinstance(prev, _BodyToken):
        yield _HintToken("(no trailing newline)")


class StatusCounter(Counter[JudgeStatus]):
    def __str__(self) -> str:
        return ", ".join(
            f"{cnt} {name}"
            for name, cnt in ((st.name, self.get(st)) for st in JudgeStatus)
            if cnt
        )


@dataclass
class Printer:
    content: str | bytes | IO[bytes]
    limit: int = 60
    head: int = 20
    tail: int = 20

    def __str__(self) -> str:
        return self.render_file_content()

    def render_file_content(self) -> str:
        tokens = self._tokenize_file_content()
        return "".join(token.render() for token in tokens)

    def _tokenize_file_content(self) -> Iterable[_PrettyToken]:
        if not isinstance(self.content, (str, bytes)):
            self.content = self.content.read()

        # Choose the shortest one from the three candidates.
        tokens, text = _load_content(self.content)
        if text:
            tokens.extend(self._token(text))
        return _merge_token(tokens)

    def _token(self, text: str) -> Generator[_PrettyToken, None, None]:
        if self.head + self.tail >= self.limit:
            raise ValueError

        if len(text) < self.limit:
            # short
            for line in text.splitlines(keepends=True):
                yield from _tokenize_line(line)
        else:
            # long
            left = text[: self.head]
            right = text[-self.tail :]

            for line in left.splitlines(keepends=True):
                yield from _tokenize_line(line)

            yield _HintToken(f"... ({len(text) - len(right) - len(left)} chars) ...")

            for line in right.splitlines(keepends=True):
                yield from _tokenize_line(line)


def green(s: str) -> str:
    return Fore.GREEN + s + Fore.RESET


def red(s: str) -> str:
    return Fore.RED + s + Fore.RESET
