import pathlib
from contextlib import nullcontext
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


test_check_gnu_time_params = [
    (
        CompletedProcess[str](
            "dummy",
            returncode=0,
            stdout="check_gnu_time",
        ),
        "1024 KB\n\n",
        True,
    ),
    (
        CompletedProcess[str](
            "dummy",
            returncode=0,
            stdout="error",
        ),
        "invalid",
        False,
    ),
    (
        CompletedProcess[str](
            "dummy",
            returncode=1,
            stdout="check_gnu_time",
        ),
        "1024 KB\n\n",
        False,
    ),
    (
        CompletedProcess[str](
            "dummy",
            returncode=0,
            stdout="check_gnu_time",
        ),
        "invalid",
        False,
    ),
    (
        FileNotFoundError,
        "invalid",
        False,
    ),
]


@pytest.mark.parametrize(
    ("command_result", "outdata", "expected"),
    test_check_gnu_time_params,
)
def test_check_gnu_time(
    command_result: CompletedProcess[str] | type[Exception],
    outdata: str,
    expected: bool,
    testtemp: pathlib.Path,
    caplog: pytest.LogCaptureFixture,
    mocker: MockerFixture,
):
    caplog.set_level(0)
    mocker.patch("tempfile.TemporaryDirectory", return_value=nullcontext(testtemp))

    if isinstance(command_result, type):
        mocker.patch("subprocess.run", side_effect=command_result)
    else:
        mocker.patch("subprocess.run", return_value=command_result)
    (testtemp / "out").write_text(outdata)
    assert gnu.check_gnu_time("dummy_time") == expected


@pytest.mark.parametrize("error", [NameError, AttributeError])
def test_check_gnu_time_error(error: type[Exception], mocker: MockerFixture):
    with mock.patch("os.name", "posix"):
        mocker.patch("tempfile.TemporaryDirectory", side_effect=error())
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
