from datetime import timedelta

import pytest

from competitive_verifier.summary import to_human_str_mega_bytes, to_human_str_seconds

test_to_human_str_seconds_params: list[tuple[timedelta, str]] = [
    (timedelta(hours=2, minutes=8, seconds=6, milliseconds=13), "2h 8m"),
    (timedelta(minutes=8, seconds=6, milliseconds=13), "8m 6s"),
    (timedelta(seconds=16, milliseconds=13), "16s"),
    (timedelta(seconds=6, milliseconds=3), "6.0s"),
    (timedelta(seconds=6, milliseconds=13), "6.0s"),
    (timedelta(seconds=6, milliseconds=213), "6.2s"),
    (timedelta(milliseconds=1), "1ms"),
    (timedelta(milliseconds=12), "12ms"),
    (timedelta(milliseconds=123), "123ms"),
]


@pytest.mark.parametrize(
    "td, expected",
    test_to_human_str_seconds_params,
)
def test_to_human_str_seconds(td: timedelta, expected: str):
    assert to_human_str_seconds(td.total_seconds()) == expected


test_to_human_str_mega_bytes_params: list[tuple[float, str]] = [
    (0.000123456789, "0MB"),
    (0.00123456, "0.00123MB"),
    (0.01234567, "0.0123MB"),
    (0.12345678, "0.123MB"),
    (1.23456789, "1.23MB"),
    (12.3456789, "12.3MB"),
    (123.456789, "123MB"),
    (1234.56789, "1234MB"),
    (12345.6789, "12345MB"),
]


@pytest.mark.parametrize(
    "megabytes, expected",
    test_to_human_str_mega_bytes_params,
)
def test_to_human_str_mega_bytes(megabytes: float, expected: str):
    assert to_human_str_mega_bytes(megabytes) == expected
