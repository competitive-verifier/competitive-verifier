# Python Version: 3.x
import collections
import glob
import os
import pathlib
import re
import sys
from collections.abc import Generator
from logging import getLogger
from re import Match

logger = getLogger(__name__)


def percentsplit(s: str) -> Generator[str, None, None]:
    for m in re.finditer("[^%]|%(.)", s):
        yield m.group(0)


def percentformat(s: str, table: dict[str, str]) -> str:
    if "%" in table and table["%"] != "%":
        raise ValueError
    table["%"] = "%"
    result = ""
    for c in percentsplit(s):
        if c.startswith("%"):
            result += table[c[1]]
        else:
            result += c
    return result


def percentparse(s: str, fmt: str, table: dict[str, str]) -> dict[str, str] | None:
    table = {key: f"(?P<{key}>{value})" for key, value in table.items()}
    used: set[str] = set()
    pattern = ""
    for token in percentsplit(re.escape(fmt).replace("\\%", "%")):
        if token.startswith("%"):
            c = token[1]
            if c not in used:
                pattern += table[c]
                used.add(c)
            else:
                pattern += rf"(?P={c})"
        else:
            pattern += token
    m = re.match(pattern, s)
    if not m:
        return None
    return m.groupdict()


def glob_with_format(directory: pathlib.Path, fmt: str) -> list[pathlib.Path]:
    if os.name == "nt":
        fmt = fmt.replace("/", "\\")
    table: dict[str, str] = {}
    table["s"] = "*"
    table["e"] = "*"
    pattern = glob.escape(str(directory) + os.path.sep) + percentformat(
        glob.escape(fmt).replace(glob.escape("%"), "%"), table
    )
    paths = list(map(pathlib.Path, glob.glob(pattern)))
    for path in paths:
        logger.debug("testcase globbed: %s", path)
    return paths


def match_with_format(
    directory: pathlib.Path, fmt: str, path: pathlib.Path
) -> Match[str] | None:
    if os.name == "nt":
        fmt = fmt.replace("/", "\\")
    table: dict[str, str] = {}
    table["s"] = "(?P<name>.+)"
    table["e"] = "(?P<ext>in|out)"
    pattern = re.compile(
        re.escape(str(directory.resolve()) + os.path.sep)
        + percentformat(re.escape(fmt).replace(re.escape("%"), "%"), table)
    )
    return pattern.match(str(path.resolve()))


def path_from_format(
    directory: pathlib.Path, fmt: str, name: str, ext: str
) -> pathlib.Path:
    table: dict[str, str] = {}
    table["s"] = name
    table["e"] = ext
    return directory / percentformat(fmt, table)


def is_backup_or_hidden_file(path: pathlib.Path) -> bool:
    basename = path.name
    return (
        basename.endswith("~")
        or (basename.startswith("#") and basename.endswith("#"))
        or basename.startswith(".")
    )


def drop_backup_or_hidden_files(paths: list[pathlib.Path]) -> list[pathlib.Path]:
    result: list[pathlib.Path] = []
    for path in paths:
        if is_backup_or_hidden_file(path):
            logger.warning("ignore a backup file: %s", path)
        else:
            result += [path]
    return result


def construct_relationship_of_files(
    paths: list[pathlib.Path], directory: pathlib.Path, fmt: str
) -> dict[str, dict[str, pathlib.Path]]:
    tests: dict[str, dict[str, pathlib.Path]] = collections.defaultdict(dict)
    for path in paths:
        m = match_with_format(directory, fmt, path.resolve())
        if not m:
            logger.error("unrecognizable file found: %s", path)
            sys.exit(1)
        name = m.groupdict()["name"]
        ext = m.groupdict()["ext"]
        if ext in tests[name]:
            raise RuntimeError
        tests[name][ext] = path
    for relationship in tests.values():
        if "in" not in relationship:
            if "out" not in relationship:
                raise RuntimeError
            logger.error("dangling output case: %s", relationship["out"])
            sys.exit(1)
    if not tests:
        logger.error("no cases found")
        sys.exit(1)
    logger.info("%d cases found", len(tests))
    return tests
