import contextlib
import os
import pathlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from functools import cache
from logging import getLogger
from typing import Protocol

logger = getLogger(__name__)


class GnuTimeRunner(Protocol):
    @property
    def gnu_time(self) -> str | None: ...

    def get_command(self, command: list[str]) -> list[str]: ...
    def get_memory(self) -> float | None:
        """Return the amount of memory used, in megabytes, if possible."""
        ...

    def clean(self) -> None: ...


class _GnuTimeRunnerDummy:
    @property
    def gnu_time(self) -> None:
        return None

    def get_command(self, command: list[str]) -> list[str]:
        return command

    def get_memory(self) -> float | None:
        pass

    def clean(self) -> None:
        pass


@dataclass
class _GnuTimeRunnerImpl:
    gnu_time: str
    tmpdir: tempfile.TemporaryDirectory[str]
    outfile: pathlib.Path

    def get_command(self, command: list[str]) -> list[str]:
        return [self.gnu_time, "-f", "%M", "-o", str(self.outfile), "--", *command]

    def get_memory(self) -> float | None:
        if self.outfile.exists() and (
            report := self.outfile.read_text("utf-8").strip()
        ):
            logger.debug("GNU time says: %s", report)
            tail = report.splitlines()[-1]
            if tail.isdigit():
                return int(tail) / 1000
        return None

    def clean(self) -> None:
        self.tmpdir.cleanup()


class GnuTimeWrapper(contextlib.AbstractContextManager["GnuTimeRunner"]):
    _gnu_time: str | None
    _runner: GnuTimeRunner

    def __init__(self, *, enabled: bool = True) -> None:
        super().__init__()
        self._gnu_time = time_command() if enabled else None
        self._runner = _GnuTimeRunnerDummy()

    def __enter__(self):
        if self._gnu_time:
            tmpdir = tempfile.TemporaryDirectory()
            self._runner = _GnuTimeRunnerImpl(
                gnu_time=self._gnu_time,
                tmpdir=tmpdir,
                outfile=pathlib.Path(tmpdir.name) / "gnu_time_report.txt",
            )
        return self._runner

    def __exit__(self, *excinfo: object):
        self._runner.clean()


@cache
def time_command() -> str | None:
    cmds = ["time", "gtime"]
    if os.name == "posix":
        cmds += ["/bin/time", "/usr/bin/time"]
    return _find_gnu_time(cmds)


def _find_gnu_time(gnu_time_candidate: list[str]) -> str | None:
    for gnu_time in gnu_time_candidate:
        if check_gnu_time(gnu_time):
            return gnu_time
    return None


def check_gnu_time(gnu_time: str) -> bool:
    try:
        with tempfile.TemporaryDirectory() as td:
            tmp = pathlib.Path(td) / "out"
            ret = subprocess.run(
                [
                    gnu_time,
                    "-f",
                    "%M KB",
                    "-o",
                    str(tmp),
                    "--",
                    "echo",
                    "check_gnu_time",
                ],
                encoding="utf-8",
                capture_output=True,
                check=True,
            )
            if (
                ret.returncode == 0
                and ret.stdout.rstrip() == "check_gnu_time"
                and re.match(r"^\d+ KB$", tmp.read_text("utf-8").strip())
            ):
                return True
    except NameError:
        raise  # NameError is not a runtime error caused by the environment, but a coding mistake
    except AttributeError:
        raise  # AttributeError is also a mistake
    except Exception:  # noqa: BLE001
        logger.debug("Failed to check gnu_time: %s", gnu_time, exc_info=True)
    return False
