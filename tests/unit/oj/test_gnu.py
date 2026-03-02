import argparse
import logging
import pathlib
from subprocess import CompletedProcess
from unittest import mock

import pytest
from pytest_mock import MockerFixture

from competitive_verifier.oj import gnu


@pytest.fixture(autouse=True)
def reset_time_command_cache():
    gnu.time_command.cache_clear()
    yield
    gnu.time_command.cache_clear()


@pytest.mark.parametrize(
    ("os_name", "expected"),
    [
        ("nt", ["time", "gtime"]),
        (
            "posix",
            ["time", "gtime", "/bin/time", "/usr/bin/time"],
        ),
    ],
)
def test_find_gnu_time_candidate(
    os_name: str,
    expected: list[str],
    mocker: MockerFixture,
):
    find_gnu_time = mocker.patch.object(gnu, "_find_gnu_time", return_value=None)
    with mock.patch("os.name", os_name):
        gnu.time_command()

    find_gnu_time.assert_called_once_with(expected)


def test_check_gnu_time(caplog: pytest.LogCaptureFixture, mocker: MockerFixture):
    caplog.set_level(0)

    def subprocess_run1(
        cmd: list[str],
        **kwargs: dict[str, object],
    ) -> CompletedProcess[str]:
        match cmd[0]:
            case "time":
                return CompletedProcess[str](
                    cmd,
                    returncode=1,
                    stdout="error",
                    stderr="error",
                )
            case "gtime":
                parser = argparse.ArgumentParser()
                parser.add_argument("-o")
                parsed, _ = parser.parse_known_args(cmd)
                pathlib.Path(parsed.o).write_text("1024 KB\n")
                return CompletedProcess[str](
                    cmd,
                    returncode=0,
                    stdout="1024 KB\n",
                    stderr="",
                )
            case "/bin/time":
                parser = argparse.ArgumentParser()
                parser.add_argument("-o")
                parsed, _ = parser.parse_known_args(cmd)
                pathlib.Path(parsed.o).write_text("1024 KB\n")
                return CompletedProcess[str](
                    cmd,
                    returncode=0,
                    stdout="1024 KB\n",
                    stderr="",
                )
            case "/usr/bin/time":
                parser = argparse.ArgumentParser()
                parser.add_argument("-o")
                parsed, _ = parser.parse_known_args(cmd)
                pathlib.Path(parsed.o).write_text("1024 KB\n")
                return CompletedProcess[str](
                    cmd,
                    returncode=0,
                    stdout="check_gnu_time\n",
                    stderr="",
                )
            case _:
                raise NotImplementedError

    def subprocess_run2(
        cmd: list[str],
        **kwargs: dict[str, object],
    ) -> CompletedProcess[str]:
        match cmd[0]:
            case "time":
                raise FileNotFoundError
            case "gtime":
                raise FileNotFoundError
            case _:
                parser = argparse.ArgumentParser()
                parser.add_argument("-o")
                parsed, _ = parser.parse_known_args(cmd)
                pathlib.Path(parsed.o).write_text("1024 KB\n")
                return CompletedProcess[str](
                    cmd,
                    returncode=1,
                    stdout="check_gnu_time\n",
                    stderr="",
                )

    with mock.patch("os.name", "posix"):
        mocker.patch("subprocess.run", side_effect=subprocess_run1)
        assert gnu.time_command() == "/usr/bin/time"
        assert caplog.record_tuples == []

        gnu.time_command.cache_clear()
        mocker.patch("subprocess.run", side_effect=subprocess_run2)
        assert gnu.time_command() is None
        assert caplog.record_tuples == [
            ("competitive_verifier.oj.gnu", logging.DEBUG, "Failed to check gnu_time"),
            ("competitive_verifier.oj.gnu", logging.DEBUG, "Failed to check gnu_time"),
        ]

        assert caplog.records[0].exc_info is not None
        assert caplog.records[1].exc_info is not None


@pytest.mark.parametrize("error", [NameError, AttributeError])
def test_check_gnu_time_error(error: type[Exception], mocker: MockerFixture):
    def subprocess_run1(
        cmd: list[str],
        **kwargs: dict[str, object],
    ) -> CompletedProcess[str]:
        raise error

    with mock.patch("os.name", "posix"):
        mocker.patch("subprocess.run", side_effect=subprocess_run1)
        with pytest.raises(error):
            gnu.time_command()


def test_gnu_wrapper_not_found(mocker: MockerFixture):
    mocker.patch.object(gnu, "time_command", return_value=None)
    with gnu.GnuTimeWrapper(enabled=True) as gw:
        cmd = gw.get_command(["foo", "bar"])
        assert cmd == ["foo", "bar"]
        assert gw.get_memory() is None


def test_gnu_wrapper(testtemp: pathlib.Path, mocker: MockerFixture):
    mocker.patch.object(gnu, "time_command", return_value="dummy_time")
    with gnu.GnuTimeWrapper(enabled=True) as gw:
        cmd = gw.get_command(["foo", "bar"])
        assert cmd == [
            "dummy_time",
            "-f",
            "%M",
            "-o",
            str(testtemp / "1" / "gnu_time_report.txt"),
            "--",
            "foo",
            "bar",
        ]
        outpath = cmd[4]
        assert gw.get_memory() is None
        pathlib.Path(outpath).write_text("2048")
        assert gw.get_memory() == 2.048
        pathlib.Path(outpath).write_text("Other output\n123456\n\n")
        assert gw.get_memory() == 123.456
        pathlib.Path(outpath).write_text("abc")
        assert gw.get_memory() is None

    with gnu.GnuTimeWrapper(enabled=False) as gw:
        cmd = gw.get_command(["foo", "bar"])
        assert cmd == ["foo", "bar"]
        assert gw.get_memory() is None
