from datetime import timedelta

import pytest

from competitive_verifier.summary import to_human_str

test_to_human_str_params: list[tuple[timedelta, str]] = [
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
    test_to_human_str_params,
)
def test_to_human_str(td: timedelta, expected: str):
    assert to_human_str(td.total_seconds()) == expected
