import logging

from tests import LogComparer


def test_comparer():
    assert LogComparer(message="123") == LogComparer(message="123")
    assert LogComparer(message="123") != LogComparer(message="124")

    assert LogComparer(message="123") == logging.makeLogRecord(
        {"msg": "%d", "args": (123,)}
    )
    assert LogComparer(message="123") != logging.makeLogRecord(
        {"msg": "%d", "args": (124,)}
    )

    assert LogComparer(message="123", level=1) == logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "levelno": 1}
    )
    assert LogComparer(message="123", level=1) != logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "levelno": 2}
    )

    assert LogComparer(message="123", name="1") == logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "name": "1"}
    )
    assert LogComparer(message="123", name="1") != logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "name": "2"}
    )

    assert LogComparer(message="123", extra={"foo": 1}) == logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "foo": 1}
    )
    assert LogComparer(message="123", extra={"foo": 1}) != logging.makeLogRecord(
        {"msg": "%d", "args": (123,), "foo": 2}
    )
