import abc
import contextlib
import os
import pathlib
import re
import subprocess
import tempfile
from dataclasses import dataclass
from functools import cache
from logging import getLogger

logger = getLogger(__name__)


class GnuTimeRunner(abc.ABC):
    @abc.abstractmethod
    def get_command(self, command: list[str]) -> list[str]: ...
    @abc.abstractmethod
    def get_report(self) -> str | None: ...
    @abc.abstractmethod
    def clean(self) -> None: ...


class _GnuTimeRunnerDummy(GnuTimeRunner):
    def get_command(self, command: list[str]) -> list[str]:
        return command

    def get_report(self) -> str | None:
        pass

    def clean(self) -> None:
        pass


@dataclass
class _GnuTimeRunnerImpl(GnuTimeRunner):
    gnu_time: str
    tmpdir: tempfile.TemporaryDirectory[str]
    outfile: pathlib.Path

    def get_command(self, command: list[str]) -> list[str]:
        return [self.gnu_time, "-f", "%M", "-o", str(self.outfile), "--", *command]

    def get_report(self) -> str | None:
        return self.outfile.read_text().strip()

    def clean(self) -> None:
        self.tmpdir.cleanup()


class GnuTimeWrapper(contextlib.AbstractContextManager["GnuTimeRunner"]):
    _gnu_time: str | None
    _runner: GnuTimeRunner | None

    def __init__(self, *, enabled: bool = True) -> None:
        super().__init__()
        self._gnu_time = time_command() if enabled else None
        self._runner = None

    def __enter__(self):
        if self._gnu_time:
            tmpdir = tempfile.TemporaryDirectory()
            self._runner = _GnuTimeRunnerImpl(
                gnu_time=self._gnu_time,
                tmpdir=tmpdir,
                outfile=pathlib.Path(tmpdir.name) / "gnu_time_report.txt",
            )
        else:
            self._runner = _GnuTimeRunnerDummy()
        return self._runner

    def __exit__(self, *excinfo: object):
        if self._runner:
            self._runner.clean()


@cache
def time_command() -> str | None:
    cmds = ["time", "gtime"]
    if os.name == "posix":
        cmds += ["/bin/time", "/usr/bin/time"]
    for cmd in cmds:
        if _check_gnu_time(cmd):
            return cmd
    return None


def _check_gnu_time(gnu_time: str) -> bool:
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
                capture_output=True,
                check=True,
            )
            if (
                ret.returncode == 0
                and ret.stdout.rstrip() == b"check_gnu_time"
                and re.match(r"^\d+ KB$", tmp.read_text().strip())
            ):
                return True
    except NameError:
        raise  # NameError is not a runtime error caused by the environment, but a coding mistake
    except AttributeError:
        raise  # AttributeError is also a mistake
    except Exception:  # noqa: BLE001
        logger.debug("Failed to check gnu_time", exc_info=True)
    return False
